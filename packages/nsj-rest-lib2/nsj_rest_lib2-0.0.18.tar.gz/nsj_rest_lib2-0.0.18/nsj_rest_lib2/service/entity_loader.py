import datetime
import json
import re
import sys
import threading
import types

from nsj_rest_lib.settings import get_logger

from nsj_rest_lib2.compiler.edl_model.primitives import REGEX_EXTERNAL_REF
from nsj_rest_lib2.compiler.model import RelationDependency
from nsj_rest_lib2.compiler.util.type_naming_util import compile_namespace_keys
from nsj_rest_lib2.exception import MissingEntityConfigException
from nsj_rest_lib2.redis_config import get_redis
from nsj_rest_lib2.settings import ESCOPO_RESTLIB2, MIN_TIME_SOURCE_REFRESH


# TODO Verificar se está atualizando o loaded_at, quando o hash não muda
class LoadedEntity:
    def __init__(self):
        self.dto_class_name: str = ""
        self.entity_class_name: str = ""
        self.entity_hash: str = ""
        self.loaded_at: datetime.datetime = datetime.datetime.now()
        self.api_expose: bool = False
        self.api_verbs: list[str] = []
        self.relations_dependencies: list[RelationDependency] = []


class Namespace:
    def __init__(self):
        self.key: str = ""
        self.loaded_entities: dict[str, LoadedEntity] = {}
        self.entities_dict: dict = {}
        self.module: types.ModuleType = types.ModuleType("empty")


namespaces_dict: dict[str, Namespace] = {}


class EntityLoader:
    def __init__(self) -> types.NoneType:
        self._lock = threading.Lock()

    def load_entity_source(
        self,
        entity_resource: str,
        tenant: str | None,
        grupo_empresarial: str | None,
        escopo: str = ESCOPO_RESTLIB2,
    ) -> tuple[str, str, dict, bool, list[str]]:
        # Montando as chaves dos namespaces
        grupo_key, tenant_key, default_key = compile_namespace_keys(
            tenant, grupo_empresarial
        )

        result = self._search_entity_namespace_in_memory(
            entity_resource, grupo_key, tenant_key, default_key
        )

        # Se conseguiu localizar na memória, verifica se houve alteração no hash, em relação ao redis
        if result is not None:
            # Desempacotando o result e recuperando informações do namespace
            (
                entity_config_key,
                namespace,
            ) = result

            loaded_entity = namespace.loaded_entities[entity_resource]
            dto_class_name = loaded_entity.dto_class_name
            entity_class_name = loaded_entity.entity_class_name
            entities_dict = namespace.entities_dict
            api_expose = loaded_entity.api_expose
            api_verbs = loaded_entity.api_verbs
            relations_dependencies = loaded_entity.relations_dependencies

            # Verificando se alguma de suas dependências precisariam ser recarregadas
            for rd in relations_dependencies:
                if rd.entity_resource is None or rd.entity_scope is None:
                    raise RuntimeError(
                        f"Erro: Dependência de entidade mal formada na entidade {entity_resource}."
                    )

                self.load_entity_source(
                    rd.entity_resource,
                    str(rd.tenant),
                    str(rd.grupo_empresarial),
                    rd.entity_scope,
                )

            # Se o tempo entre o carregamento e agora for maior do que MIN_TIME_SOURCE_REFRESH minutos,
            # verifica se precisa de refresh
            time_diff = datetime.datetime.now() - loaded_entity.loaded_at

            if time_diff.total_seconds() >= MIN_TIME_SOURCE_REFRESH * 60:
                # Renovando o tempo de refresh
                loaded_entity.loaded_at = datetime.datetime.now()

                # Recuperando do Redis direto pela key (faz uma só chamada ao redis)
                loaded_config = self._load_entity_config_from_redis(
                    entity_resource,
                    grupo_key,
                    tenant_key,
                    default_key,
                    entity_config_key,
                    escopo=escopo,
                )

                # Se não achar no redis, usa o que estava em memória
                if not loaded_config:
                    return (
                        dto_class_name,
                        entity_class_name,
                        entities_dict,
                        api_expose,
                        api_verbs,
                    )

                # Desempacotando resultado
                entity_config_key, entity_config_str = loaded_config

                # Executando o código da entidade, só se houver mudança no hash
                result_execute = self._execute_entity_source(
                    entity_config_str,
                    entity_config_key,
                    entity_resource,
                    check_refresh=True,
                )

                # Se não carregou novo código, usa o que estava em memória
                if result_execute is None:
                    return (
                        dto_class_name,
                        entity_class_name,
                        entities_dict,
                        api_expose,
                        api_verbs,
                    )
                else:
                    (
                        dto_class_name,
                        entity_class_name,
                        namespace,
                        api_expose,
                        api_verbs,
                    ) = result_execute
                    return (
                        dto_class_name,
                        entity_class_name,
                        namespace.entities_dict,
                        api_expose,
                        api_verbs,
                    )
            else:
                # Se não deu o intervalo de verificação do refresh, retorna o que está em memória
                return (
                    dto_class_name,
                    entity_class_name,
                    entities_dict,
                    api_expose,
                    api_verbs,
                )

        # Se não conseguir recuperar a entidade, procura no redis:
        loaded_config = self._load_entity_config_from_redis(
            entity_resource,
            grupo_key,
            tenant_key,
            default_key,
            None,
            escopo=escopo,
        )

        # Se também não achar no redis, lanca exceção
        if not loaded_config:
            raise MissingEntityConfigException()

        # Desempacotando resultado
        entity_config_key, entity_config_str = loaded_config

        # Executando o código da entidade
        result_execute = self._execute_entity_source(
            entity_config_str, entity_config_key, entity_resource
        )

        if result_execute is None:
            raise RuntimeError(
                f"Erro desconhecido carregando entidade: {entity_resource}"
            )
        dto_class_name, entity_class_name, namespace, api_expose, api_verbs = (
            result_execute
        )

        return (
            dto_class_name,
            entity_class_name,
            namespace.entities_dict,
            api_expose,
            api_verbs,
        )

    def clear_namespaces(self):
        """
        Clears all loaded namespaces from memory.

        This method removes all entries from the namespaces_dict, effectively resetting
        the in-memory cache of loaded entities and their associated namespaces.
        """
        with self._lock:
            namespaces_dict.clear()

    def _ensure_dynamic_package(self):
        """
        Garante que exista um pacote 'dynamic' em sys.modules.
        """
        pkg = sys.modules.get("dynamic")
        if pkg is None:
            pkg = types.ModuleType("dynamic")
            pkg.__path__ = []  # marca como pacote
            pkg.__package__ = "dynamic"
            sys.modules["dynamic"] = pkg
        return pkg

    def _execute_entity_source(
        self,
        entity_config_str: str,
        entity_config_key: str,
        entity_resource: str,
        check_refresh: bool = False,
    ) -> tuple[str, str, Namespace, bool, list[str]] | None:
        # Interpretando o json de configuração da entidade
        try:
            entity_config = json.loads(entity_config_str)

            dto_class_name = entity_config["dto_class_name"]
            entity_class_name = entity_config["entity_class_name"]
            source_dto = entity_config["source_dto"]
            source_entity = entity_config["source_entity"]
            entity_hash = entity_config["entity_hash"]

            api_expose = entity_config["api_expose"]
            # api_resource = entity_config["api_resource"]
            api_verbs = entity_config["api_verbs"]
            relations_dependencies = [
                RelationDependency().from_dict(rd)
                for rd in entity_config.get("relations_dependencies", [])
            ]
        except json.JSONDecodeError as e:
            if not check_refresh:
                raise RuntimeError(
                    f"Erro ao decodificar JSON da entidade {entity_resource}; na chave {entity_config_key}: {e}"
                )
            else:
                get_logger().error(
                    f"Erro ao decodificar JSON da entidade {entity_resource}; na chave {entity_config_key}: {e}"
                )
                return None

        # Verificando se alguma de suas dependências precisariam ser carregadas (ou recarregadas)
        for rd in relations_dependencies:
            if rd.entity_resource is None or rd.entity_scope is None:
                raise RuntimeError(
                    f"Erro: Dependência de entidade mal formada na entidade {entity_resource}."
                )

            self.load_entity_source(
                rd.entity_resource,
                str(rd.tenant),
                str(rd.grupo_empresarial),
                rd.entity_scope,
            )

        # Verificando se a entidade precisa ou não de refresh
        if check_refresh:
            loaded_namespace = namespaces_dict.get(entity_config_key)
            if not loaded_namespace:
                return None

            loaded_entity = loaded_namespace.loaded_entities.get(entity_resource)
            if not loaded_entity:
                return None

            if loaded_entity.entity_hash == entity_hash:
                return None

        # Imprimindo alerta de load no log
        get_logger().debug(
            f"Carregando entidade {entity_resource} no namespace {entity_config_key}."
        )

        # Carregando a entidade no namespace
        with self._lock:
            self._ensure_dynamic_package()

            namespace = namespaces_dict.get(entity_config_key)
            if namespace is None:
                namespace = Namespace()
                namespace.key = entity_config_key
                namespaces_dict[entity_config_key] = namespace

            # Hot reload: removendo o módulo do sys.modules, se existir
            full_name = f"dynamic.{entity_config_key}"
            # if full_name in sys.modules:
            #     sys.modules.pop(full_name)

            # Executando o código da entidade
            module = sys.modules.get(full_name)
            if not module:
                module = types.ModuleType(full_name)
                module.__package__ = "dynamic"
                module.__dict__["__builtins__"] = __builtins__
                sys.modules[full_name] = module

                parent = sys.modules["dynamic"]
                setattr(parent, entity_config_key, module)

                namespace.module = module
                namespace.entities_dict = module.__dict__

            get_logger().debug(
                f"Executando o código da entidade {entity_resource} no namespace {entity_config_key}. Código:"
            )
            get_logger().debug(f"Entity source:\n{source_entity}")
            get_logger().debug(f"DTO source:\n{source_dto}")

            self._safe_exec(source_entity, namespace.entities_dict, "Entity source")
            self._safe_exec(source_dto, namespace.entities_dict, "DTO source")

            # Gravando a entidade no dict de entidades carregadas
            loaded_entity = LoadedEntity()
            loaded_entity.dto_class_name = dto_class_name
            loaded_entity.entity_class_name = entity_class_name
            loaded_entity.entity_hash = entity_hash
            loaded_entity.api_expose = api_expose
            loaded_entity.api_verbs = api_verbs
            loaded_entity.relations_dependencies = relations_dependencies

            namespace.loaded_entities[entity_resource] = loaded_entity

        return (dto_class_name, entity_class_name, namespace, api_expose, api_verbs)

    def _safe_exec(self, source_code, context, description):
        try:
            exec(source_code, context)
        except Exception as e:
            get_logger().error(f"Error executing {description}: {e}")
            raise

    def _load_entity_config_from_redis(
        self,
        entity_resource: str,
        grupo_key: str,
        tenant_key: str,
        default_key: str,
        entity_config_key: str | None,
        escopo: str,
    ) -> tuple[str, str] | None:
        get_logger().debug(
            f"Procurando a configuração da entidade {entity_resource} no redis. Tenant key: {tenant_key} e Grupo key: {grupo_key}"
        )

        if entity_config_key is not None:
            entity_config_str = get_redis(
                "entity_config", escopo, entity_config_key, entity_resource
            )

        else:
            entity_config_key = grupo_key
            entity_config_str = get_redis(
                "entity_config", escopo, grupo_key, entity_resource
            )
            if entity_config_str is None:
                entity_config_key = tenant_key
                entity_config_str = get_redis(
                    "entity_config", escopo, tenant_key, entity_resource
                )
            if entity_config_str is None:
                entity_config_key = default_key
                entity_config_str = get_redis(
                    "entity_config", escopo, default_key, entity_resource
                )

        # Se não encontrar no redis, retorna None
        if entity_config_str is None:
            return None

        return (entity_config_key, entity_config_str)

    def _search_entity_namespace_in_memory(
        self,
        entity_resource: str,
        grupo_key: str,
        tenant_key: str,
        default_key: str,
    ) -> tuple[str, Namespace] | None:
        namespace = None
        entity_config_key = None

        # Pesquisando a entidade no namespace mais específico (grupo_empresarial)
        grupo_namespace = namespaces_dict.get(grupo_key)
        if grupo_namespace and entity_resource in grupo_namespace.loaded_entities:
            entity_config_key = grupo_key
            namespace = grupo_namespace

        # Pesquisando a entidade no namespace intermediário (tenant)
        tenant_namespace = namespaces_dict.get(tenant_key)
        if tenant_namespace and entity_resource in tenant_namespace.loaded_entities:
            entity_config_key = tenant_key
            namespace = tenant_namespace

        # Pesquisando a entidade no namespace padrão (default)
        default_namespace = namespaces_dict.get(default_key)
        if default_namespace and entity_resource in default_namespace.loaded_entities:
            entity_config_key = default_key
            namespace = default_namespace

        if namespace and entity_config_key:
            return (entity_config_key, namespace)
        else:
            return None

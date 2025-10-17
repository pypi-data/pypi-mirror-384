import json

from typing import Any

from flask import Flask, request

from nsj_rest_lib.settings import APP_NAME

from nsj_gcf_utils.rest_error_util import format_json_error

from nsj_multi_database_lib.decorator.multi_database import multi_database

from nsj_rest_lib.controller.controller_util import DEFAULT_RESP_HEADERS
from nsj_rest_lib.controller.list_route import ListRoute
from nsj_rest_lib.controller.get_route import GetRoute
from nsj_rest_lib.controller.post_route import PostRoute
from nsj_rest_lib.controller.put_route import PutRoute
from nsj_rest_lib.controller.patch_route import PatchRoute
from nsj_rest_lib.controller.delete_route import DeleteRoute

from nsj_rest_lib2.exception import MissingEntityConfigException
from nsj_rest_lib2.service.entity_loader import EntityLoader


def _get_tenant_grupo() -> tuple[str, str]:
    # Tentando ler do query args
    query_args = request.args
    tenant = query_args.get("tenant")
    grupo_empresarial = query_args.get("grupo_empresarial")

    # Tentando ler do corpo da requisição
    try:
        body_str = request.data.decode("utf-8")
        body_json = json.loads(body_str)

        if not tenant:
            tenant = body_json.get("tenant")
        if not grupo_empresarial:
            grupo_empresarial = body_json.get("grupo_empresarial")
    except:
        pass

    return (str(tenant), str(grupo_empresarial))


def _endpoint_name(func: Any, multidb: bool, root: str) -> str:
    suffix = "_mb" if multidb else ""
    return f"{root}_{func.__name__}{suffix}"


def setup_dynamic_routes(
    flask_app: Flask,
    multidb: bool = True,
    dynamic_root_path: str = "edl1",
    injector_factory: Any = None,
) -> None:

    COLLECTION_DYNAMIC_ROUTE = f"/{APP_NAME}/{dynamic_root_path}/<entity_resource>"
    ONE_DYNAMIC_ROUTE = f"/{APP_NAME}/{dynamic_root_path}/<entity_resource>/<id>"

    def list_dynamic_wrapper(injector_factory: Any, *args: Any, **kwargs: Any) -> Any:

        def list_dynamic(*args: Any, **kwargs: Any):
            # Recuperando o identificador da entidade
            if "entity_resource" not in kwargs:
                msg = "Faltando parâmetro identificador da entidade na URL."
                return (format_json_error(msg), 400, {**DEFAULT_RESP_HEADERS})
            entity_resource = kwargs.pop("entity_resource")

            # Lendo tenant e grupo_empresarial
            tenant, grupo_empresarial = _get_tenant_grupo()

            try:
                # Recuperando o código do DTO e Entity correspondente
                entity_loader = EntityLoader()
                (
                    dto_class_name,
                    entity_class_name,
                    etities_dict,
                    api_expose,
                    api_verbs,
                ) = entity_loader.load_entity_source(
                    entity_resource, tenant, grupo_empresarial
                )

                # Verificando se essa API deve ser exposta
                if not api_expose or "GET" not in api_verbs:
                    return ("", 405, {})

                # Executando o list pelo RestLib
                route = ListRoute(
                    url=COLLECTION_DYNAMIC_ROUTE,
                    http_method="GET",
                    dto_class=etities_dict[dto_class_name],
                    entity_class=etities_dict[entity_class_name],
                    injector_factory=injector_factory,
                )

                return route.handle_request(*args, **kwargs)
            except MissingEntityConfigException:
                msg = f"Entity configuration for {entity_resource} not found."
                return (format_json_error(msg), 412, {**DEFAULT_RESP_HEADERS})

        return list_dynamic

    def get_dynamic_wrapper(injector_factory: Any, *args: Any, **kwargs: Any) -> Any:

        def get_dynamic(*args: Any, **kwargs: Any):
            # Recuperando o identificador da entidade
            if "entity_resource" not in kwargs:
                msg = "Faltando parâmetro identificador da entidade na URL."
                return (format_json_error(msg), 400, {**DEFAULT_RESP_HEADERS})
            entity_resource = kwargs.pop("entity_resource")

            # Lendo tenant e grupo_empresarial
            tenant, grupo_empresarial = _get_tenant_grupo()

            try:
                # Recuperando o código do DTO e Entity correspondente
                entity_loader = EntityLoader()
                (
                    dto_class_name,
                    entity_class_name,
                    etities_dict,
                    api_expose,
                    api_verbs,
                ) = entity_loader.load_entity_source(
                    entity_resource, tenant, grupo_empresarial
                )

                # Verificando se essa API deve ser exposta
                if not api_expose or "GET" not in api_verbs:
                    return ("", 405, {})

                # Executando o list pelo RestLib
                route = GetRoute(
                    url=ONE_DYNAMIC_ROUTE,
                    http_method="GET",
                    dto_class=etities_dict[dto_class_name],
                    entity_class=etities_dict[entity_class_name],
                    injector_factory=injector_factory,
                )

                return route.handle_request(*args, **kwargs)
            except MissingEntityConfigException:
                msg = f"Entity configuration for {entity_resource} not found."
                return (format_json_error(msg), 412, {**DEFAULT_RESP_HEADERS})

        return get_dynamic

    def post_dynamic_wrapper(injector_factory: Any, *args: Any, **kwargs: Any) -> Any:
        def post_dynamic(*args: Any, **kwargs: Any):
            # Recuperando o identificador da entidade
            if "entity_resource" not in kwargs:
                msg = "Faltando parâmetro identificador da entidade na URL."
                return (format_json_error(msg), 400, {**DEFAULT_RESP_HEADERS})
            entity_resource = kwargs.pop("entity_resource")

            # Lendo tenant e grupo_empresarial
            tenant, grupo_empresarial = _get_tenant_grupo()

            try:
                # Recuperando o código do DTO e Entity correspondente
                entity_loader = EntityLoader()
                (
                    dto_class_name,
                    entity_class_name,
                    etities_dict,
                    api_expose,
                    api_verbs,
                ) = entity_loader.load_entity_source(
                    entity_resource, tenant, grupo_empresarial
                )

                # Verificando se essa API deve ser exposta
                if not api_expose or "POST" not in api_verbs:
                    return ("", 405, {})

                # Executando o list pelo RestLib
                route = PostRoute(
                    url=COLLECTION_DYNAMIC_ROUTE,
                    http_method="POST",
                    dto_class=etities_dict[dto_class_name],
                    entity_class=etities_dict[entity_class_name],
                    injector_factory=injector_factory,
                )

                return route.handle_request(*args, **kwargs)
            except MissingEntityConfigException:
                msg = f"Entity configuration for {entity_resource} not found."
                return (format_json_error(msg), 412, {**DEFAULT_RESP_HEADERS})

        return post_dynamic

    def put_dynamic_wrapper(injector_factory: Any, *args: Any, **kwargs: Any) -> Any:
        def put_dynamic(*args: Any, **kwargs: Any):
            # Recuperando o identificador da entidade
            if "entity_resource" not in kwargs:
                msg = "Faltando parâmetro identificador da entidade na URL."
                return (format_json_error(msg), 400, {**DEFAULT_RESP_HEADERS})
            entity_resource = kwargs.pop("entity_resource")

            # Lendo tenant e grupo_empresarial
            tenant, grupo_empresarial = _get_tenant_grupo()

            try:
                # Recuperando o código do DTO e Entity correspondente
                entity_loader = EntityLoader()
                (
                    dto_class_name,
                    entity_class_name,
                    etities_dict,
                    api_expose,
                    api_verbs,
                ) = entity_loader.load_entity_source(
                    entity_resource, tenant, grupo_empresarial
                )

                # Verificando se essa API deve ser exposta
                if not api_expose or "PUT" not in api_verbs:
                    return ("", 405, {})

                # Executando o list pelo RestLib
                route = PutRoute(
                    url=ONE_DYNAMIC_ROUTE,
                    http_method="PUT",
                    dto_class=etities_dict[dto_class_name],
                    entity_class=etities_dict[entity_class_name],
                    injector_factory=injector_factory,
                )

                return route.handle_request(*args, **kwargs)
            except MissingEntityConfigException:
                msg = f"Entity configuration for {entity_resource} not found."
                return (format_json_error(msg), 412, {**DEFAULT_RESP_HEADERS})

        return put_dynamic

    def patch_dynamic_wrapper(injector_factory: Any, *args: Any, **kwargs: Any) -> Any:
        def patch_dynamic(*args: Any, **kwargs: Any):
            # Recuperando o identificador da entidade
            if "entity_resource" not in kwargs:
                msg = "Faltando parâmetro identificador da entidade na URL."
                return (format_json_error(msg), 400, {**DEFAULT_RESP_HEADERS})
            entity_resource = kwargs.pop("entity_resource")

            # Lendo tenant e grupo_empresarial
            tenant, grupo_empresarial = _get_tenant_grupo()

            try:
                # Recuperando o código do DTO e Entity correspondente
                entity_loader = EntityLoader()
                (
                    dto_class_name,
                    entity_class_name,
                    etities_dict,
                    api_expose,
                    api_verbs,
                ) = entity_loader.load_entity_source(
                    entity_resource, tenant, grupo_empresarial
                )

                # Verificando se essa API deve ser exposta
                if not api_expose or "PATCH" not in api_verbs:
                    return ("", 405, {})

                # Executando o list pelo RestLib
                route = PatchRoute(
                    url=ONE_DYNAMIC_ROUTE,
                    http_method="PATCH",
                    dto_class=etities_dict[dto_class_name],
                    entity_class=etities_dict[entity_class_name],
                    injector_factory=injector_factory,
                )

                return route.handle_request(*args, **kwargs)
            except MissingEntityConfigException:
                msg = f"Entity configuration for {entity_resource} not found."
                return (format_json_error(msg), 412, {**DEFAULT_RESP_HEADERS})

        return patch_dynamic

    def delete_dynamic_wrapper(injector_factory: Any, *args: Any, **kwargs: Any) -> Any:
        def delete_dynamic(*args: Any, **kwargs: Any):
            # Recuperando o identificador da entidade
            if "entity_resource" not in kwargs:
                msg = "Faltando parâmetro identificador da entidade na URL."
                return (format_json_error(msg), 400, {**DEFAULT_RESP_HEADERS})
            entity_resource = kwargs.pop("entity_resource")

            # Lendo tenant e grupo_empresarial
            tenant, grupo_empresarial = _get_tenant_grupo()

            try:
                # Recuperando o código do DTO e Entity correspondente
                entity_loader = EntityLoader()
                (
                    dto_class_name,
                    entity_class_name,
                    etities_dict,
                    api_expose,
                    api_verbs,
                ) = entity_loader.load_entity_source(
                    entity_resource, tenant, grupo_empresarial
                )

                # Verificando se essa API deve ser exposta
                if not api_expose or "DELETE" not in api_verbs:
                    return ("", 405, {})

                # Executando o list pelo RestLib
                route = DeleteRoute(
                    url=ONE_DYNAMIC_ROUTE,
                    http_method="DELETE",
                    dto_class=etities_dict[dto_class_name],
                    entity_class=etities_dict[entity_class_name],
                    injector_factory=injector_factory,
                )

                return route.handle_request(*args, **kwargs)
            except MissingEntityConfigException:
                msg = f"Entity configuration for {entity_resource} not found."
                return (format_json_error(msg), 412, {**DEFAULT_RESP_HEADERS})

        return delete_dynamic

    # Ajustando para o padrão com multi database (se necessário)
    if multidb:
        list_dynamic = multi_database()(list_dynamic_wrapper(injector_factory))
        get_dynamic = multi_database()(get_dynamic_wrapper(injector_factory))
        post_dynamic = multi_database()(post_dynamic_wrapper(injector_factory))
        put_dynamic = multi_database()(put_dynamic_wrapper(injector_factory))
        patch_dynamic = multi_database()(patch_dynamic_wrapper(injector_factory))
        delete_dynamic = multi_database()(delete_dynamic_wrapper(injector_factory))
    else:
        list_dynamic = list_dynamic_wrapper(injector_factory)
        get_dynamic = get_dynamic_wrapper(injector_factory)
        post_dynamic = post_dynamic_wrapper(injector_factory)
        put_dynamic = put_dynamic_wrapper(injector_factory)
        patch_dynamic = patch_dynamic_wrapper(injector_factory)
        delete_dynamic = delete_dynamic_wrapper(injector_factory)

    # Registrando as rotas no flask
    flask_app.add_url_rule(
        COLLECTION_DYNAMIC_ROUTE,
        endpoint=_endpoint_name(list_dynamic, multidb, dynamic_root_path),
        view_func=list_dynamic,
        methods=["GET"],
    )
    flask_app.add_url_rule(
        ONE_DYNAMIC_ROUTE,
        endpoint=_endpoint_name(get_dynamic, multidb, dynamic_root_path),
        view_func=get_dynamic,
        methods=["GET"],
    )
    flask_app.add_url_rule(
        COLLECTION_DYNAMIC_ROUTE,
        endpoint=_endpoint_name(post_dynamic, multidb, dynamic_root_path),
        view_func=post_dynamic,
        methods=["POST"],
    )
    flask_app.add_url_rule(
        ONE_DYNAMIC_ROUTE,
        endpoint=_endpoint_name(put_dynamic, multidb, dynamic_root_path),
        view_func=put_dynamic,
        methods=["PUT"],
    )
    flask_app.add_url_rule(
        ONE_DYNAMIC_ROUTE,
        endpoint=_endpoint_name(patch_dynamic, multidb, dynamic_root_path),
        view_func=patch_dynamic,
        methods=["PATCH"],
    )
    flask_app.add_url_rule(
        ONE_DYNAMIC_ROUTE,
        endpoint=_endpoint_name(delete_dynamic, multidb, dynamic_root_path),
        view_func=delete_dynamic,
        methods=["DELETE"],
    )

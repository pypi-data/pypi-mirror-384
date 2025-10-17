import re

from typing import Any

from nsj_rest_lib2.compiler.compiler_structures import (
    ComponentsCompilerStructure,
    IndexCompilerStructure,
    PropertiesCompilerStructure,
)
from nsj_rest_lib2.compiler.dto_compiler import DTOCompiler
from nsj_rest_lib2.compiler.edl_model.entity_model_base import EntityModelBase
from nsj_rest_lib2.compiler.edl_model.entity_model_root import EntityModelRoot
from nsj_rest_lib2.compiler.edl_model.primitives import REGEX_EXTERNAL_REF
from nsj_rest_lib2.compiler.entity_compiler import EntityCompiler
from nsj_rest_lib2.compiler.model import CompilerResult
from nsj_rest_lib2.compiler.property_compiler import EDLPropertyCompiler

from nsj_rest_lib2.compiler.edl_model.entity_model import EntityModel

from nsj_rest_lib2.settings import get_logger

# TODO GET e POST de relacionamentos 1X1
# TODO Revisar compilação de valores default (sensível a tipos)
# TODO Implementar suporte a conjuntos
# TODO Autenticação nas rotas
# TODO Atualizar o status da entidade pelo worker de compilação (e talvez parar uma compilação, quando se delete uma entidade)
# TODO Classes Abstratas
# TODO Partial Classes
# TODO Migrations
# TODO Criar imagem docker base para as aplicações, usando venv (para poderem atualizar o pydantic)

# TODO Suporte ao "min_items" dos relacionamentos no RestLib1


class EDLCompiler:
    def __init__(self) -> None:
        self._properties_compiler = EDLPropertyCompiler()
        self._dto_compiler = DTOCompiler()
        self._entity_compiler = EntityCompiler()

    def compile_models(
        self, entity_models: dict[str, EntityModel]
    ) -> list[CompilerResult]:

        compiler_results = []
        for entity_model_id in entity_models:
            entity_model = entity_models[entity_model_id]
            compiler_result = self._compile_model(entity_model, entity_models)
            if compiler_result:
                compiler_results.append(compiler_result)

        return compiler_results

    def compile_model_from_edl(
        self,
        edl_json: dict[str, Any],
        dependencies_edls: list[dict[str, Any]],
    ) -> CompilerResult | None:
        entity_model = EntityModel(**edl_json)

        entity_models = []
        for dependency_edl in dependencies_edls:
            if "mixin" in dependency_edl and dependency_edl["mixin"]:
                dependency_entity_model = EntityModelRoot(**dependency_edl)
            else:
                dependency_entity_model = EntityModel(**dependency_edl)
            entity_models.append(dependency_entity_model)

        return self.compile_model(entity_model, entity_models)

    def compile_model(
        self,
        entity_model: EntityModelBase,
        dependencies_models: list[tuple[str, EntityModelBase]],
    ) -> CompilerResult | None:
        entity_models = {}
        for dependency_entity_model in dependencies_models:
            complete_entity_id = dependency_entity_model[0]
            entity_models[complete_entity_id] = dependency_entity_model[1]

        return self._compile_model(entity_model, entity_models)

    def _compile_model(
        self,
        entity_model: EntityModelBase,
        entity_models: dict[str, EntityModel],
        escopo: str | None = None,
        prefx_class_name: str = "",
    ) -> CompilerResult | None:
        if entity_model.mixin:
            return None

        if escopo is None and (isinstance(entity_model, EntityModel)):
            escopo = entity_model.escopo

        if not escopo:
            raise Exception(f"Escopo não definido para a entidade: {entity_model.id}.")

        # Criando um mapa de índices por nome de property
        # TODO Implementar tratamento dos índices de apoio às query (não de unicidade)
        map_indexes_by_property: dict[str, list[IndexCompilerStructure]] = {}
        map_unique_by_property: dict[str, IndexCompilerStructure] = {}
        self._make_unique_map_by_property(
            map_indexes_by_property, map_unique_by_property, entity_model, entity_models
        )

        # Criando uma cópia das coleções necessárias à compilação das properties
        # (a ideia é ser possível alterar as coleções sem afetar a entidade modelo,
        # o que será necessário para o tratamento de traits, etc - os quais serão
        # uma classe nova, resultado da união dessas propriedades).
        properties_structure = PropertiesCompilerStructure()
        self._make_properties_structures(
            properties_structure, entity_model, entity_models
        )

        # Criando a lista de atributos do DTO e da Entity; e recuperando as chaves primarias
        (
            ast_dto_attributes,
            ast_entity_attributes,
            props_pk,
            aux_classes,
            related_imports,
            relations_dependencies,
            fixed_filters,
        ) = self._properties_compiler.compile(
            properties_structure,
            map_unique_by_property,
            escopo,
            entity_model,
            entity_models,
            prefx_class_name,
        )

        # Gerando o buffer para os códigos de DTO e Entity
        dto_code = ""
        entity_code = ""
        relations_dependencies_complete = []

        # Carregando a estrutura de compilação dos components
        components_structure = ComponentsCompilerStructure()
        self._make_components_structures(
            components_structure, entity_model, entity_models
        )

        # Gerando o código das entidades filhas (components)
        for component_key in components_structure.components:
            component = components_structure.components[component_key]
            component_compiled = self._compile_model(
                component,
                entity_models,
                escopo,
                prefx_class_name=f"{prefx_class_name}_{entity_model.id}",
            )

            if not component_compiled:
                raise Exception(
                    f"Erro ao compilar o component '{component_key}' da entidade '{entity_model.id}'. Gerou saída None, como se fosse um mixin."
                )

            # Guardando o código gerado no buffer
            if component_compiled.dto_code:
                dto_code += component_compiled.dto_code + "\n\n"
            if component_compiled.entity_code:
                entity_code += component_compiled.entity_code + "\n\n"
            if component_compiled.relations_dependencies:
                relations_dependencies_complete.extend(
                    component_compiled.relations_dependencies
                )

        # Gerando o código do DTO
        dto_class_name, code_dto = self._dto_compiler.compile(
            entity_model,
            ast_dto_attributes,
            aux_classes,
            related_imports,
            fixed_filters,
            prefx_class_name,
        )

        # Gerando o código da Entity
        entity_class_name, code_entity = self._entity_compiler.compile(
            entity_model,
            ast_entity_attributes,
            props_pk,
            prefx_class_name,
        )

        # Extendendo os buffers com os códigos gerados
        dto_code += code_dto
        entity_code += code_entity
        relations_dependencies_complete.extend(relations_dependencies)

        # Construindo o resultado
        compiler_result = CompilerResult()
        compiler_result.entity_class_name = entity_class_name
        compiler_result.entity_code = entity_code
        compiler_result.dto_class_name = dto_class_name
        compiler_result.dto_code = dto_code

        # Compilando questões das APIs
        if isinstance(entity_model, EntityModel):
            compiler_result.api_expose = entity_model.api.expose
            compiler_result.api_resource = entity_model.api.resource
            compiler_result.api_verbs = entity_model.api.verbs
            compiler_result.relations_dependencies = relations_dependencies_complete

        get_logger().debug(f"código gerado para a entidade: {entity_model.id}")
        get_logger().debug("DTO Code:")
        get_logger().debug(f"\n{dto_code}")
        get_logger().debug("Entity Code:")
        get_logger().debug(f"\n{entity_code}")

        return compiler_result

    def _make_components_structures(
        self,
        components_structure: ComponentsCompilerStructure,
        entity_model: EntityModelBase,
        entity_models: dict[str, EntityModel],
    ):
        if not entity_model:
            return

        # Populando com os components da superclasse (extends)
        if entity_model.extends:
            super_model = entity_models[entity_model.extends]

            self._make_components_structures(
                components_structure,
                super_model,
                entity_models,
            )

        # Populando com os components do trait
        if entity_model.trait_from:
            trait_model = entity_models[entity_model.trait_from]

            self._make_components_structures(
                components_structure,
                trait_model,
                entity_models,
            )

        # Populando com os components da entidade atual
        if entity_model.components:
            components_structure.components.update(entity_model.components)

    def _make_properties_structures(
        self,
        properties_structure: PropertiesCompilerStructure,
        entity_model: EntityModelBase,
        entity_models: dict[str, EntityModel],
    ):
        if not entity_model:
            return

        # Populando com as propriedades dos mixins
        if entity_model.mixins:
            for mixin_id in entity_model.mixins:
                if mixin_id not in entity_models:
                    raise Exception(f"Mixin '{mixin_id}' não encontrado.")

                mixin_model = entity_models[mixin_id]
                self._make_properties_structures(
                    properties_structure,
                    mixin_model,
                    entity_models,
                )

        # Populando com as propriedades da superclasse (extends)
        if entity_model.extends:
            super_model = entity_models[entity_model.extends]

            self._make_properties_structures(
                properties_structure,
                super_model,
                entity_models,
            )

        # Populando com as propriedades do trait
        if entity_model.trait_from:
            trait_model = entity_models[entity_model.trait_from]

            self._make_properties_structures(
                properties_structure,
                trait_model,
                entity_models,
            )

        # Populando com as propriedades da entidade atual
        properties_structure.properties.update(entity_model.properties)
        if entity_model.main_properties:
            properties_structure.main_properties.extend(entity_model.main_properties)
        if entity_model.required:
            properties_structure.required.extend(entity_model.required)
        if entity_model.partition_data:
            properties_structure.partition_data.extend(entity_model.partition_data)
        if entity_model.search_properties:
            properties_structure.search_properties.extend(
                entity_model.search_properties
            )
        if entity_model.metric_label:
            properties_structure.metric_label.extend(entity_model.metric_label)

        if entity_model.trait_properties:
            properties_structure.trait_properties.update(entity_model.trait_properties)

        if entity_model.extends_properties:
            properties_structure.extends_properties.update(
                entity_model.extends_properties
            )

        if entity_model.composed_properties:
            properties_structure.composed_properties.update(
                entity_model.composed_properties
            )

        if entity_model.repository.properties:
            properties_structure.entity_properties.update(
                entity_model.repository.properties
            )

    def _make_unique_map_by_property(
        self,
        map_indexes_by_property: dict[str, list[IndexCompilerStructure]],
        map_unique_by_property: dict[str, IndexCompilerStructure],
        entity_model: EntityModelBase,
        entity_models: dict[str, EntityModel],
        deep: int = 1,
    ):

        if not entity_model:
            return

        # Populando com as uniques da superclasse (extends)
        if entity_model.extends:
            super_model = entity_models[entity_model.extends]

            self._make_unique_map_by_property(
                map_indexes_by_property,
                map_unique_by_property,
                super_model,
                entity_models,
                deep=deep + 1,
            )

        # Populando com as uniques do trait
        if entity_model.trait_from:
            trait_model = entity_models[entity_model.trait_from]

            self._make_unique_map_by_property(
                map_indexes_by_property,
                map_unique_by_property,
                trait_model,
                entity_models,
                deep=deep + 1,
            )

        # Varrendo e organizando os índices
        if entity_model.repository.indexes:
            for index in entity_model.repository.indexes:
                for pkey in index.columns:
                    if index.unique:
                        if pkey in map_unique_by_property:
                            if deep > 1:
                                get_logger().warning(
                                    f"Propriedade '{pkey}' possui mais de um índice de unicidade (sendo um herdado). Por isso a replicação (herdada) será ignorada."
                                )
                                continue
                            else:
                                raise Exception(
                                    f"Propriedade '{pkey}' possui mais de um índice de unicidade."
                                )  # TODO Verificar esse modo de tratar erros

                        map_unique_by_property[pkey] = IndexCompilerStructure(
                            index, deep > 1
                        )
                    else:
                        list_index = map_indexes_by_property.setdefault(pkey, [])
                        list_index.append(IndexCompilerStructure(index, deep > 1))

    def list_dependencies(
        self, edl_json: dict[str, Any]
    ) -> tuple[list[str], EntityModelBase]:
        if edl_json.get("mixin", False):
            entity_model = EntityModelRoot(**edl_json)
        else:
            entity_model = EntityModel(**edl_json)

        return (self._list_dependencies(entity_model), entity_model)

    def _list_dependencies(self, entity_model: EntityModelBase) -> list[str]:
        entities: list[str] = []

        # Adicionando dependências por mixins
        if entity_model.mixins:
            entities.extend(entity_model.mixins)

        # Adicionando dependências por traits
        if entity_model.extends:
            entities.append(entity_model.extends)

        # Adicionando dependências por traits
        if entity_model.trait_from:
            entities.append(entity_model.trait_from)

        # Populando com as dependências de propriedades de relacionamento
        relations = self._list_dependencies_relations(entity_model)

        components_dependency_list = []
        if entity_model.components is not None:
            for component in entity_model.components:
                components_dependency_list.extend(
                    self._list_dependencies(entity_model.components[component])
                )

        relations.extend(components_dependency_list)

        entities.extend(relations)

        return entities

    def _list_dependencies_relations(self, entity_model) -> list[str]:
        entities = []

        # Relacionamento 1_N
        for pkey in entity_model.properties:
            prop = entity_model.properties[pkey]

            if isinstance(prop.type, str):
                external_match = re.match(REGEX_EXTERNAL_REF, prop.type)
                if external_match:
                    external_dependency = external_match.group(0)
                    entities.append(external_dependency)

        return entities


def get_files_from_directory(directory):
    files = []
    for file in os.listdir(directory):
        if file.endswith(".json") or file.endswith(".yml") or file.endswith(".yaml"):
            files.append(os.path.join(directory, file))
    return files


if __name__ == "__main__":
    import argparse
    import json
    import os
    import yaml

    parser = argparse.ArgumentParser(
        description="Compila arquivos EDL para classes Python"
    )
    parser.add_argument(
        "-d",
        "--directory",
        help="Diretório com arquivos .json para compilar",
        type=str,
        required=True,
    )
    args = parser.parse_args()

    files = get_files_from_directory(args.directory)

    entities = {}
    for file in files:
        with open(file, "r") as f:
            if file.endswith(".json"):
                edl = json.load(f)
            else:
                edl = yaml.safe_load(f)

        # Instanciando o objeto de modelo de entidade a partir do JSON,
        # e já realizando as validações básicas de tipo e estrutura.
        print(f"Validando arquivo: {file}")
        if edl.get("mixin", False):
            entity_model = EntityModelRoot(**edl)
        else:
            entity_model = EntityModel(**edl)

        complete_entity_id = f"{entity_model.escopo}/{entity_model.id}"
        entities[complete_entity_id] = entity_model

    compiler = EDLCompiler()
    compiler_results = compiler.compile_models(entities)

    for compiler_result in compiler_results:
        print("==========================================================")
        print(f"Entity: {compiler_result.entity_class_name}")
        print(f"{compiler_result.entity_code}")
        print("\n")
        print("==========================================================")
        print(f"DTO: {compiler_result.dto_class_name}")
        print(f"{compiler_result.dto_code}")
        print("\n")

        print("==========================================================")
        print("API Expose: ", compiler_result.api_expose)
        print("API Route Path: ", compiler_result.api_resource)
        print("API Verbs: ", compiler_result.api_verbs)
        print("==========================================================")
        print("\n")

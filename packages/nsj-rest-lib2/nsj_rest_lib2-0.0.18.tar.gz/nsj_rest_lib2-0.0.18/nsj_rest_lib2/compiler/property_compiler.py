import ast
import re

from nsj_rest_lib2.compiler.compiler_structures import (
    IndexCompilerStructure,
    PropertiesCompilerStructure,
)
from nsj_rest_lib2.compiler.edl_model.entity_model import EntityModel
from nsj_rest_lib2.compiler.edl_model.entity_model_base import EntityModelBase
from nsj_rest_lib2.compiler.edl_model.primitives import (
    BasicTypes,
    CardinalityTypes,
    PrimitiveTypes,
    REGEX_EXTERNAL_REF,
    REGEX_INTERNAL_REF,
)
from nsj_rest_lib2.compiler.edl_model.property_meta_model import PropertyMetaModel
from nsj_rest_lib2.compiler.edl_model.trait_property_meta_model import (
    TraitPropertyMetaModel,
)
from nsj_rest_lib2.compiler.model import RelationDependency
from nsj_rest_lib2.compiler.util.str_util import CompilerStrUtil
from nsj_rest_lib2.compiler.util.type_naming_util import (
    compile_dto_class_name,
    compile_entity_class_name,
    compile_namespace_keys,
)
from nsj_rest_lib2.compiler.util.type_util import TypeUtil

# TODO pattern
# TODO lowercase
# TODO uppercase


class EDLPropertyCompiler:

    def compile(
        self,
        properties_structure: PropertiesCompilerStructure,
        map_unique_by_property: dict[str, IndexCompilerStructure],
        escopo: str,
        entity_model: EntityModelBase,
        entity_models: dict[str, EntityModel],
        prefx_class_name: str,
    ) -> tuple[
        list[ast.stmt],
        list[ast.stmt],
        list[str],
        list[ast.stmt],
        list[tuple[str, str, str]],
        list[RelationDependency],
        list[tuple[str, BasicTypes]],
    ]:

        # TODO Criar opção de campo calculado?

        # Descobrindo os atributos marcados como PK (e recuperando a chave primária)
        # TODO Verificar se devemos manter essa verificação
        pk_keys = []
        for pkey in properties_structure.properties:
            prop = properties_structure.properties[pkey]

            if isinstance(prop.type, PrimitiveTypes):
                if prop.pk:
                    pk_keys.append(pkey)

        if not entity_model.mixin:
            if len(pk_keys) > 1:
                raise Exception(
                    f"Entidade '{entity_model.id}' possui mais de uma chave primária (ainda não suportado): {pk_keys}"
                )
            elif len(pk_keys) == 0:
                raise Exception(
                    f"Entidade '{entity_model.id}' não tem nenhuma chave primária (ainda não suportado)"
                )

        # pk_key = pk_keys[0]

        # Instanciando as listas de retorno
        ast_dto_attributes = []
        ast_entity_attributes = []
        props_pk = []
        aux_classes = []
        related_imports = []
        relations_dependencies = []
        fixed_filters = []

        if properties_structure.properties is None:
            return (ast_dto_attributes, ast_entity_attributes, props_pk, aux_classes)

        composed_properties = properties_structure.composed_properties or {}

        aggregator_class_names: dict[str, str] = {}
        aggregator_dto_attributes: dict[str, list[ast.stmt]] = {}
        aggregated_property_to_group: dict[str, str] = {}

        for composed_key, composed_list in composed_properties.items():
            if not composed_list:
                continue

            composed_class_name = (
                f"{CompilerStrUtil.to_pascal_case(escopo)}"
                f"{CompilerStrUtil.to_pascal_case(prefx_class_name)}"
                f"{CompilerStrUtil.to_pascal_case(entity_model.id)}"
                f"{CompilerStrUtil.to_pascal_case(composed_key)}AggregatorDTO"
            )

            aggregator_class_names[composed_key] = composed_class_name
            aggregator_dto_attributes[composed_key] = []

            for composed_property in composed_list:
                if composed_property in aggregated_property_to_group:
                    raise Exception(
                        f"Propriedade '{composed_property}' da entidade '{entity_model.id}' está associada a mais de um composed_property."
                    )

                if composed_property not in properties_structure.properties:
                    raise Exception(
                        f"Propriedade '{composed_property}' referenciada no composed_property '{composed_key}' não encontrada na entidade '{entity_model.id}'."
                    )

                aggregated_property_to_group[composed_property] = composed_key

        for pkey in properties_structure.properties:
            prop = properties_structure.properties[pkey]

            composed_key = aggregated_property_to_group.get(pkey)
            if composed_key:
                if prop.pk:
                    raise Exception(
                        f"Propriedade '{pkey}' não pode ser utilizada em composed_properties por ser chave primária."
                    )
                target_dto_attributes = aggregator_dto_attributes[composed_key]
            else:
                target_dto_attributes = ast_dto_attributes

            # DTO
            if isinstance(prop.type, PrimitiveTypes):
                # Tratando propriedade simples (não array, não object)
                self._compile_simple_property(
                    properties_structure,
                    map_unique_by_property,
                    escopo,
                    entity_model,
                    target_dto_attributes,
                    ast_entity_attributes,
                    props_pk,
                    aux_classes,
                    pkey,
                    prop,
                    prefx_class_name,
                )

            elif isinstance(prop.type, str):
                # Tratando propriedade de relacionamento
                external_match = re.match(REGEX_EXTERNAL_REF, prop.type)
                internal_match = re.match(REGEX_INTERNAL_REF, prop.type)

                if external_match:
                    # Resolvendo o id da entidade
                    related_entity_id = external_match.group(2)
                    related_entity_key = external_match.group(0)

                    self._compile_external_relation(
                        related_entity_id,
                        related_entity_key,
                        entity_model,
                        entity_models,
                        properties_structure,
                        target_dto_attributes,
                        ast_entity_attributes,
                        related_imports,
                        relations_dependencies,
                        pkey,
                        prop,
                    )

                elif internal_match:
                    related_entity_id = internal_match.group(1)

                    self._compile_internal_relation(
                        related_entity_id,
                        entity_model,
                        properties_structure,
                        target_dto_attributes,
                        ast_entity_attributes,
                        pkey,
                        prop,
                        prefx_class_name,
                    )
                else:
                    raise Exception(
                        f"Tipo da propriedade '{pkey}' não suportado: {prop.type}"
                    )

        for pkey in properties_structure.trait_properties:
            prop = properties_structure.trait_properties[pkey]

            self._compile_trait_extends_property(
                properties_structure,
                map_unique_by_property,
                pkey,
                prop,
                ast_dto_attributes,
                ast_entity_attributes,
                fixed_filters,
                escopo,
                entity_model,
                aux_classes,
                prefx_class_name,
            )

        for pkey in properties_structure.extends_properties:
            prop = properties_structure.extends_properties[pkey]

            self._compile_trait_extends_property(
                properties_structure,
                map_unique_by_property,
                pkey,
                prop,
                ast_dto_attributes,
                ast_entity_attributes,
                fixed_filters,
                escopo,
                entity_model,
                aux_classes,
                prefx_class_name,
            )

        for composed_key, class_name in aggregator_class_names.items():
            dto_attributes = aggregator_dto_attributes.get(composed_key, [])

            aux_classes.append(
                self._build_aggregator_class_ast(
                    class_name=class_name,
                    dto_attributes=dto_attributes,
                )
            )

            ast_dto_attributes.append(
                self._build_dto_aggregator_ast(
                    name=composed_key,
                    class_name=class_name,
                )
            )

        return (
            ast_dto_attributes,
            ast_entity_attributes,
            props_pk,
            aux_classes,
            related_imports,
            relations_dependencies,
            fixed_filters,
        )

    def _compile_trait_extends_property(
        self,
        properties_structure: PropertiesCompilerStructure,
        map_unique_by_property: dict[str, IndexCompilerStructure],
        pkey: str,
        prop: TraitPropertyMetaModel,
        ast_dto_attributes: list[ast.stmt],
        ast_entity_attributes: list[ast.stmt],
        fixed_filters: list[tuple[str, BasicTypes]],
        escopo: str,
        entity_model: EntityModelBase,
        aux_classes: list[ast.stmt],
        prefx_class_name: str,
    ):
        enum_class_name = None
        keywords = []

        if (
            properties_structure.main_properties
            and pkey in properties_structure.main_properties
        ):
            keywords.append(ast.keyword(arg="resume", value=ast.Constant(True)))

        if properties_structure.required and pkey in properties_structure.required:
            keywords.append(ast.keyword(arg="not_null", value=ast.Constant(True)))

        if (
            properties_structure.partition_data
            and pkey in properties_structure.partition_data
        ):
            keywords.append(ast.keyword(arg="partition_data", value=ast.Constant(True)))

        if pkey in map_unique_by_property:
            unique = map_unique_by_property[pkey].index_model
            keywords.append(
                ast.keyword(
                    arg="unique",
                    value=ast.Constant(unique.name),
                )
            )

        if (
            properties_structure.search_properties
            and pkey in properties_structure.search_properties
        ):
            keywords.append(ast.keyword(arg="search", value=ast.Constant(True)))
        else:
            keywords.append(ast.keyword(arg="search", value=ast.Constant(False)))

        if (
            properties_structure.metric_label
            and pkey in properties_structure.metric_label
        ):
            keywords.append(ast.keyword(arg="metric_label", value=ast.Constant(True)))

        if prop.type == PrimitiveTypes.CPF:
            keywords.append(
                ast.keyword(
                    arg="validator",
                    value=ast.Attribute(
                        value=ast.Call(
                            func=ast.Name(id="DTOFieldValidators", ctx=ast.Load()),
                            args=[],
                            keywords=[],
                        ),
                        attr="validate_cpf",
                        ctx=ast.Load(),
                    ),
                )
            )
        elif prop.type == PrimitiveTypes.CNPJ:
            keywords.append(
                ast.keyword(
                    arg="validator",
                    value=ast.Attribute(
                        value=ast.Call(
                            func=ast.Name(id="DTOFieldValidators", ctx=ast.Load()),
                            args=[],
                            keywords=[],
                        ),
                        attr="validate_cnpj",
                        ctx=ast.Load(),
                    ),
                )
            )
        elif prop.type == PrimitiveTypes.CPF_CNPJ:
            keywords.append(
                ast.keyword(
                    arg="validator",
                    value=ast.Attribute(
                        value=ast.Call(
                            func=ast.Name(id="DTOFieldValidators", ctx=ast.Load()),
                            args=[],
                            keywords=[],
                        ),
                        attr="validate_cpf_or_cnpj",
                        ctx=ast.Load(),
                    ),
                )
            )
        elif prop.type == PrimitiveTypes.EMAIL:
            keywords.append(
                ast.keyword(
                    arg="validator",
                    value=ast.Attribute(
                        value=ast.Call(
                            func=ast.Name(id="DTOFieldValidators", ctx=ast.Load()),
                            args=[],
                            keywords=[],
                        ),
                        attr="validate_email",
                        ctx=ast.Load(),
                    ),
                )
            )

        # Trtando de uma definição de enum
        if prop.domain_config:
            result = self._compile_domain_config(
                pkey, prop, escopo, entity_model, prefx_class_name
            )
            if not result:
                raise Exception(f"Erro desconhecido ao compilar a propriedade {pkey}")

            enum_class_name, ast_enum_class = result
            aux_classes.append(ast_enum_class)

        # Resolvendo o nome da propriedade no Entity
        if (
            properties_structure.entity_properties
            and pkey in properties_structure.entity_properties
        ):
            entity_field_name = properties_structure.entity_properties[pkey].column
        else:
            entity_field_name = pkey

        # Escrevendo, se necessário, o alias para o nome da entity
        if entity_field_name != pkey:
            keywords.append(
                ast.keyword(
                    arg="entity_field",
                    value=ast.Constant(value=entity_field_name),
                )
            )

        # Instanciando o atributo AST
        if not isinstance(prop.type, PrimitiveTypes):
            raise Exception(
                f"Tipo da trait_property '{pkey}' não suportado: {prop.type} (deveria ser um Tipo Primitivo)"
            )

        # Instanciando o atributo AST
        if enum_class_name:
            prop_type = enum_class_name
        else:
            prop_type = TypeUtil.property_type_to_python_type(prop.type)

        ast_attr = ast.AnnAssign(
            target=ast.Name(id=CompilerStrUtil.to_snake_case(pkey), ctx=ast.Store()),
            annotation=ast.Name(
                id=prop_type,
                ctx=ast.Load(),
            ),
            value=ast.Call(
                func=ast.Name(id="DTOField", ctx=ast.Load()),
                args=[],
                keywords=keywords,
            ),
            simple=1,
        )

        ast_dto_attributes.append(ast_attr)

        # Entity
        ast_entity_attr = ast.AnnAssign(
            target=ast.Name(
                id=CompilerStrUtil.to_snake_case(entity_field_name),
                ctx=ast.Store(),
            ),
            annotation=ast.Name(
                id=TypeUtil.property_type_to_python_type(prop.type),
                ctx=ast.Load(),
            ),
            value=ast.Constant(value=None),
            simple=1,
        )

        ast_entity_attributes.append(ast_entity_attr)

        # Guardando como um fixed_filter
        # TODO Pensar em validações para esse value (se está de acordo com o tipo ou enum)
        fixed_filters.append((pkey, prop.value))

    def _build_aggregator_class_ast(
        self,
        class_name: str,
        dto_attributes: list[ast.stmt],
    ):
        body = dto_attributes if dto_attributes else [ast.Pass()]

        return ast.ClassDef(
            name=class_name,
            bases=[ast.Name(id="DTOBase", ctx=ast.Load())],
            keywords=[],
            decorator_list=[
                ast.Call(
                    func=ast.Name(id="DTO", ctx=ast.Load()),
                    args=[],
                    keywords=[],
                )
            ],
            body=body,
        )

    def _build_dto_aggregator_ast(
        self,
        name: str,
        class_name: str,
    ):
        return ast.AnnAssign(
            target=ast.Name(
                id=CompilerStrUtil.to_snake_case(name),
                ctx=ast.Store(),
            ),
            annotation=ast.Name(
                id=class_name,
                ctx=ast.Load(),
            ),
            value=ast.Call(
                func=ast.Name(id="DTOAggregator", ctx=ast.Load()),
                args=[ast.Name(id=class_name, ctx=ast.Load())],
                keywords=[],
            ),
            simple=1,
        )

    def _compile_external_relation(
        self,
        related_entity_id: str,
        related_entity_key: str,
        entity_model: EntityModelBase,
        entity_models: dict[str, EntityModel],
        properties_structure: PropertiesCompilerStructure,
        ast_dto_attributes: list[ast.stmt],
        ast_entity_attributes: list[ast.stmt],
        related_imports: list[tuple[str, str, str]],
        relations_dependencies: list[RelationDependency],
        pkey: str,
        prop: PropertyMetaModel,
    ):
        # Resolvendo o nome das classes de DTO e Entity
        related_dto_class_name = compile_dto_class_name(related_entity_id)
        related_entity_class_name = compile_entity_class_name(related_entity_id)

        # Resolvendo o caminho do import
        related_entity = entity_models.get(related_entity_key)
        if not related_entity:
            raise Exception(
                f"Entidade '{entity_model.id}' possui uma referência externa para uma entidade inexistente: '{related_entity_key}', por meio da propriedade: '{pkey}'."
            )

        tenant = related_entity.tenant
        grupo_empresarial = related_entity.grupo_empresarial
        grupo_key, tenant_key, default_key = compile_namespace_keys(
            tenant, grupo_empresarial
        )

        if (
            tenant
            and tenant != 0
            and grupo_empresarial
            and grupo_empresarial != "00000000-0000-0000-0000-000000000000"
        ):
            related_import = grupo_key
        elif tenant and tenant != 0:
            related_import = tenant_key
        else:
            related_import = default_key

        related_imports.append(
            (
                related_import,
                related_dto_class_name,
                related_entity_class_name,
            )
        )

        # Gravando a dependência de relacionamento
        relation_dependency = RelationDependency()
        relation_dependency.entity_resource = related_entity.api.resource
        relation_dependency.entity_scope = related_entity.escopo
        relation_dependency.tenant = tenant
        relation_dependency.grupo_empresarial = grupo_empresarial
        relations_dependencies.append(relation_dependency)

        # Instanciando o ast
        if prop.cardinality == CardinalityTypes.C1_N:
            # Para relacionamentos 1_N
            self._build_ast_1_N(
                properties_structure,
                ast_dto_attributes,
                pkey,
                related_dto_class_name,
                related_entity_class_name,
                prop,
            )

        elif prop.cardinality == CardinalityTypes.C1_1:
            self._build_ast_1_1(
                properties_structure,
                ast_dto_attributes,
                ast_entity_attributes,
                pkey,
                related_dto_class_name,
                related_entity_class_name,
                prop,
            )

        elif prop.cardinality == CardinalityTypes.CN_N:
            # TODO
            pass
        else:
            raise Exception(
                f"Propriedade '{pkey}' da entidade '{entity_model.id}' possui cardinalidade inválida ou não suportada: {prop.cardinality}"
            )

    def _compile_internal_relation(
        self,
        related_entity_id: str,
        entity_model: EntityModelBase,
        properties_structure: PropertiesCompilerStructure,
        ast_dto_attributes: list[ast.stmt],
        ast_entity_attributes: list[ast.stmt],
        pkey: str,
        prop: PropertyMetaModel,
        prefx_class_name: str,
    ):
        # Resolvendo o nome das classes de DTO e Entity
        related_dto_class_name = compile_dto_class_name(
            related_entity_id, f"{prefx_class_name}_{entity_model.id}"
        )
        related_entity_class_name = compile_entity_class_name(
            related_entity_id, f"{prefx_class_name}_{entity_model.id}"
        )

        # Instanciando o ast
        if prop.cardinality == CardinalityTypes.C1_N:
            # Para relacionamentos 1_N
            self._build_ast_1_N(
                properties_structure,
                ast_dto_attributes,
                pkey,
                related_dto_class_name,
                related_entity_class_name,
                prop,
            )

        elif prop.cardinality == CardinalityTypes.C1_1:
            self._build_ast_1_1(
                properties_structure,
                ast_dto_attributes,
                ast_entity_attributes,
                pkey,
                related_dto_class_name,
                related_entity_class_name,
                prop,
            )

        elif prop.cardinality == CardinalityTypes.CN_N:
            # TODO
            pass
        else:
            raise Exception(
                f"Propriedade '{pkey}' da entidade '{entity_model.id}' possui cardinalidade inválida ou não suportada: {prop.cardinality}"
            )

    def _build_ast_1_N(
        self,
        properties_structure: PropertiesCompilerStructure,
        ast_dto_attributes: list[ast.stmt],
        pkey: str,
        related_dto_class_name: str,
        related_entity_class_name: str,
        prop: PropertyMetaModel,
    ):
        # TODO Verificar uso da propriedade relation_key_field do Rest_lib_1

        # Propriedade do property descriptor
        keywords = [
            ast.keyword(
                arg="dto_type",
                value=ast.Name(id=related_dto_class_name, ctx=ast.Load()),
            ),
            ast.keyword(
                arg="entity_type",
                value=ast.Name(id=related_entity_class_name, ctx=ast.Load()),
            ),
        ]

        # Tratando das opções básicas do descritor de propriedade
        if properties_structure.required and pkey in properties_structure.required:
            keywords.append(ast.keyword(arg="not_null", value=ast.Constant(True)))

        if prop.max_length:
            keywords.append(ast.keyword(arg="max", value=ast.Constant(prop.max_length)))
        if prop.min_length:
            keywords.append(ast.keyword(arg="min", value=ast.Constant(prop.min_length)))

        if prop.validator:
            keywords.append(
                ast.keyword(
                    arg="validator",
                    value=ast.Name(prop.validator, ctx=ast.Load()),
                )
            )

        # Resolvendo a coluna usada no relacionamento
        if (
            not properties_structure.entity_properties
            or pkey not in properties_structure.entity_properties
            or not properties_structure.entity_properties[pkey].relation_column
        ):
            raise Exception(
                f"Propriedade '{pkey}' possui um relacionamento, mas nenhuma coluna de relacioanamento foi apontada na propriedade correspondente no repository."
            )

        relation_column_ref = properties_structure.entity_properties[
            pkey
        ].relation_column
        relation_column = str(relation_column_ref).split("/")[-1]

        keywords.append(
            ast.keyword(
                arg="related_entity_field",
                value=ast.Constant(value=relation_column),
            )
        )

        ast_attr = ast.AnnAssign(
            target=ast.Name(id=CompilerStrUtil.to_snake_case(pkey), ctx=ast.Store()),
            annotation=ast.Name(
                id="list",
                ctx=ast.Load(),
            ),
            value=ast.Call(
                func=ast.Name(id="DTOListField", ctx=ast.Load()),
                args=[],
                keywords=keywords,
            ),
            simple=1,
        )

        ast_dto_attributes.append(ast_attr)

    def _build_ast_1_1(
        self,
        properties_structure: PropertiesCompilerStructure,
        ast_dto_attributes: list[ast.stmt],
        ast_entity_attributes: list[ast.stmt],
        pkey: str,
        related_dto_class_name: str,
        related_entity_class_name: str,
        prop: PropertyMetaModel,
    ):
        # Propriedade do property descriptor
        keywords = [
            ast.keyword(
                arg="entity_type",
                value=ast.Name(id=related_entity_class_name, ctx=ast.Load()),
            ),
        ]

        # Tratando das opções básicas do descritor de propriedade
        if properties_structure.required and pkey in properties_structure.required:
            keywords.append(ast.keyword(arg="not_null", value=ast.Constant(True)))

        if (
            properties_structure.main_properties
            and pkey in properties_structure.main_properties
        ):
            keywords.append(ast.keyword(arg="resume", value=ast.Constant(True)))

        if prop.validator:
            keywords.append(
                ast.keyword(
                    arg="validator",
                    value=ast.Name(prop.validator, ctx=ast.Load()),
                )
            )

        # Resolvendo a coluna usada no relacionamento
        if (
            not properties_structure.entity_properties
            or pkey not in properties_structure.entity_properties
            or not properties_structure.entity_properties[pkey].relation_column
        ):
            raise Exception(
                f"Propriedade '{pkey}' possui um relacionamento, mas nenhuma coluna de relacioanamento foi apontada na propriedade correspondente no repository."
            )

        relation_column = str(
            properties_structure.entity_properties[pkey].relation_column
        )

        owner_relation = False
        if "/" in relation_column:
            owner_relation = True
            relation_column = relation_column.split("/")[-1]

        # TODO Verificar, porque desconfio que o apontamento para a coluna de relacionamento
        # para o caso do relacionamento OTHER, não é suportado pelo RestLib (acho que, quando
        # o dono é OTHER, o RestLib sempre aponta para a PK da entidade corrente).
        keywords.append(
            ast.keyword(
                arg="relation_field",
                value=ast.Constant(value=relation_column),
            )
        )

        if not owner_relation:
            keywords.append(
                ast.keyword(
                    arg="entity_relation_owner",
                    value=ast.Attribute(
                        value=ast.Name(id="EntityRelationOwner", ctx=ast.Load()),
                        attr="OTHER",
                        ctx=ast.Load(),
                    ),
                )
            )
        else:
            dto_property_name = f"relation_1_1_self_column_{relation_column}"
            # Adicionando propriedade, para o campo de relação, no DTO (quando for o dono da relação)
            ast_dto_attributes.append(
                self._build_dto_property_ast(
                    dto_property_name,
                    PrimitiveTypes.UUID,
                    keywords=[
                        ast.keyword(
                            arg="entity_field",
                            value=ast.Constant(value=relation_column),
                        ),
                    ],
                )
            )

            # Adicionando propriedade, para o campo de relação, no Entity (quando for o dono da relação)
            ast_entity_attributes.append(
                self._build_entity_property_ast(relation_column, PrimitiveTypes.UUID)
            )

        # Adicionando a propriedade em si do relacionamento, no DTO
        ast_attr = ast.AnnAssign(
            target=ast.Name(id=CompilerStrUtil.to_snake_case(pkey), ctx=ast.Store()),
            annotation=ast.Name(
                id=related_dto_class_name,
                ctx=ast.Load(),
            ),
            value=ast.Call(
                func=ast.Name(id="DTOObjectField", ctx=ast.Load()),
                args=[],
                keywords=keywords,
            ),
            simple=1,
        )

        ast_dto_attributes.append(ast_attr)

    def _build_dto_property_ast(
        self,
        name: str,
        type: PrimitiveTypes | str,
        keywords: list[ast.keyword] = [],
    ):
        if isinstance(type, PrimitiveTypes):
            type_str = TypeUtil.property_type_to_python_type(type)
        else:
            type_str = type

        return ast.AnnAssign(
            target=ast.Name(
                id=CompilerStrUtil.to_snake_case(name),
                ctx=ast.Store(),
            ),
            annotation=ast.Name(
                id=type_str,
                ctx=ast.Load(),
            ),
            value=ast.Call(
                func=ast.Name(id="DTOField", ctx=ast.Load()),
                args=[],
                keywords=keywords,
            ),
            simple=1,
        )

    def _build_entity_property_ast(
        self,
        name: str,
        type: PrimitiveTypes,
    ):
        return ast.AnnAssign(
            target=ast.Name(
                id=CompilerStrUtil.to_snake_case(name),
                ctx=ast.Store(),
            ),
            annotation=ast.Name(
                id=TypeUtil.property_type_to_python_type(type),
                ctx=ast.Load(),
            ),
            value=ast.Constant(value=None),
            simple=1,
        )

    def _compile_simple_property(
        self,
        properties_structure,
        map_unique_by_property,
        escopo,
        entity_model,
        ast_dto_attributes,
        ast_entity_attributes,
        props_pk,
        aux_classes,
        pkey,
        prop,
        prefx_class_name: str,
    ):
        enum_class_name = None
        keywords = []

        if prop.pk:
            keywords.append(ast.keyword(arg="pk", value=ast.Constant(True)))
            props_pk.append(pkey)

        if prop.key_alternative:
            keywords.append(ast.keyword(arg="candidate_key", value=ast.Constant(True)))

        if (
            properties_structure.main_properties
            and pkey in properties_structure.main_properties
        ):
            keywords.append(ast.keyword(arg="resume", value=ast.Constant(True)))

        if properties_structure.required and pkey in properties_structure.required:
            keywords.append(ast.keyword(arg="not_null", value=ast.Constant(True)))

        if (
            properties_structure.partition_data
            and pkey in properties_structure.partition_data
        ):
            keywords.append(ast.keyword(arg="partition_data", value=ast.Constant(True)))

        if pkey in map_unique_by_property:
            unique = map_unique_by_property[pkey].index_model
            keywords.append(
                ast.keyword(
                    arg="unique",
                    value=ast.Constant(unique.name),
                )
            )

        if (
            prop.default
        ):  # TODO Verificar esse modo de tratar valores default (principalmente expressões)
            keywords.append(
                ast.keyword(
                    arg="default_value",
                    value=ast.Name(str(prop.default), ctx=ast.Load()),
                )
            )

        if prop.trim:
            keywords.append(ast.keyword(arg="strip", value=ast.Constant(True)))

        max = None
        min = None
        if prop.type in [PrimitiveTypes.STRING, PrimitiveTypes.EMAIL]:
            if prop.max_length:
                max = prop.max_length
            if prop.min_length:
                min = prop.min_length
        elif prop.type in [PrimitiveTypes.INTEGER, PrimitiveTypes.NUMBER]:
            if prop.minimum:
                min = prop.minimum
            if prop.maximum:
                max = prop.maximum

        if max:
            keywords.append(ast.keyword(arg="max", value=ast.Constant(max)))
        if min:
            keywords.append(ast.keyword(arg="min", value=ast.Constant(min)))

        if (
            properties_structure.search_properties
            and pkey in properties_structure.search_properties
        ):
            keywords.append(ast.keyword(arg="search", value=ast.Constant(True)))
        else:
            keywords.append(ast.keyword(arg="search", value=ast.Constant(False)))

        if (
            properties_structure.metric_label
            and pkey in properties_structure.metric_label
        ):
            keywords.append(ast.keyword(arg="metric_label", value=ast.Constant(True)))

        if prop.type == PrimitiveTypes.CPF and not prop.validator:
            keywords.append(
                ast.keyword(
                    arg="validator",
                    value=ast.Attribute(
                        value=ast.Call(
                            func=ast.Name(id="DTOFieldValidators", ctx=ast.Load()),
                            args=[],
                            keywords=[],
                        ),
                        attr="validate_cpf",
                        ctx=ast.Load(),
                    ),
                )
            )
        elif prop.type == PrimitiveTypes.CNPJ and not prop.validator:
            keywords.append(
                ast.keyword(
                    arg="validator",
                    value=ast.Attribute(
                        value=ast.Call(
                            func=ast.Name(id="DTOFieldValidators", ctx=ast.Load()),
                            args=[],
                            keywords=[],
                        ),
                        attr="validate_cnpj",
                        ctx=ast.Load(),
                    ),
                )
            )
        elif prop.type == PrimitiveTypes.CPF_CNPJ and not prop.validator:
            keywords.append(
                ast.keyword(
                    arg="validator",
                    value=ast.Attribute(
                        value=ast.Call(
                            func=ast.Name(id="DTOFieldValidators", ctx=ast.Load()),
                            args=[],
                            keywords=[],
                        ),
                        attr="validate_cpf_or_cnpj",
                        ctx=ast.Load(),
                    ),
                )
            )
        elif prop.type == PrimitiveTypes.EMAIL and not prop.validator:
            keywords.append(
                ast.keyword(
                    arg="validator",
                    value=ast.Attribute(
                        value=ast.Call(
                            func=ast.Name(id="DTOFieldValidators", ctx=ast.Load()),
                            args=[],
                            keywords=[],
                        ),
                        attr="validate_email",
                        ctx=ast.Load(),
                    ),
                )
            )
        elif prop.validator:
            keywords.append(
                ast.keyword(
                    arg="validator",
                    value=ast.Name(prop.validator, ctx=ast.Load()),
                )
            )

        if prop.immutable:
            keywords.append(ast.keyword(arg="read_only", value=ast.Constant(True)))

        if prop.on_save:
            keywords.append(
                ast.keyword(
                    arg="convert_to_entity",
                    value=ast.Name(prop.on_save, ctx=ast.Load()),
                )
            )

        if prop.on_retrieve:
            keywords.append(
                ast.keyword(
                    arg="convert_from_entity",
                    value=ast.Name(id=prop.on_retrieve, ctx=ast.Load()),
                )
            )

        if prop.domain_config:
            result = self._compile_domain_config(
                pkey, prop, escopo, entity_model, prefx_class_name
            )
            if not result:
                raise Exception(f"Erro desconhecido ao compilar a propriedade {pkey}")

            enum_class_name, ast_enum_class = result
            aux_classes.append(ast_enum_class)

        # Resolvendo o nome da propriedade no Entity
        if (
            properties_structure.entity_properties
            and pkey in properties_structure.entity_properties
        ):
            entity_field_name = properties_structure.entity_properties[pkey].column
        else:
            entity_field_name = pkey

        # Escrevendo, se necessário, o alias para o nome da entity
        if entity_field_name != pkey:
            keywords.append(
                ast.keyword(
                    arg="entity_field",
                    value=ast.Constant(value=entity_field_name),
                )
            )

        # Instanciando o atributo AST
        if enum_class_name:
            prop_type = enum_class_name
        else:
            prop_type = TypeUtil.property_type_to_python_type(prop.type)

        ast_attr = self._build_dto_property_ast(pkey, prop_type, keywords)
        ast_dto_attributes.append(ast_attr)

        # Entity
        ast_entity_attr = self._build_entity_property_ast(entity_field_name, prop.type)

        ast_entity_attributes.append(ast_entity_attr)

    def _compile_domain_config(
        self,
        pkey: str,
        prop: PropertyMetaModel | TraitPropertyMetaModel,
        escopo: str,
        entity_model: EntityModelBase,
        prefx_class_name: str,
    ) -> tuple[str, ast.stmt] | None:
        if not prop.domain_config:
            return None

        # Verificando se deveria usar o mapped_value
        use_mapped_value = False
        for value in prop.domain_config:
            if value.mapped_value:
                use_mapped_value = True
                break

        # Compilando as opções do enum
        ast_values = []
        for value in prop.domain_config:
            value_name = CompilerStrUtil.to_snake_case(value.value).upper()

            if use_mapped_value and value.mapped_value is None:
                raise Exception(
                    f"Propriedade '{pkey}' possui domain_config com value '{value.value}' mas sem mapped_value"
                )

            if value.mapped_value is not None:
                ast_value = ast.Assign(
                    targets=[ast.Name(id=value_name, ctx=ast.Store())],
                    value=ast.Tuple(
                        elts=[
                            ast.Constant(value=value.value),
                            ast.Constant(value=value.mapped_value),
                        ],
                        ctx=ast.Load(),
                    ),
                )
            else:
                ast_value = ast.Assign(
                    targets=[ast.Name(id=value_name, ctx=ast.Store())],
                    value=ast.Constant(value=value.value),
                )

            ast_values.append(ast_value)

        # Instanciando o atributo AST
        enum_class_name = f"{CompilerStrUtil.to_pascal_case(escopo)}{CompilerStrUtil.to_pascal_case(prefx_class_name)}{CompilerStrUtil.to_pascal_case(entity_model.id)}{CompilerStrUtil.to_pascal_case(pkey)}Enum"
        ast_enum_class = ast.ClassDef(
            name=enum_class_name,
            bases=[
                ast.Attribute(
                    value=ast.Name(id="enum", ctx=ast.Load()),
                    attr="Enum",
                    ctx=ast.Load(),
                )
            ],
            keywords=[],
            decorator_list=[],
            body=ast_values,
        )

        return enum_class_name, ast_enum_class

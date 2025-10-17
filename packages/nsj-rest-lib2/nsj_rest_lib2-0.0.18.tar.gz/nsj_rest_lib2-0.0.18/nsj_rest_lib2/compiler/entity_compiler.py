import ast

import black

from nsj_rest_lib2.compiler.edl_model.entity_model import EntityModel
from nsj_rest_lib2.compiler.edl_model.entity_model_base import EntityModelBase
from nsj_rest_lib2.compiler.util.str_util import CompilerStrUtil
from nsj_rest_lib2.compiler.util.type_naming_util import compile_entity_class_name


class EntityCompiler:
    def __init__(self):
        pass

    def compile(
        self,
        entity_model: EntityModelBase,
        ast_entity_attributes: list[ast.stmt],
        props_pk: list[str],
        prefix_class_name: str,
    ) -> tuple[str, str]:
        # Imports
        imports = [
            # import datetime
            ast.Import(names=[ast.alias(name="datetime", asname=None)]),
            # import uuid
            ast.Import(names=[ast.alias(name="uuid", asname=None)]),
            # from nsj_rest_lib.entity.entity_base import EntityBase
            ast.ImportFrom(
                module="nsj_rest_lib.entity.entity_base",
                names=[ast.alias(name="EntityBase", asname=None)],
                level=0,
            ),
            # from nsj_rest_lib.decorator.entity import Entity
            ast.ImportFrom(
                module="nsj_rest_lib.decorator.entity",
                names=[ast.alias(name="Entity", asname=None)],
                level=0,
            ),
        ]

        # Entity
        if len(props_pk) > 1:
            raise Exception(
                f"Entidade '{entity_model.id}' possui mais de uma chave primária (ainda não suportado): {props_pk}"
            )
        elif len(props_pk) <= 0:
            raise Exception(
                f"Entidade '{entity_model.id}' não possui nenhuma chave primária (ainda não suportado)."
            )

        default_order_props = []

        key_field = props_pk[0]
        if entity_model.repository.properties:
            if (
                key_field in entity_model.repository.properties
                and entity_model.repository.properties[key_field].column
            ):
                key_field = entity_model.repository.properties[props_pk[0]].column

        if (
            isinstance(entity_model, EntityModel)
            and entity_model.api
            and entity_model.api.default_sort
        ):
            default_order_props = entity_model.api.default_sort

        default_order_fields = []
        for prop in default_order_props:
            if (
                entity_model.repository.properties
                and prop in entity_model.repository.properties
            ):
                field = entity_model.repository.properties[prop].column
            else:
                field = prop

            default_order_fields.append(CompilerStrUtil.to_snake_case(field))

        if CompilerStrUtil.to_snake_case(key_field) not in default_order_fields:
            default_order_fields.append(CompilerStrUtil.to_snake_case(key_field))

        class_name = compile_entity_class_name(entity_model.id, prefix_class_name)
        ast_class = ast.ClassDef(
            name=class_name,
            bases=[ast.Name(id="EntityBase", ctx=ast.Load())],
            keywords=[],
            decorator_list=[
                ast.Call(
                    func=ast.Name(id="Entity", ctx=ast.Load()),
                    args=[],
                    keywords=[
                        ast.keyword(
                            arg="table_name",
                            value=ast.Constant(value=entity_model.repository.map),
                        ),
                        ast.keyword(
                            arg="pk_field",
                            value=ast.Constant(
                                value=CompilerStrUtil.to_snake_case(key_field)
                            ),
                        ),
                        ast.keyword(
                            arg="default_order_fields",
                            value=ast.List(
                                elts=[
                                    ast.Constant(value=field)
                                    for field in default_order_fields
                                ],
                                ctx=ast.Load(),
                            ),
                        ),
                    ],
                )
            ],
            body=ast_entity_attributes,
        )

        # Definindo o módulo
        module = ast.Module(
            body=imports + [ast_class],
            type_ignores=[],
        )
        module = ast.fix_missing_locations(module)

        # Compilando o AST do DTO para o código Python
        code = ast.unparse(module)

        # Chamando o black para formatar o código Python do DTO
        code = black.format_str(code, mode=black.FileMode())

        return (class_name, code)

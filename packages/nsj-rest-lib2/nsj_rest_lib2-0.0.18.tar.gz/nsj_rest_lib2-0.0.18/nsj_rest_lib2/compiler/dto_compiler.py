import ast

import black

from nsj_rest_lib2.compiler.edl_model.entity_model import EntityModel
from nsj_rest_lib2.compiler.edl_model.entity_model_base import EntityModelBase
from nsj_rest_lib2.compiler.edl_model.primitives import BasicTypes
from nsj_rest_lib2.compiler.util.type_naming_util import compile_dto_class_name


class DTOCompiler:
    def __init__(self):
        pass

    def compile(
        self,
        entity_model: EntityModelBase,
        ast_dto_attributes: list[ast.stmt],
        aux_classes: list[ast.stmt],
        related_imports: list[tuple[str, str, str]],
        fixed_filters: list[tuple[str, BasicTypes]],
        prefx_class_name: str,
    ) -> tuple[str, str]:
        """
        Compila o código do DTO a partir do AST e retorna o código compilado.

        :param entity_model: Modelo de entidade
        :type entity_model: EntityModel

        :param ast_dto_attributes: Atributos do DTO
        :type ast_dto_attributes: list[ast.stmt]

        :param aux_classes: Classes auxiliares (enums, agregadores, etc.)
        :type aux_classes: list[ast.stmt]

        :return: Código compilado do DTO
        :rtype: str
        """
        # Criando o ast dos imports
        imports = [
            # import datetime
            ast.Import(names=[ast.alias(name="datetime", asname=None)]),
            # import enum
            ast.Import(names=[ast.alias(name="enum", asname=None)]),
            # import uuid
            ast.Import(names=[ast.alias(name="uuid", asname=None)]),
            # from nsj_rest_lib.decorator.dto import DTO
            ast.ImportFrom(
                module="nsj_rest_lib.decorator.dto",
                names=[ast.alias(name="DTO", asname=None)],
                level=0,
            ),
            # from nsj_rest_lib.descriptor.dto_field import DTOField
            ast.ImportFrom(
                module="nsj_rest_lib.descriptor.dto_field",
                names=[ast.alias(name="DTOField", asname=None)],
                level=0,
            ),
            # from nsj_rest_lib.descriptor.dto_list_field import DTOField
            ast.ImportFrom(
                module="nsj_rest_lib.descriptor.dto_list_field",
                names=[ast.alias(name="DTOListField", asname=None)],
                level=0,
            ),
            # from nsj_rest_lib.descriptor.dto_field_validators import DTOFieldValidators
            ast.ImportFrom(
                module="nsj_rest_lib.descriptor.dto_field_validators",
                names=[ast.alias(name="DTOFieldValidators", asname=None)],
                level=0,
            ),
            # from nsj_rest_lib.dto.dto_base import DTOBase
            ast.ImportFrom(
                module="nsj_rest_lib.dto.dto_base",
                names=[ast.alias(name="DTOBase", asname=None)],
                level=0,
            ),
            # from nsj_rest_lib.descriptor.dto_left_join_field import EntityRelationOwner
            ast.ImportFrom(
                module="nsj_rest_lib.descriptor.dto_left_join_field",
                names=[ast.alias(name="EntityRelationOwner", asname=None)],
                level=0,
            ),
            # from nsj_rest_lib.descriptor.dto_object_field import DTOObjectField
            ast.ImportFrom(
                module="nsj_rest_lib.descriptor.dto_object_field",
                names=[ast.alias(name="DTOObjectField", asname=None)],
                level=0,
            ),
            # from nsj_rest_lib.descriptor import DTOAggregator
            ast.ImportFrom(
                module="nsj_rest_lib.descriptor",
                names=[ast.alias(name="DTOAggregator", asname=None)],
                level=0,
            ),
        ]

        for import_ in related_imports:
            imports.append(
                ast.ImportFrom(
                    module=f"dynamic.{import_[0]}",
                    names=[ast.alias(name=import_[1])],
                    level=0,
                )
            )
            imports.append(
                ast.ImportFrom(
                    module=f"dynamic.{import_[0]}",
                    names=[ast.alias(name=import_[2])],
                    level=0,
                )
            )

        # Keywords para tipos usados em fixed_filters
        keywords_decorator_dto = []
        for fixed_filter in fixed_filters:
            keywords_decorator_dto.append(
                ast.keyword(
                    arg="fixed_filters",
                    value=ast.Dict(
                        keys=[ast.Constant(value=fixed_filter[0])],
                        values=[ast.Constant(value=fixed_filter[1])],
                    ),
                )
            )

        # Criando o ast da classe
        class_name = compile_dto_class_name(entity_model.id, prefx_class_name)
        ast_class = ast.ClassDef(
            name=class_name,
            bases=[ast.Name(id="DTOBase", ctx=ast.Load())],
            keywords=[],
            decorator_list=[
                ast.Call(
                    func=ast.Name(id="DTO", ctx=ast.Load()),
                    args=[],
                    keywords=keywords_decorator_dto,
                )
            ],
            body=ast_dto_attributes,
        )

        # Definindo o módulo
        module = ast.Module(
            body=imports + aux_classes + [ast_class],
            type_ignores=[],
        )
        module = ast.fix_missing_locations(module)

        # Compilando o AST do DTO para o código Python
        code = ast.unparse(module)

        # Chamando o black para formatar o código Python do DTO
        code = black.format_str(code, mode=black.FileMode())

        return (class_name, code)

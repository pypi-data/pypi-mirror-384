import enum

from typing import Annotated, List, Union
from pydantic import StringConstraints

REGEX_EXTERNAL_REF = r"^(\w+)\/(\w+)$"
REGEX_INTERNAL_REF = r"^#\/components\/(\w+)$"

ExternalRefType = Annotated[str, StringConstraints(pattern=REGEX_EXTERNAL_REF)]
InternalRefType = Annotated[str, StringConstraints(pattern=REGEX_INTERNAL_REF)]


class PrimitiveTypes(enum.Enum):
    # TODO Validar esses tipos
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    UUID = "uuid"
    CURRENCY = "currency"
    QUANTITY = "quantity"
    CPF = "cpf"
    CNPJ = "cnpj"
    CPF_CNPJ = "cpf_cnpj"
    EMAIL = "email"
    DATE = "date"
    DATETIME = "datetime"


PropertyType = Union[PrimitiveTypes, ExternalRefType, InternalRefType]

MAPPING_PRIMITIVE_TYPES_TO_PYTHON = {
    PrimitiveTypes.STRING: "str",
    PrimitiveTypes.NUMBER: "float",
    PrimitiveTypes.INTEGER: "int",
    PrimitiveTypes.BOOLEAN: "bool",
    PrimitiveTypes.UUID: "uuid.UUID",
    PrimitiveTypes.CURRENCY: "float",
    PrimitiveTypes.QUANTITY: "float",
    PrimitiveTypes.CPF: "str",
    PrimitiveTypes.CNPJ: "str",
    PrimitiveTypes.CPF_CNPJ: "str",
    PrimitiveTypes.EMAIL: "str",
    PrimitiveTypes.DATE: "datetime.date",
    PrimitiveTypes.DATETIME: "datetime.datetime",
}

BasicTypes = int | bool | float | str
DefaultTypes = BasicTypes | List[BasicTypes]


class CardinalityTypes(enum.Enum):
    C1_1 = "1_1"
    C1_N = "1_N"
    CN_N = "N_N"

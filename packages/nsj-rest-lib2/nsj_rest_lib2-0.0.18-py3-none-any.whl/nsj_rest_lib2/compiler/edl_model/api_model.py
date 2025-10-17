from pydantic import BaseModel, Field
from typing import List, Optional, Literal

APIVerbs = Literal["GET", "POST", "PUT", "DELETE", "PATCH"]


class APIModel(BaseModel):
    resource: str = Field(
        ...,
        description="Nome do recurso REST (rota base dos endpoints; exemplo: 'clientes').",
    )
    expose: Optional[bool] = Field(
        default=True,
        description="Indica se a API deve ser exposta (padrão: True).",
    )
    verbs: Optional[List[APIVerbs]] = Field(
        default=["GET", "POST", "PUT", "DELETE", "PATCH"],
        description="Lista de verbos HTTP suportados pela API (padrão: todos).",
    )
    default_sort: Optional[List[str]] = Field(
        None,
        description="Lista de campos usados na ordenação padrão (padrão: se nada for fornecido, será usada, ao menos, a PK).",
    )

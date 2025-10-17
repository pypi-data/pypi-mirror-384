from pydantic import BaseModel, Field
from typing import List, Optional

from nsj_rest_lib2.compiler.edl_model.column_meta_model import ColumnMetaModel
from nsj_rest_lib2.compiler.edl_model.index_model import IndexModel


class RepositoryModel(BaseModel):
    map: str = Field(
        ..., description="Nome da tabela, no BD, para a qual a entidade é mapeada."
    )
    shared_table: Optional[bool] = Field(
        default=False,
        description="Indica se a tabela é compartilhada entre múltiplas entidades (padrão: False).",
    )
    table_owner: Optional[bool] = Field(
        None, description="Indica que essa entidade é dona da tabela (schema)."
    )  # TODO Validar explicação
    properties: Optional[dict[str, ColumnMetaModel]] = Field(
        None, description="Dicionário de colunas da entidade."
    )
    indexes: Optional[List[IndexModel]] = Field(
        None, description="Lista de índices de banco de dados, associados à entidade."
    )

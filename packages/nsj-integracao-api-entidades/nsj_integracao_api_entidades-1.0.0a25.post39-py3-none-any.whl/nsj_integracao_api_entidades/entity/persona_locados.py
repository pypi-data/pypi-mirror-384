import datetime
import uuid

from nsj_rest_lib.entity.entity_base import EntityBase
from nsj_rest_lib.decorator.entity import Entity


@Entity(
    table_name="persona.locados",
    pk_field="locado",
    default_order_fields=["locado"],
)
class LocadosEntity(EntityBase):
    codigo: str = None
    cpf: str = None
    nome: str = None
    paisresidencia: str = None
    tipologradouroresidencia: str = None
    logradouroresidencia: str = None
    numerologradouroresidencia: str = None
    complementologradouroresidencia: str = None
    bairroresidencia: str = None
    cepresidencia: str = None
    municipioresidencia: str = None
    cidaderesidencia: str = None
    empresa: uuid.UUID = None
    estabelecimento: uuid.UUID = None
    departamento: uuid.UUID = None
    locado: uuid.UUID = None
    horario: uuid.UUID = None
    prestadorservico: uuid.UUID = None
    nivelcargo: uuid.UUID = None
    identificacaonasajon: str = None
    dataadmissao: datetime.datetime = None
    datavencimento: datetime.datetime = None
    ufresidencia: str = None
    salario: float = None
    lastupdate: datetime.datetime = None
    tenant: int = None

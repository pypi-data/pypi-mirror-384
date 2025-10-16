import datetime
import uuid

from nsj_rest_lib.entity.entity_base import EntityBase
from nsj_rest_lib.decorator.entity import Entity

@Entity(
    table_name="persona.gestoreslocados",
    pk_field="gestorlocado",
    default_order_fields=["gestorlocado"],
)
class GestoreslocadosEntity(EntityBase):
    gestorlocado: uuid.UUID = None  # primary key
    locado: uuid.UUID = None
    tipogestor: int = None
    gestortrabalhador: uuid.UUID = None
    gestornaotrabalhador: uuid.UUID = None
    percentualengajamento: float = None
    identificacaonasajongestor: str = None
    lastupdate: datetime.datetime = None
    tenant: int = None

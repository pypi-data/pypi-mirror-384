
import datetime
import uuid

from nsj_rest_lib.entity.entity_base import EntityBase
from nsj_rest_lib.decorator.entity import Entity


@Entity(
    table_name="ns.conjuntosunidades",
    pk_field="conjuntounidade",
    default_order_fields=["conjuntounidade"],
)
class ConjuntosunidadeEntity(EntityBase):
    conjuntounidade: uuid.UUID = None
    tenant: int = None
    registro: uuid.UUID = None
    conjunto: uuid.UUID = None
    lastupdate: datetime.datetime = None

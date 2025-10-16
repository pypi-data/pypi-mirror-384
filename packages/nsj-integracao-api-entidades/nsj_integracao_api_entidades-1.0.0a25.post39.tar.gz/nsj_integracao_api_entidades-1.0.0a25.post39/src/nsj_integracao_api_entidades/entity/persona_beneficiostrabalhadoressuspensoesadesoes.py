
import datetime
import uuid

from nsj_rest_lib.entity.entity_base import EntityBase
from nsj_rest_lib.decorator.entity import Entity


@Entity(
    table_name="persona.beneficiostrabalhadoressuspensoesadesoes",
    pk_field="beneficiotrabalhadorsuspensaoadesao",
    default_order_fields=["beneficiotrabalhadorsuspensaoadesao"],
)
class BeneficiostrabalhadoressuspensoesadesoeEntity(EntityBase):
    beneficiotrabalhadorsuspensaoadesao: uuid.UUID = None
    tenant: int = None
    beneficiotrabalhadoradesao: uuid.UUID = None
    datainicio: datetime.datetime = None
    datafim: datetime.datetime = None
    lastupdate: datetime.datetime = None


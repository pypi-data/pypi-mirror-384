
import datetime
import uuid

from nsj_rest_lib.entity.entity_base import EntityBase
from nsj_rest_lib.decorator.entity import Entity


@Entity(
    table_name="persona.beneficiostrabalhadoresadesoes",
    pk_field="beneficiotrabalhadoradesao",
    default_order_fields=["beneficiotrabalhadoradesao"],
)
class BeneficiostrabalhadoresadesoeEntity(EntityBase):
    beneficiotrabalhadoradesao: uuid.UUID = None
    tenant: int = None
    beneficiotrabalhador: uuid.UUID = None
    dataadesao: datetime.datetime = None
    dataexclusao: datetime.datetime = None
    lastupdate: datetime.datetime = None


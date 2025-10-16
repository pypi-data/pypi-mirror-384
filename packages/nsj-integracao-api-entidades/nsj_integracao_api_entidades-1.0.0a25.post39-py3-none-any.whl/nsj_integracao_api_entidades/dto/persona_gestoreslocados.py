import datetime
import uuid

from nsj_rest_lib.decorator.dto import DTO
from nsj_rest_lib.descriptor.dto_field import DTOField
from nsj_rest_lib.descriptor.dto_field_validators import DTOFieldValidators
from nsj_rest_lib.dto.dto_base import DTOBase

# Configuracoes execucao
from nsj_integracao_api_entidades.config import tenant_is_partition_data

@DTO()
class GestoreslocadosDTO(DTOBase):
    id: uuid.UUID = DTOField(
        pk=True,
        entity_field='gestorlocado',
        resume=True,
        not_null=True,
        strip=True,
        min=36,
        max=36,
        validator=DTOFieldValidators().validate_uuid,
    )
    tenant: int = DTOField(
        partition_data=tenant_is_partition_data,
        resume=True,
        not_null=True,
    )
    locado: uuid.UUID = DTOField(
        validator=DTOFieldValidators().validate_uuid,
    )
    tipogestor: int = DTOField()
    gestortrabalhador: uuid.UUID = DTOField(
        validator=DTOFieldValidators().validate_uuid,
    )
    gestornaotrabalhador: uuid.UUID = DTOField(
        validator=DTOFieldValidators().validate_uuid,
    )
    percentualengajamento: float = DTOField()
    identificacaonasajongestor: str = DTOField(
        strip=True,
        max=250,
    )
    lastupdate: datetime.datetime = DTOField()

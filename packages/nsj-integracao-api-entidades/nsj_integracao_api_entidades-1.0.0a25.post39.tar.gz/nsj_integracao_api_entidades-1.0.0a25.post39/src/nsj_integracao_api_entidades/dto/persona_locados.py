import datetime
import uuid

from nsj_rest_lib.decorator.dto import DTO
from nsj_rest_lib.descriptor.dto_field import DTOField
from nsj_rest_lib.descriptor.dto_field_validators import DTOFieldValidators
from nsj_rest_lib.dto.dto_base import DTOBase

# Configuracoes execucao
from nsj_integracao_api_entidades.config import tenant_is_partition_data

@DTO()
class LocadosDTO(DTOBase):
    # Atributos da entidade
    id: uuid.UUID = DTOField(
        pk=True,
        entity_field='locado',
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
    codigo: str = DTOField(strip=True, min=1, max=6)
    cpf: str = DTOField(strip=True, min=11, max=11)
    nome: str = DTOField(strip=True, max=80)
    paisresidencia: str = DTOField(strip=True, max=5)
    tipologradouroresidencia: str = DTOField(strip=True, max=10)
    logradouroresidencia: str = DTOField(strip=True, max=80)
    numerologradouroresidencia: str = DTOField(strip=True, max=10)
    complementologradouroresidencia: str = DTOField(strip=True, max=30)
    bairroresidencia: str = DTOField(strip=True, max=30)
    cepresidencia: str = DTOField(strip=True, max=10)
    municipioresidencia: str = DTOField(strip=True, max=8)
    cidaderesidencia: str = DTOField(strip=True, max=30)
    empresa: uuid.UUID = DTOField(validator=DTOFieldValidators().validate_uuid)
    estabelecimento: uuid.UUID = DTOField(validator=DTOFieldValidators().validate_uuid)
    departamento: uuid.UUID = DTOField(validator=DTOFieldValidators().validate_uuid)
    horario: uuid.UUID = DTOField(validator=DTOFieldValidators().validate_uuid)
    prestadorservico: uuid.UUID = DTOField(validator=DTOFieldValidators().validate_uuid)
    nivelcargo: uuid.UUID = DTOField(validator=DTOFieldValidators().validate_uuid)
    identificacaonasajon: str = DTOField(strip=True, max=250)
    dataadmissao: datetime.datetime = DTOField()
    datavencimento: datetime.datetime = DTOField()
    ufresidencia: str = DTOField(strip=True, max=2)
    salario: float = DTOField()
    lastupdate: datetime.datetime = DTOField()

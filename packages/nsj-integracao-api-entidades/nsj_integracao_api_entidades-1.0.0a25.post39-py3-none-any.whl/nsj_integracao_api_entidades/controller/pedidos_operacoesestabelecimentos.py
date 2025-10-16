
from nsj_rest_lib.controller.get_route import GetRoute
from nsj_rest_lib.controller.list_route import ListRoute
from nsj_rest_lib.controller.post_route import PostRoute
from nsj_rest_lib.controller.put_route import PutRoute
from nsj_rest_lib.controller.delete_route import DeleteRoute
from nsj_integracao_api_entidades.nsj_rest_lib_extensions.controller.integrity_check_route import IntegrityCheckRoute

from nsj_integracao_api_entidades.auth import auth
from nsj_integracao_api_entidades.injector_factory import InjectorFactory
from nsj_integracao_api_entidades.settings import application, APP_NAME, MOPE_CODE

from nsj_integracao_api_entidades.dto.pedidos_operacoesestabelecimentos import OperacoesestabelecimentoDTO as DTO
from nsj_integracao_api_entidades.entity.pedidos_operacoesestabelecimentos import OperacoesestabelecimentoEntity as Entity

ROUTE = f"/{APP_NAME}/{MOPE_CODE}/pedidos/operacoesestabelecimentos"
ID_ROUTE = f"/{APP_NAME}/{MOPE_CODE}/pedidos/operacoesestabelecimentos/<id>"
INTEGRITY_ROUTE = f"/{APP_NAME}/{MOPE_CODE}/pedidos/operacoesestabelecimentos/verificacao-integridade"
LIST_BULK_ROUTE = f'{ROUTE}/bulk'

@application.route(ROUTE, methods=["GET"])
@auth.requires_api_key_or_access_token()
@ListRoute(
    url=ROUTE,
    http_method="GET",
    dto_class=DTO,
    entity_class=Entity,
    injector_factory=InjectorFactory,
)
def pedidos_operacoesestabelecimentos_list_action(_, response):
    return response


@application.route(f"{ROUTE}/<id>", methods=["GET"])
@auth.requires_api_key_or_access_token()
@GetRoute(
    url=f"{ROUTE}/<id>",
    http_method="GET",
    dto_class=DTO,
    entity_class=Entity,
    injector_factory=InjectorFactory,
)
def pedidos_operacoesestabelecimentos_get_action(_, response):
    return response


@application.route(ROUTE, methods=["POST"])
@auth.requires_api_key_or_access_token()
@PostRoute(
    url=ROUTE,
    http_method="POST",
    dto_class=DTO,
    entity_class=Entity,
    injector_factory=InjectorFactory,
)
def pedidos_operacoesestabelecimentos_post_action(_, response):
    return response


@application.route(ID_ROUTE, methods=["PUT"])
@auth.requires_api_key_or_access_token()
@PutRoute(
    url=ID_ROUTE,
    http_method="PUT",
    dto_class=DTO,
    entity_class=Entity,
    injector_factory=InjectorFactory,
)
def pedidos_operacoesestabelecimentos_put_action(_, response):
    return response


@application.route(ROUTE, methods=["PUT"])
@auth.requires_api_key_or_access_token()
@PutRoute(
    url=ROUTE,
    http_method="PUT",
    dto_class=DTO,
    entity_class=Entity,
    injector_factory=InjectorFactory,
)
def pedidos_operacoesestabelecimentos_put_list_action(_, response):
    return response


@application.route(ID_ROUTE, methods=["DELETE"])
@auth.requires_api_key_or_access_token()
@DeleteRoute(
    url=ID_ROUTE,
    http_method="DELETE",
    dto_class=DTO,
    entity_class=Entity,
    injector_factory=InjectorFactory,
)
def pedidos_operacoesestabelecimentos_delete_action(_, response):
    return response


@application.route(ROUTE, methods=["DELETE"])
@auth.requires_api_key_or_access_token()
@DeleteRoute(
    url=ROUTE,
    http_method="DELETE",
    dto_class=DTO,
    entity_class=Entity,
    injector_factory=InjectorFactory,
)
def pedidos_operacoesestabelecimentos_delete_list_action(_, response):
    return response


@application.route(INTEGRITY_ROUTE, methods=["GET"])
@auth.requires_api_key_or_access_token()
@IntegrityCheckRoute(
    url=INTEGRITY_ROUTE,
    http_method="GET",
    dto_class=DTO,
    entity_class=Entity,
    injector_factory=InjectorFactory,
)
def pedidos_operacoesestabelecimentos_integrity_check_action(_, response):
    return response


@application.route(LIST_BULK_ROUTE, methods=['DELETE'])
@DeleteRoute(
    url=LIST_BULK_ROUTE,
    http_method='DELETE',
    dto_class=DTO,
    entity_class=Entity
)
def pedidos_operacoesestabelecimentos_delete_bulk_action(_, response):
    return response


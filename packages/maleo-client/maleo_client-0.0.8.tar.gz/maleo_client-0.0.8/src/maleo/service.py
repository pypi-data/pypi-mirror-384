from Crypto.PublicKey.RSA import RsaKey
from typing import Generic
from maleo.database.enums import CacheOrigin, CacheLayer
from maleo.database.handlers import RedisHandler
from maleo.logging.logger import Client
from maleo.schemas.application import ApplicationContext
from maleo.schemas.operation.context import generate
from maleo.schemas.operation.enums import Origin, Layer, Target
from maleo.schemas.resource import Resource, AggregateField
from ..http import HTTPClientManager
from .config import AnyMaleoClientConfigT


class MaleoClientService(Generic[AnyMaleoClientConfigT]):
    resource: Resource

    def __init__(
        self,
        *,
        application_context: ApplicationContext,
        config: AnyMaleoClientConfigT,
        logger: Client,
        http_client_manager: HTTPClientManager,
        private_key: RsaKey,
        redis: RedisHandler,
    ):
        self._application_context = application_context
        self._config = config
        self._logger = logger
        self._http_client_manager = http_client_manager
        self._private_key = private_key
        self._redis = redis

        self._namespace = self._redis.config.additional.build_namespace(
            self.resource.aggregate(AggregateField.KEY),
            use_self_base=True,
            client=self._config.key,
            origin=CacheOrigin.CLIENT,
            layer=CacheLayer.SERVICE,
        )

        self._operation_context = generate(
            origin=Origin.CLIENT, layer=Layer.SERVICE, target=Target.INTERNAL
        )

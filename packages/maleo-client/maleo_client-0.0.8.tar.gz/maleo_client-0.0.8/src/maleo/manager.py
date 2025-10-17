from abc import ABC, abstractmethod
from Crypto.PublicKey.RSA import RsaKey
from typing import Generic
from maleo.database.handlers import RedisHandler
from maleo.enums.environment import Environment
from maleo.enums.service import ServiceKey
from maleo.logging.config import LogConfig
from maleo.logging.logger import Client
from maleo.schemas.application import ApplicationContext
from ..http import HTTPClientManager
from .config import AnyMaleoClientConfigT


class MaleoClientManager(ABC, Generic[AnyMaleoClientConfigT]):
    def __init__(
        self,
        *,
        application_context: ApplicationContext,
        config: AnyMaleoClientConfigT,
        log_config: LogConfig,
        private_key: RsaKey,
        redis: RedisHandler,
    ):
        self._application_context = application_context
        self._config = config
        self._log_config = log_config

        self._key = self._config.key
        self._name = self._config.name

        self._logger = Client[Environment, ServiceKey](
            environment=self._application_context.environment,
            service_key=self._application_context.service_key,
            client_key=self._key,
            config=log_config,
        )

        self._http_client_manager = HTTPClientManager()
        self._private_key = private_key
        self._redis = redis

        self.initalize_services()
        self._logger.info(f"{self._name} client manager initialized successfully")

    @abstractmethod
    def initalize_services(self):
        """Initialize all services of this client"""

from abc import ABC, abstractmethod
from google.oauth2.service_account import Credentials
from pathlib import Path
from typing import Generic, Type
from uuid import UUID
from maleo.enums.environment import Environment
from maleo.enums.service import ServiceKey
from maleo.google.secret import Format, GoogleSecretManager
from maleo.logging.config import LogConfig
from maleo.logging.logger import ApplicationLoggers
from maleo.schemas.application import ApplicationSettingsT, ApplicationContext
from maleo.schemas.key.rsa import Keys
from maleo.utils.loaders.yaml import from_path, from_string
from .config import ApplicationConfigT


class ApplicationManager(ABC, Generic[ApplicationSettingsT, ApplicationConfigT]):
    def __init__(
        self,
        operation_id: UUID,
        log_config: LogConfig,
        google_credentials: Credentials,
        google_secret_manager: GoogleSecretManager,
        settings: ApplicationSettingsT,
        config_cls: Type[ApplicationConfigT],
    ):
        self._google_credentials = google_credentials
        self._log_config = log_config
        self.settings = settings
        self._config_cls = config_cls
        self._google_secret_manager = google_secret_manager

        self.application_context = ApplicationContext.from_settings(settings)

        self._initialize_config(operation_id)
        self._initialize_keys(operation_id)
        self._initialize_loggers()
        self._initialize_database()
        self._initialize_google_cloud_storage()

    def _initialize_config(self, operation_id: UUID):
        use_local = self.settings.USE_LOCAL_CONFIG
        config_path = self.settings.CONFIG_PATH

        if use_local and config_path is not None and isinstance(config_path, str):
            config_path = Path(config_path)
            if config_path.exists() and config_path.is_file():
                data = from_path(config_path)
                self.config: ApplicationConfigT = self._config_cls.model_validate(data)
                return

        name = f"{self.settings.SERVICE_KEY}-config-{self.settings.ENVIRONMENT}"
        read_secret = self._google_secret_manager.read(
            Format.STRING, name=name, operation_id=operation_id
        )
        data = from_string(read_secret.data.value)
        self.config: ApplicationConfigT = self._config_cls.model_validate(data)

    def _initialize_keys(self, operation_id: UUID):
        if self.settings.PRIVATE_KEY_PASSWORD is not None:
            password = self.settings.PRIVATE_KEY_PASSWORD
        else:
            read_key_password = self._google_secret_manager.read(
                Format.STRING,
                name="maleo-key-password",
                operation_id=operation_id,
            )
            password = read_key_password.data.value

        if self.settings.USE_LOCAL_KEY:
            self.keys = Keys.from_path(
                private=self.settings.PRIVATE_KEY_PATH,
                public=self.settings.PUBLIC_KEY_PATH,
                password=password,
            )
        else:
            read_private_key = self._google_secret_manager.read(
                Format.STRING, name="maleo-private-key", operation_id=operation_id
            )
            private = read_private_key.data.value

            read_public_key = self._google_secret_manager.read(
                Format.STRING, name="maleo-public-key", operation_id=operation_id
            )
            public = read_public_key.data.value

            self.keys = Keys.from_string(
                private=private, public=public, password=password
            )

    def _initialize_loggers(self):
        self.loggers = ApplicationLoggers[Environment, ServiceKey].new(
            environment=self.settings.ENVIRONMENT,
            service_key=self.settings.SERVICE_KEY,
            config=self._log_config,
        )

    @abstractmethod
    def _initialize_database(self):
        """Initialize all given databases"""

    @abstractmethod
    def _initialize_google_cloud_storage(self):
        """Initialize Google Cloud Storage"""

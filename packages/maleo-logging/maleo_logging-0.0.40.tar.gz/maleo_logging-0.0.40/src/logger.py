import logging
import os
from datetime import datetime, timezone
from google.cloud.logging.handlers import CloudLoggingHandler
from pydantic import BaseModel, ConfigDict, Field
from typing import Generic, Literal, TypeVar, overload
from maleo.types.dict import StrToStrDict
from maleo.types.misc import StrOrStrEnum
from maleo.types.string import OptStr
from .config import LogConfig
from .enums import LoggerType


EnvironmentT = TypeVar("EnvironmentT", bound=StrOrStrEnum)
ServiceKeyT = TypeVar("ServiceKeyT", bound=StrOrStrEnum)


# * We suggest to NOT use this class
# * Instead use the inherited classes
class Base(
    logging.Logger,
    Generic[
        EnvironmentT,
        ServiceKeyT,
    ],
):
    def __init__(
        self,
        type: LoggerType = LoggerType.BASE,
        *,
        environment: EnvironmentT | None = None,
        service_key: ServiceKeyT | None = None,
        client_key: OptStr = None,
        config: LogConfig,
    ):
        self._type = type  # Declare logger type

        # Ensure environment exists
        actual_environment = environment or os.getenv("ENVIRONMENT")
        if actual_environment is None:
            raise ValueError(
                "ENVIRONMENT environment variable must be set if 'environment' is set to None"
            )
        else:
            self._environment = actual_environment

        # Ensure service_key exists
        actual_service_key = service_key or os.getenv("SERVICE_KEY")
        if actual_service_key is None:
            raise ValueError(
                "SERVICE_KEY environment variable must be set if 'service_key' is set to None"
            )
        else:
            self._service_key = actual_service_key

        self._client_key = client_key  # Declare client key

        # Ensure client_key is valid if logger type is a client
        if self._type == LoggerType.CLIENT and self._client_key is None:
            raise ValueError(
                "'client_key' parameter must be provided if 'logger_type' is 'client'"
            )

        # Define logger name
        base_name = f"{self._environment} - {self._service_key} - {self._type}"
        if self._type == LoggerType.CLIENT:
            self._name = f"{base_name} - {self._client_key}"
        else:
            self._name = base_name

        # Define log labels
        self._labels: StrToStrDict = {
            "logger_type": self._type.value,
            "service_environment": str(self._environment),
            "service_key": str(self._service_key),
        }
        if client_key is not None:
            self._labels["client_key"] = client_key
        if config.labels is not None:
            self._labels.update(config.labels)

        self._config = config

        super().__init__(self._name, self._config.level)  # Init the superclass's logger

        # Clear existing handlers to prevent duplicates
        for handler in list(self.handlers):
            self.removeHandler(handler)
            handler.close()

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        self.addHandler(console_handler)

        # Google Cloud Logging handler (If enabled)
        if self._config.google_cloud_logging is not None:
            self._cloud_logging_handler = CloudLoggingHandler(
                self._config.google_cloud_logging,
                name=self._name.replace(" ", ""),
                labels=self._labels,
            )
            self.addHandler(self._cloud_logging_handler)
        else:
            self.warning(
                "Cloud logging is not configured. Will not add cloud logging handler"
            )

        # Define aggregate log directory
        if self._config.aggregate_file_name is not None:
            self._aggregate_log_dir = os.path.join(self._config.dir, "aggregate")
            os.makedirs(self._aggregate_log_dir, exist_ok=True)
            if not self._config.aggregate_file_name.endswith(".log"):
                self._config.aggregate_file_name += ".log"
            log_filename = os.path.join(
                self._aggregate_log_dir, self._config.aggregate_file_name
            )

            # File handler
            file_handler = logging.FileHandler(log_filename, mode="a")
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            self.addHandler(file_handler)

        # Define individual log directory
        if self._config.individual_log:
            self._individual_log_dir = os.path.join(self._config.dir, self._type)
            if self._type is LoggerType.CLIENT:
                if self._client_key is None:
                    raise ValueError(
                        "'client_key' parameter must be provided if 'logger_type' is 'client'"
                    )
                self._individual_log_dir = os.path.join(
                    self._individual_log_dir, self._client_key
                )
            os.makedirs(self._individual_log_dir, exist_ok=True)

            # Generate timestamped filename
            log_filename = os.path.join(
                self._individual_log_dir,
                f"{datetime.now(tz=timezone.utc).isoformat(timespec="seconds")}.log",
            )

            # File handler
            file_handler = logging.FileHandler(log_filename, mode="a")
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            self.addHandler(file_handler)

        logging.Logger.manager.loggerDict[self._name] = self

    def dispose(self):
        """Dispose of the logger by removing all handlers."""
        for handler in list(self.handlers):
            self.removeHandler(handler)
            handler.close()
        self.handlers.clear()


class Application(Base[EnvironmentT, ServiceKeyT], Generic[EnvironmentT, ServiceKeyT]):
    def __init__(
        self,
        *,
        environment: EnvironmentT | None = None,
        service_key: ServiceKeyT | None = None,
        config: LogConfig,
    ):
        super().__init__(
            LoggerType.APPLICATION,
            environment=environment,
            service_key=service_key,
            client_key=None,
            config=config,
        )


class Cache(Base[EnvironmentT, ServiceKeyT], Generic[EnvironmentT, ServiceKeyT]):
    def __init__(
        self,
        *,
        environment: EnvironmentT | None = None,
        service_key: ServiceKeyT | None = None,
        config: LogConfig,
    ):
        super().__init__(
            LoggerType.CACHE,
            environment=environment,
            service_key=service_key,
            client_key=None,
            config=config,
        )


class Client(Base[EnvironmentT, ServiceKeyT], Generic[EnvironmentT, ServiceKeyT]):
    def __init__(
        self,
        *,
        environment: EnvironmentT | None = None,
        service_key: ServiceKeyT | None = None,
        client_key: str,
        config: LogConfig,
    ):
        super().__init__(
            LoggerType.CLIENT,
            environment=environment,
            service_key=service_key,
            client_key=client_key,
            config=config,
        )


class Controller(Base[EnvironmentT, ServiceKeyT], Generic[EnvironmentT, ServiceKeyT]):
    def __init__(
        self,
        *,
        environment: EnvironmentT | None = None,
        service_key: ServiceKeyT | None = None,
        config: LogConfig,
    ):
        super().__init__(
            LoggerType.CONTROLLER,
            environment=environment,
            service_key=service_key,
            client_key=None,
            config=config,
        )


class Database(Base[EnvironmentT, ServiceKeyT], Generic[EnvironmentT, ServiceKeyT]):
    def __init__(
        self,
        *,
        environment: EnvironmentT | None = None,
        service_key: ServiceKeyT | None = None,
        config: LogConfig,
    ):
        super().__init__(
            LoggerType.DATABASE,
            environment=environment,
            service_key=service_key,
            client_key=None,
            config=config,
        )


class Exception(Base[EnvironmentT, ServiceKeyT], Generic[EnvironmentT, ServiceKeyT]):
    def __init__(
        self,
        *,
        environment: EnvironmentT | None = None,
        service_key: ServiceKeyT | None = None,
        config: LogConfig,
    ):
        super().__init__(
            LoggerType.EXCEPTION,
            environment=environment,
            service_key=service_key,
            client_key=None,
            config=config,
        )


class Middleware(Base[EnvironmentT, ServiceKeyT], Generic[EnvironmentT, ServiceKeyT]):
    def __init__(
        self,
        *,
        environment: EnvironmentT | None = None,
        service_key: ServiceKeyT | None = None,
        config: LogConfig,
    ):
        super().__init__(
            LoggerType.MIDDLEWARE,
            environment=environment,
            service_key=service_key,
            client_key=None,
            config=config,
        )


class Repository(Base[EnvironmentT, ServiceKeyT], Generic[EnvironmentT, ServiceKeyT]):
    def __init__(
        self,
        *,
        environment: EnvironmentT | None = None,
        service_key: ServiceKeyT | None = None,
        config: LogConfig,
    ):
        super().__init__(
            LoggerType.REPOSITORY,
            environment=environment,
            service_key=service_key,
            client_key=None,
            config=config,
        )


class Service(Base[EnvironmentT, ServiceKeyT], Generic[EnvironmentT, ServiceKeyT]):
    def __init__(
        self,
        *,
        environment: EnvironmentT | None = None,
        service_key: ServiceKeyT | None = None,
        config: LogConfig,
    ):
        super().__init__(
            LoggerType.SERVICE,
            environment=environment,
            service_key=service_key,
            client_key=None,
            config=config,
        )


@overload
def create(
    type: Literal[LoggerType.APPLICATION],
    *,
    environment: EnvironmentT | None = None,
    service_key: ServiceKeyT | None = None,
    config: LogConfig,
) -> Application[EnvironmentT, ServiceKeyT]: ...
@overload
def create(
    type: Literal[LoggerType.CACHE],
    *,
    environment: EnvironmentT | None = None,
    service_key: ServiceKeyT | None = None,
    config: LogConfig,
) -> Cache[EnvironmentT, ServiceKeyT]: ...
@overload
def create(
    type: Literal[LoggerType.CLIENT],
    *,
    environment: EnvironmentT | None = None,
    service_key: ServiceKeyT | None = None,
    client_key: str,
    config: LogConfig,
) -> Client[EnvironmentT, ServiceKeyT]: ...
@overload
def create(
    type: Literal[LoggerType.CONTROLLER],
    *,
    environment: EnvironmentT | None = None,
    service_key: ServiceKeyT | None = None,
    config: LogConfig,
) -> Controller[EnvironmentT, ServiceKeyT]: ...
@overload
def create(
    type: Literal[LoggerType.DATABASE],
    *,
    environment: EnvironmentT | None = None,
    service_key: ServiceKeyT | None = None,
    config: LogConfig,
) -> Database[EnvironmentT, ServiceKeyT]: ...
@overload
def create(
    type: Literal[LoggerType.EXCEPTION],
    *,
    environment: EnvironmentT | None = None,
    service_key: ServiceKeyT | None = None,
    config: LogConfig,
) -> Exception[EnvironmentT, ServiceKeyT]: ...
@overload
def create(
    type: Literal[LoggerType.MIDDLEWARE],
    *,
    environment: EnvironmentT | None = None,
    service_key: ServiceKeyT | None = None,
    config: LogConfig,
) -> Middleware[EnvironmentT, ServiceKeyT]: ...
@overload
def create(
    type: Literal[LoggerType.REPOSITORY],
    *,
    environment: EnvironmentT | None = None,
    service_key: ServiceKeyT | None = None,
    config: LogConfig,
) -> Repository[EnvironmentT, ServiceKeyT]: ...
@overload
def create(
    type: Literal[LoggerType.SERVICE],
    *,
    environment: EnvironmentT | None = None,
    service_key: ServiceKeyT | None = None,
    config: LogConfig,
) -> Service[EnvironmentT, ServiceKeyT]: ...
def create(
    type: LoggerType = LoggerType.BASE,
    *,
    environment: EnvironmentT | None = None,
    service_key: ServiceKeyT | None = None,
    client_key: OptStr = None,
    config: LogConfig,
) -> (
    Base[EnvironmentT, ServiceKeyT]
    | Application[EnvironmentT, ServiceKeyT]
    | Cache[EnvironmentT, ServiceKeyT]
    | Client[EnvironmentT, ServiceKeyT]
    | Controller[EnvironmentT, ServiceKeyT]
    | Database[EnvironmentT, ServiceKeyT]
    | Exception[EnvironmentT, ServiceKeyT]
    | Middleware[EnvironmentT, ServiceKeyT]
    | Repository[EnvironmentT, ServiceKeyT]
    | Service[EnvironmentT, ServiceKeyT]
):
    if type is LoggerType.BASE:
        return Base[EnvironmentT, ServiceKeyT](
            environment=environment,
            service_key=service_key,
            client_key=client_key,
            config=config,
        )
    elif type is LoggerType.APPLICATION:
        return Application[EnvironmentT, ServiceKeyT](
            environment=environment,
            service_key=service_key,
            config=config,
        )
    elif type is LoggerType.CACHE:
        return Cache[EnvironmentT, ServiceKeyT](
            environment=environment,
            service_key=service_key,
            config=config,
        )
    elif type is LoggerType.CLIENT:
        if client_key is None:
            raise ValueError(
                "Argument 'client_key' can not be None if 'logger_type' is 'client'"
            )
        return Client[EnvironmentT, ServiceKeyT](
            environment=environment,
            service_key=service_key,
            client_key=client_key,
            config=config,
        )
    elif type is LoggerType.CONTROLLER:
        return Controller[EnvironmentT, ServiceKeyT](
            environment=environment,
            service_key=service_key,
            config=config,
        )
    elif type is LoggerType.DATABASE:
        return Database[EnvironmentT, ServiceKeyT](
            environment=environment,
            service_key=service_key,
            config=config,
        )
    elif type is LoggerType.EXCEPTION:
        return Exception[EnvironmentT, ServiceKeyT](
            environment=environment,
            service_key=service_key,
            config=config,
        )
    elif type is LoggerType.MIDDLEWARE:
        return Middleware[EnvironmentT, ServiceKeyT](
            environment=environment,
            service_key=service_key,
            config=config,
        )
    elif type is LoggerType.REPOSITORY:
        return Repository[EnvironmentT, ServiceKeyT](
            environment=environment,
            service_key=service_key,
            config=config,
        )
    elif type is LoggerType.SERVICE:
        return Service[EnvironmentT, ServiceKeyT](
            environment=environment,
            service_key=service_key,
            config=config,
        )


class ApplicationLoggers(BaseModel, Generic[EnvironmentT, ServiceKeyT]):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    application: Application[EnvironmentT, ServiceKeyT] = Field(
        ..., description="Application logger"
    )
    cache: Cache[EnvironmentT, ServiceKeyT] = Field(..., description="Cache logger")
    controller: Controller[EnvironmentT, ServiceKeyT] = Field(
        ..., description="Controller logger"
    )
    database: Database[EnvironmentT, ServiceKeyT] = Field(
        ..., description="Database logger"
    )
    exception: Exception[EnvironmentT, ServiceKeyT] = Field(
        ..., description="Exception logger"
    )
    middleware: Middleware[EnvironmentT, ServiceKeyT] = Field(
        ..., description="Middleware logger"
    )
    repository: Repository[EnvironmentT, ServiceKeyT] = Field(
        ..., description="Repository logger"
    )
    service: Service[EnvironmentT, ServiceKeyT] = Field(
        ..., description="Service logger"
    )

    @classmethod
    def new(
        cls,
        *,
        environment: EnvironmentT | None = None,
        service_key: ServiceKeyT | None = None,
        config: LogConfig,
    ) -> "ApplicationLoggers[EnvironmentT, ServiceKeyT]":
        return cls(
            application=create(
                LoggerType.APPLICATION,
                environment=environment,
                service_key=service_key,
                config=config,
            ),
            cache=create(
                LoggerType.CACHE,
                environment=environment,
                service_key=service_key,
                config=config,
            ),
            controller=create(
                LoggerType.CONTROLLER,
                environment=environment,
                service_key=service_key,
                config=config,
            ),
            database=create(
                LoggerType.DATABASE,
                environment=environment,
                service_key=service_key,
                config=config,
            ),
            exception=create(
                LoggerType.EXCEPTION,
                environment=environment,
                service_key=service_key,
                config=config,
            ),
            middleware=create(
                LoggerType.MIDDLEWARE,
                environment=environment,
                service_key=service_key,
                config=config,
            ),
            repository=create(
                LoggerType.REPOSITORY,
                environment=environment,
                service_key=service_key,
                config=config,
            ),
            service=create(
                LoggerType.SERVICE,
                environment=environment,
                service_key=service_key,
                config=config,
            ),
        )

from pydantic import BaseModel
from typing import Generic, TypeVar
from maleo.client.config import ClientConfigT, ClientConfigMixin
from maleo.database.config import (
    DatabaseConfigsT,
    DatabaseConfigsMixin,
)
from maleo.google.pubsub.config import PubSubConfigMixin
from maleo.google.pubsub.config.publisher import PublisherConfigT
from maleo.google.pubsub.config.subscription import SubscriptionsConfigT
from maleo.infra.config import InfraConfigMixin
from maleo.middlewares.config import MiddlewareConfigMixin


class ApplicationConfig(
    PubSubConfigMixin[PublisherConfigT, SubscriptionsConfigT],
    MiddlewareConfigMixin,
    InfraConfigMixin,
    DatabaseConfigsMixin[DatabaseConfigsT],
    ClientConfigMixin[ClientConfigT],
    BaseModel,
    Generic[ClientConfigT, DatabaseConfigsT, PublisherConfigT, SubscriptionsConfigT],
):
    pass


ApplicationConfigT = TypeVar("ApplicationConfigT", bound=ApplicationConfig)

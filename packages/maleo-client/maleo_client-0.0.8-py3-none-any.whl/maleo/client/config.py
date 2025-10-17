from pydantic import BaseModel, Field
from typing import Generic, TypeVar
from .maleo.config import MaleoClientsConfigT


class ClientConfig(BaseModel, Generic[MaleoClientsConfigT]):
    maleo: MaleoClientsConfigT = Field(
        ...,
        description="Maleo client's configurations",
    )


OptClientConfig = ClientConfig | None
ClientConfigT = TypeVar("ClientConfigT", bound=OptClientConfig)


class ClientConfigMixin(BaseModel, Generic[ClientConfigT]):
    client: ClientConfigT = Field(..., description="Client config")

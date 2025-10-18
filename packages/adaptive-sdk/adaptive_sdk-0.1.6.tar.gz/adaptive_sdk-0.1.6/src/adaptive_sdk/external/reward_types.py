from typing import Any, TypeVar, Generic
from pydantic import BaseModel as PydanticBaseModel, model_validator, ConfigDict


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(extra="forbid")


MetadataType = TypeVar("MetadataType", bound=BaseModel)


class Turn(BaseModel):
    """@public"""

    role: str
    content: str


class Request(BaseModel):
    """@public"""

    turns: list[Turn]
    metadata: dict[str, Any] | None = None
    id: int | None = None


class BatchedRequest(BaseModel):
    """@public"""

    requests: list[Request]


class ValidatedRequest(BaseModel, Generic[MetadataType]):
    """@public"""

    turns: list[Turn]
    metadata: MetadataType
    id: int | None = None

    @model_validator(mode="before")
    @classmethod
    def intercept_none_metadata(cls, data: Any) -> Any:
        # we need an empty dict to map to an empty pydantic base model in the server
        if "metadata" in data and data["metadata"] is None:
            data["metadata"] = {}
        return data


class ValidatedBatchedRequest(BaseModel, Generic[MetadataType]):
    """@public"""

    requests: list[ValidatedRequest[MetadataType]]


class Response(BaseModel):
    """@public"""

    reward: float
    metadata: dict[str, Any]
    id: int | None = None


class BatchedResponse(BaseModel):
    """@public"""

    responses: list[Response]


class MetadataValidationResponse(BaseModel):
    """@public"""

    is_valid: bool
    error_message: str | None = None


class BatchedMetadataValidationResponse(BaseModel):
    """@public"""

    responses: list[MetadataValidationResponse]


class ServerInfo(BaseModel):
    """@public"""

    version: str
    name: str
    description: str

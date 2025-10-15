"""Common response schemas for API endpoints."""

from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, RootModel, Field

__all__ = (
    "ResponseBase",
    "SuccessResponse",
    "FailedResponse",
    "BoolResponse",
    "StrResponse",
    "UUIDResponse",
    "ListResponse",
    "ListOfDictResponse",
    "DictResponse",
)


T = TypeVar("T")


class ResponseBase(BaseModel):
    """Base structure returned by every API endpoint."""

    success: bool = Field(
        ...,
        description="Indicates whether the request was processed successfully."
    )


class SuccessResponse(ResponseBase, Generic[T]):
    """Successful API response wrapper."""

    success: bool = Field(
        default=True,
        description="Always true for successful responses."
    )
    data: Any = Field(
        ...,
        description="Payload returned by the API. The content depends on the specific endpoint."
    )


class FailedResponse(ResponseBase):
    """Error response wrapper."""

    success: bool = Field(
        default=False,
        description="Always false for failed responses."
    )
    message: str = Field(
        ...,
        description="Error message explaining why the request failed."
    )


class BoolResponse(RootModel[bool]):
    pass


class StrResponse(RootModel[str]):
    pass


class UUIDResponse(RootModel[UUID]):
    pass


class ListResponse(RootModel[list]):
    pass


class ListOfDictResponse(RootModel[list[dict[str, Any]]]):
    pass


class DictResponse(RootModel[dict[str, Any]]):
    pass

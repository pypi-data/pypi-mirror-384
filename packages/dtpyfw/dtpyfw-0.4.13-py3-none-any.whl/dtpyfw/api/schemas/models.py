from datetime import date, datetime
from typing import List

from pydantic import BaseModel, ConfigDict, field_validator, Field

from ...core.enums import OrderingType

__all__ = (
    "Sorting",
    "SearchPayload",
    "NumberRange",
    "TimeRange",
    "DateRange",
    "BaseModelEnumValue",
    "ListPayloadResponse",
)


class Sorting(BaseModel):
    """Sorting configuration for query results."""

    sort_by: str = Field(
        ...,
        description="The field name to sort results by."
    )
    order_by: OrderingType = Field(
        default=OrderingType.asc,
        description="Sorting direction: ascending or descending."
    )


class SearchPayload(BaseModel):
    """Common request payload for paginated and searchable list endpoints."""

    page: int | None = Field(
        default=1,
        description="Page number to retrieve (must be >= 1)."
    )
    items_per_page: int | None = Field(
        default=20,
        description="Number of items per page (max 30)."
    )
    sorting: List[Sorting] | None = Field(
        default=None,
        description="Optional list of sorting rules applied to the query."
    )
    search: str | None = Field(
        default="",
        description="Optional search term to filter results."
    )

    # Page number must be greater than or equal to one
    @field_validator("page")
    def validate_page(cls, page):
        if page is not None and page < 1:
            raise ValueError("page number must be greater than one")
        return page

    # Make limitation for items per page
    @field_validator("items_per_page")
    def validate_items_per_page(cls, items_per_page):
        if items_per_page is not None and items_per_page > 30:
            raise ValueError("Item per page should be lower than or equal to 30.")
        return items_per_page

    class Config:
        use_enum_values = True


class NumberRange(BaseModel):
    """Range filter for numeric values."""

    min: int | None = Field(
        default=None,
        description="Minimum value allowed in the range."
    )
    max: int | None = Field(
        default=None,
        description="Maximum value allowed in the range."
    )


class TimeRange(BaseModel):
    """Range filter for time values."""

    min: datetime | None = Field(
        default=None,
        description="Minimum datetime allowed in the range."
    )
    max: datetime | None = Field(
        default=None,
        description="Maximum datetime allowed in the range."
    )


class DateRange(BaseModel):
    """Range filter for date values."""

    min: date | None = Field(
        default=None,
        description="Minimum date allowed in the range."
    )
    max: date | None = Field(
        default=None,
        description="Maximum date allowed in the range."
    )


class BaseModelEnumValue(BaseModel):
    """Base model configured to serialize enums as their values."""

    model_config = ConfigDict(use_enum_values=True)


class ListPayloadResponse(BaseModel):
    """Standard response structure for paginated list endpoints."""

    total_row: int | None = Field(
        default=None,
        description="Total number of rows matching the query."
    )
    last_page: int | None = Field(
        default=None,
        description="The index of the last available page."
    )
    has_next: bool | None = Field(
        default=None,
        description="Indicates if there is a next page available."
    )

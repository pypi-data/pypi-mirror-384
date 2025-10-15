from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Annotated, Union, Literal

from pydantic import RootModel, BaseModel, Field, ConfigDict


class AvailableFilterType(Enum):
    select = "select"
    number = "number"
    date = "date"


class RowsList(RootModel[List[Dict]]):
    pass


class AvailableFilterSelectItem(BaseModel):
    label: str
    value: Any


class AvailableFilterSelect(BaseModel):
    label: str
    name: str
    type: Literal[AvailableFilterType.select]
    value: list[AvailableFilterSelectItem]


class AvailableFilterNumberItem(BaseModel):
    min: int
    max: int


class AvailableFilterNumber(BaseModel):
    label: str
    name: str
    type: Literal[AvailableFilterType.number]
    value: AvailableFilterNumberItem


class AvailableFilterDateItem(BaseModel):
    min: datetime
    max: datetime


class AvailableFilterDate(BaseModel):
    label: str
    name: str
    type: Literal[AvailableFilterType.date]
    value: AvailableFilterDateItem


AvailableFilter = Annotated[
    Union[
        AvailableFilterSelect,
        AvailableFilterNumber,
        AvailableFilterDate,
    ],
    Field(discriminator='type')
]


class SearchType(Enum):
    select = "select"
    number = "number"
    date = "date"
    search = "search"


class SelectedFilterSelect(BaseModel):
    label: str
    name: str
    type: Literal[SearchType.select]
    value: str | Enum


class SelectedFilterNumberItem(BaseModel):
    min: int
    max: int


class SelectedFilterNumber(BaseModel):
    label: str
    name: str
    type: Literal[SearchType.number]
    value: SelectedFilterNumberItem


class SelectedFilterDateItem(BaseModel):
    min: datetime
    max: datetime


class SelectedFilterDate(BaseModel):
    label: str
    name: str
    type: Literal[SearchType.date]
    value: SelectedFilterDateItem


class SelectedFilterSearch(BaseModel):
    label: str
    name: str
    type: Literal[SearchType.search]
    value: str


SelectedFilter = Annotated[
    Union[
        SelectedFilterSelect,
        SelectedFilterNumber,
        SelectedFilterDate,
        SelectedFilterSearch,
    ],
    Field(discriminator='type')
]


class PayloadSorting(BaseModel):
    order_by: str | Enum
    sort_by: str | Enum


class Payload(BaseModel):
    search: str = None
    sorting: list[PayloadSorting]
    page: int = 1
    items_per_page: int = 30
    total_row: int
    last_page: int
    has_next: bool

    model_config = ConfigDict(extra='allow')


class SearchResult(BaseModel):
    payload: Payload
    available_filters: List[AvailableFilter] | None = None
    selected_filters: List[SelectedFilter] | None = None
    rows_data: RowsList | None = None

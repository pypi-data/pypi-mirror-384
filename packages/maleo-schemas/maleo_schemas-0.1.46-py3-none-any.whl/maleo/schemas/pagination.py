from enum import IntEnum
from pydantic import BaseModel, Field, model_validator
from typing import Annotated, Generic, Self, TypeVar
from maleo.types.integer import ListOfInts, OptInt


class Limit(IntEnum):
    LIM_10 = 10
    LIM_20 = 20
    LIM_50 = 50
    LIM_100 = 100

    @classmethod
    def choices(cls) -> ListOfInts:
        return [e.value for e in cls]


class Page(BaseModel):
    page: Annotated[int, Field(1, ge=1, description="Page number, must be >= 1")] = 1


class FlexibleLimit(BaseModel):
    limit: Annotated[
        OptInt, Field(None, description="Page limit. (Optional)", ge=1)
    ] = None


class StrictLimit(BaseModel):
    limit: Limit = Field(Limit.LIM_10, description="Page limit")


class PageInfo(BaseModel):
    data_count: Annotated[int, Field(..., description="Fetched data count", ge=0)] = 0
    total_data: Annotated[int, Field(..., description="Total data count", ge=0)] = 0
    total_pages: Annotated[int, Field(..., description="Total pages count", ge=1)] = 1


class BaseFlexiblePagination(FlexibleLimit, Page):
    @model_validator(mode="after")
    def validate_page_and_limit(self) -> Self:
        if self.limit is None:
            self.page = 1
        return self


class FlexiblePagination(PageInfo, BaseFlexiblePagination):
    pass


class BaseStrictPagination(StrictLimit, Page):
    pass


class StrictPagination(PageInfo, BaseStrictPagination):
    pass


AnyPagination = FlexiblePagination | StrictPagination
PaginationT = TypeVar("PaginationT", bound=AnyPagination)
OptAnyPagination = AnyPagination | None
OptPaginationT = TypeVar("OptPaginationT", bound=OptAnyPagination)


class PaginationMixin(BaseModel, Generic[OptPaginationT]):
    pagination: OptPaginationT = Field(..., description="Pagination")

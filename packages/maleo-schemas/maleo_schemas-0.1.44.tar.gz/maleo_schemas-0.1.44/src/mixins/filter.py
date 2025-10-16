import re
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Annotated, Self, TypeGuard, overload
from maleo.types.datetime import OptDatetime
from maleo.types.string import ListOfStrs
from .identity import Name
from .timestamp import FromTimestamp, ToTimestamp


DATE_FILTER_REGEX = (
    r"^(?P<name>[a-z_]+)"
    r"(?:\|from::(?P<from>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})))?"
    r"(?:\|to::(?P<to>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})))?$"
)
DATE_FILTER_PATTERN = re.compile(DATE_FILTER_REGEX)


class DateFilter(
    ToTimestamp[OptDatetime],
    FromTimestamp[OptDatetime],
    Name[str],
):
    name: Annotated[str, Field(..., description="Name", min_length=1)]
    from_date: Annotated[OptDatetime, Field(None, description="From date")] = None
    to_date: Annotated[OptDatetime, Field(None, description="To date")] = None

    def _validate_timestamps(self):
        if self.from_date is None and self.to_date is None:
            raise ValueError("Either 'from_date' or 'to_date' must have value")
        if self.from_date is not None and self.to_date is not None:
            if self.to_date < self.from_date:
                raise ValueError("Attribute 'from_date' can not be more than 'to_date'")

    @model_validator(mode="after")
    def validate_timestamps(self) -> Self:
        self._validate_timestamps()
        return self

    @classmethod
    def from_string(cls, filter: str) -> "DateFilter":
        match = DATE_FILTER_PATTERN.match(filter)
        if not match:
            raise ValueError(f"Invalid date filter format: {filter!r}")

        name = match.group("name")
        from_raw = match.group("from")
        to_raw = match.group("to")

        from_date = datetime.fromisoformat(from_raw) if from_raw else None
        to_date = datetime.fromisoformat(to_raw) if to_raw else None

        if from_date is None and to_date is None:
            raise ValueError("Either 'from_date' or 'to_date' must be provided")

        return cls(name=name, from_date=from_date, to_date=to_date)

    def to_string(self) -> str:
        self._validate_timestamps()
        filter_string = self.name
        if self.from_date:
            filter_string += f"|from::{self.from_date.isoformat()}"
        if self.to_date:
            filter_string += f"|to::{self.to_date.isoformat()}"
        return filter_string


OptDateFilter = DateFilter | None
ListOfDateFilters = list[DateFilter]
OptListOfDateFilters = OptDateFilter | None


AnyFilters = ListOfDateFilters | ListOfStrs


def is_date_filters(
    filters: AnyFilters,
) -> TypeGuard[ListOfDateFilters]:
    return all(isinstance(filter, DateFilter) for filter in filters)


def is_filters(
    filters: AnyFilters,
) -> TypeGuard[ListOfStrs]:
    return all(isinstance(filter, str) for filter in filters)


class Filters(BaseModel):
    filters: Annotated[
        ListOfStrs,
        Field(
            list[str](),
            description="Date range filters with '<COLUMN_NAME>|from::<ISO_DATETIME>|to::<ISO_DATETIME>' format",
        ),
    ] = list[str]()

    @field_validator("filters", mode="after")
    @classmethod
    def validate_filters_pattern(cls, value: ListOfStrs) -> ListOfStrs:
        for v in value:
            match = DATE_FILTER_PATTERN.match(v)
            if not match:
                raise ValueError(f"Invalid date filter format: {v!r}")
        return value

    @classmethod
    def from_date_filters(cls, date_filters: ListOfDateFilters) -> "Filters":
        return cls(filters=[filter.to_string() for filter in date_filters])

    @property
    def date_filters(self) -> ListOfDateFilters:
        return [DateFilter.from_string(filter) for filter in self.filters]


class DateFilters(BaseModel):
    date_filters: Annotated[
        ListOfDateFilters,
        Field(list[DateFilter](), description="Date filters to be applied"),
    ] = list[DateFilter]()

    @classmethod
    def from_filters(cls, filters: ListOfStrs) -> "DateFilters":
        return cls(date_filters=[DateFilter.from_string(filter) for filter in filters])

    @property
    def filters(self) -> ListOfStrs:
        return [filter.to_string() for filter in self.date_filters]


@overload
def convert(filters: ListOfDateFilters) -> ListOfStrs: ...
@overload
def convert(filters: ListOfStrs) -> ListOfDateFilters: ...
def convert(filters: AnyFilters) -> AnyFilters:
    if is_date_filters(filters):
        return [filter.to_string() for filter in filters]
    elif is_filters(filters):
        return [DateFilter.from_string(filter) for filter in filters]
    else:
        raise ValueError("Filter type is neither DateFilter nor string")

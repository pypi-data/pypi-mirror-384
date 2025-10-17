import re
from pydantic import BaseModel, Field, field_validator
from typing import Annotated, TypeGuard, overload
from maleo.enums.order import Order as OrderEnum
from maleo.types.string import ListOfStrs
from .general import Order
from .identity import Name


SORT_COLUMN_REGEX = r"^(?P<name>[a-z_]+)\.(?P<order>asc|desc)$"
SORT_COLUMN_PATTERN = re.compile(SORT_COLUMN_REGEX)


class SortColumn(
    Order[OrderEnum],
    Name[str],
):
    name: Annotated[str, Field(..., description="Name", min_length=1)]

    @classmethod
    def from_string(cls, sort: str) -> "SortColumn":
        match = SORT_COLUMN_PATTERN.match(sort)
        if not match:
            raise ValueError(f"Invalid sort format: {sort!r}")

        name = match.group("name")
        order_raw = match.group("order")
        order = OrderEnum(order_raw)

        return cls(name=name, order=order)

    def to_string(self) -> str:
        return f"{self.name}.{self.order}"


OptSortColumn = SortColumn | None
ListOfSortColumns = list[SortColumn]
OptListOfSortColumns = ListOfSortColumns | None


AnySorts = ListOfSortColumns | ListOfStrs


def is_sort_columns(
    sorts: AnySorts,
) -> TypeGuard[ListOfSortColumns]:
    return all(isinstance(sort, SortColumn) for sort in sorts)


def is_sorts(
    sorts: AnySorts,
) -> TypeGuard[ListOfStrs]:
    return all(isinstance(sort, str) for sort in sorts)


class Sorts(BaseModel):
    sorts: Annotated[
        ListOfStrs,
        Field(
            ["id.asc"],
            description="Column sorts with '<COLUMN_NAME>.<ASC|DESC>' format",
        ),
    ] = ["id.asc"]

    @field_validator("sorts", mode="after")
    @classmethod
    def validate_sorts_pattern(cls, value: ListOfStrs) -> ListOfStrs:
        for v in value:
            match = SORT_COLUMN_PATTERN.match(v)
            if not match:
                raise ValueError(f"Invalid sort column format: {v!r}")
        return value

    @classmethod
    def from_sort_columns(cls, sort_columns: ListOfSortColumns) -> "Sorts":
        return cls(sorts=[sort.to_string() for sort in sort_columns])

    @property
    def sort_columns(self) -> ListOfSortColumns:
        return [SortColumn.from_string(sort) for sort in self.sorts]


class SortColumns(BaseModel):
    sort_columns: Annotated[
        ListOfSortColumns,
        Field(
            [SortColumn(name="id", order=OrderEnum.ASC)],
            description="List of columns to be sorted",
        ),
    ] = [SortColumn(name="id", order=OrderEnum.ASC)]

    @classmethod
    def from_sorts(cls, sorts: ListOfStrs) -> "SortColumns":
        return cls(sort_columns=[SortColumn.from_string(sort) for sort in sorts])

    @property
    def sorts(self) -> ListOfStrs:
        return [sort.to_string() for sort in self.sort_columns]


@overload
def convert(sorts: ListOfSortColumns) -> ListOfStrs: ...
@overload
def convert(sorts: ListOfStrs) -> ListOfSortColumns: ...
def convert(sorts: AnySorts) -> AnySorts:
    if is_sort_columns(sorts):
        return [sort.to_string() for sort in sorts]
    elif is_sorts(sorts):
        return [SortColumn.from_string(sort) for sort in sorts]
    else:
        raise ValueError("Sort type is neither SortColumn nor string")

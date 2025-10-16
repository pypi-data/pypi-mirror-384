from enum import StrEnum
from pydantic import BaseModel, Field
from typing import Annotated, Generic, Literal, TypeVar, overload
from maleo.types.dict import OptStrToAnyDict
from maleo.types.string import ListOfStrs


class AggregateField(StrEnum):
    KEY = "key"
    NAME = "name"
    SLUG = "slug"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


class ResourceIdentifier(BaseModel):
    key: Annotated[str, Field(..., description="Key", pattern=r"^[a-zA-Z0-9_-]+$")]
    name: Annotated[str, Field(..., description="Name")]
    slug: Annotated[
        str, Field(..., description="URL Slug", pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    ]


class Resource(BaseModel):
    identifiers: Annotated[
        list[ResourceIdentifier], Field(..., min_length=1, description="Identifiers")
    ]
    details: Annotated[OptStrToAnyDict, Field(None, description="Details")] = None

    @overload
    def aggregate(
        self, field: Literal[AggregateField.KEY], *, sep: str = "_"
    ) -> str: ...
    @overload
    def aggregate(
        self, field: Literal[AggregateField.NAME], *, sep: str = " "
    ) -> str: ...
    @overload
    def aggregate(
        self, field: Literal[AggregateField.SLUG], *, sep: str = "/"
    ) -> str: ...
    @overload
    def aggregate(
        self, field: AggregateField = AggregateField.KEY, *, sep: str = "_"
    ) -> str: ...
    def aggregate(
        self, field: AggregateField = AggregateField.KEY, *, sep: str = "_"
    ) -> str:
        if field is AggregateField.KEY:
            return sep.join([id.key for id in self.identifiers])
        elif field is AggregateField.NAME:
            return sep.join([id.name for id in self.identifiers])
        elif field is AggregateField.SLUG:
            return sep.join([id.slug for id in self.identifiers])


OptResource = Resource | None
OptResourceT = TypeVar("OptResourceT", bound=OptResource)


class ResourceMixin(BaseModel, Generic[OptResourceT]):
    resource: OptResourceT = Field(..., description="Resource")

from pydantic import BaseModel, Field
from typing import Generic, TypeVar
from .mixins.general import Success, Descriptor, Other


AnyMetadataT = TypeVar("AnyMetadataT")
ModelMetadataT = TypeVar("ModelMetadataT", bound=BaseModel | None)


class MetadataMixin(BaseModel, Generic[AnyMetadataT]):
    metadata: AnyMetadataT = Field(..., description="Metadata")


class FieldExpansionMetadata(Other, Descriptor[str], Success[bool]):
    pass


class FieldExpansionMetadataMixin(BaseModel):
    field_expansion: str | dict[str, FieldExpansionMetadata] | None = Field(
        None, description="Field expansion metadata"
    )

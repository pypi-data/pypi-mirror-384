from pydantic import BaseModel, Field
from typing import Generic, TypeVar
from .data import DataPair, AnyDataT, DataMixin, ModelDataT
from .metadata import MetadataMixin, AnyMetadataT, ModelMetadataT
from .mixins.general import Other
from .pagination import OptPaginationT, PaginationT, PaginationMixin


class Payload(
    Other,
    MetadataMixin[AnyMetadataT],
    PaginationMixin[OptPaginationT],
    DataMixin[AnyDataT],
    BaseModel,
    Generic[AnyDataT, OptPaginationT, AnyMetadataT],
):
    pass


PayloadT = TypeVar("PayloadT", bound=Payload)


class PayloadMixin(BaseModel, Generic[PayloadT]):
    payload: PayloadT = Field(..., description="Payload")


class NoDataPayload(
    Payload[None, None, ModelMetadataT],
    Generic[ModelMetadataT],
):
    data: None = None
    pagination: None = None


class SingleDataPayload(
    Payload[ModelDataT, None, ModelMetadataT],
    Generic[ModelDataT, ModelMetadataT],
):
    pagination: None = None


class CreateSingleDataPayload(
    Payload[DataPair[None, ModelDataT], None, ModelMetadataT],
    Generic[ModelDataT, ModelMetadataT],
):
    pass


class ReadSingleDataPayload(
    Payload[DataPair[ModelDataT, None], None, ModelMetadataT],
    Generic[ModelDataT, ModelMetadataT],
):
    pass


class UpdateSingleDataPayload(
    Payload[DataPair[ModelDataT, ModelDataT], None, ModelMetadataT],
    Generic[ModelDataT, ModelMetadataT],
):
    pass


class DeleteSingleDataPayload(
    Payload[DataPair[ModelDataT, None], None, ModelMetadataT],
    Generic[ModelDataT, ModelMetadataT],
):
    pass


class OptSingleDataPayload(
    Payload[ModelDataT | None, None, ModelMetadataT],
    Generic[ModelDataT, ModelMetadataT],
):
    pagination: None = None


class MultipleDataPayload(
    Payload[list[ModelDataT], PaginationT, ModelMetadataT],
    Generic[ModelDataT, PaginationT, ModelMetadataT],
):
    pass


class CreateMultipleDataPayload(
    Payload[DataPair[None, list[ModelDataT]], PaginationT, ModelMetadataT],
    Generic[ModelDataT, PaginationT, ModelMetadataT],
):
    pass


class ReadMultipleDataPayload(
    Payload[DataPair[list[ModelDataT], None], PaginationT, ModelMetadataT],
    Generic[ModelDataT, PaginationT, ModelMetadataT],
):
    pass


class UpdateMultipleDataPayload(
    Payload[DataPair[list[ModelDataT], list[ModelDataT]], PaginationT, ModelMetadataT],
    Generic[ModelDataT, PaginationT, ModelMetadataT],
):
    pass


class DeleteMultipleDataPayload(
    Payload[DataPair[list[ModelDataT], None], PaginationT, ModelMetadataT],
    Generic[ModelDataT, PaginationT, ModelMetadataT],
):
    pass


class OptMultipleDataPayload(
    Payload[list[ModelDataT] | None, PaginationT, ModelMetadataT],
    Generic[ModelDataT, PaginationT, ModelMetadataT],
):
    pass

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Generic, TypeVar
from maleo.types.datetime import OptDatetime, OptDatetimeT
from maleo.types.float import OptFloatT


class FromTimestamp(BaseModel, Generic[OptDatetimeT]):
    from_date: OptDatetimeT = Field(..., description="From date")


class ToTimestamp(BaseModel, Generic[OptDatetimeT]):
    to_date: OptDatetimeT = Field(..., description="To date")


class ExecutionTimestamp(BaseModel, Generic[OptDatetimeT]):
    executed_at: OptDatetimeT = Field(..., description="executed_at timestamp")


class CompletionTimestamp(BaseModel, Generic[OptDatetimeT]):
    completed_at: OptDatetimeT = Field(..., description="completed_at timestamp")


class CreationTimestamp(BaseModel):
    created_at: datetime = Field(..., description="created_at timestamp")


class UpdateTimestamp(BaseModel):
    updated_at: datetime = Field(..., description="updated_at timestamp")


class LifecycleTimestamp(
    UpdateTimestamp,
    CreationTimestamp,
):
    pass


class DeletionTimestamp(BaseModel, Generic[OptDatetimeT]):
    deleted_at: OptDatetimeT = Field(..., description="deleted_at timestamp")


class RestorationTimestamp(BaseModel, Generic[OptDatetimeT]):
    restored_at: OptDatetimeT = Field(..., description="restored_at timestamp")


class DeactivationTimestamp(BaseModel, Generic[OptDatetimeT]):
    deactivated_at: OptDatetimeT = Field(..., description="deactivated_at timestamp")


class ActivationTimestamp(BaseModel, Generic[OptDatetimeT]):
    activated_at: OptDatetimeT = Field(..., description="activated_at timestamp")


DeletionTimestampT = TypeVar("DeletionTimestampT", bound=OptDatetime)
RestorationTimestampT = TypeVar("RestorationTimestampT", bound=OptDatetime)
DeactivationTimestampT = TypeVar("DeactivationTimestampT", bound=OptDatetime)
ActivationTimestampT = TypeVar("ActivationTimestampT", bound=OptDatetime)


class StatusTimestamp(
    ActivationTimestamp[ActivationTimestampT],
    DeactivationTimestamp[DeactivationTimestampT],
    RestorationTimestamp[RestorationTimestampT],
    DeletionTimestamp[DeletionTimestampT],
    Generic[
        DeletionTimestampT,
        RestorationTimestampT,
        DeactivationTimestampT,
        ActivationTimestampT,
    ],
):
    pass


class DataStatusTimestamp(
    StatusTimestamp[
        OptDatetime,
        OptDatetime,
        OptDatetime,
        datetime,
    ],
):
    pass


class DataTimestamp(
    DataStatusTimestamp,
    LifecycleTimestamp,
):
    pass


class Duration(BaseModel, Generic[OptFloatT]):
    duration: OptFloatT = Field(..., description="Duration")


class InferenceDuration(BaseModel, Generic[OptFloatT]):
    inference_duration: OptFloatT = Field(..., description="Inference duration")

from datetime import datetime, timezone
from pydantic import BaseModel, Field, model_validator
from typing import Annotated, Self
from uuid import UUID
from ..mixins.identity import UUIDId
from ..mixins.timestamp import ExecutionTimestamp, CompletionTimestamp, Duration
from .enums import OperationType as OperationTypeEnum


class Id(UUIDId[UUID]):
    pass


class OperationType(BaseModel):
    type: Annotated[OperationTypeEnum, Field(..., description="Operation's type")]


class Timestamp(
    Duration[float],
    CompletionTimestamp[datetime],
    ExecutionTimestamp[datetime],
):
    duration: Annotated[float, Field(0.0, ge=0.0, description="Duration")] = 0.0

    @model_validator(mode="after")
    def calculate_duration(self) -> Self:
        self.duration = (self.completed_at - self.executed_at).total_seconds()
        return self

    @classmethod
    def now(cls) -> "Timestamp":
        now = datetime.now(tz=timezone.utc)
        return cls(executed_at=now, completed_at=now, duration=0)

    @classmethod
    def completed_now(cls, executed_at: datetime) -> "Timestamp":
        completed_at = datetime.now(tz=timezone.utc)
        return cls(
            executed_at=executed_at,
            completed_at=completed_at,
            duration=(completed_at - executed_at).total_seconds(),
        )


OptTimestamp = Timestamp | None


class TimestampMixin(BaseModel):
    timestamp: Annotated[Timestamp, Field(..., description="Operation's timestamp")]


class Summary(BaseModel):
    summary: Annotated[str, Field(..., description="Operation's summary")]

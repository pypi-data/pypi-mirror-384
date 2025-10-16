from pydantic import BaseModel, Field
from typing import Generic, TypeVar


OldDataT = TypeVar("OldDataT")
NewDataT = TypeVar("NewDataT")


class DataPair(BaseModel, Generic[OldDataT, NewDataT]):
    old: OldDataT = Field(..., description="Old data")
    new: NewDataT = Field(..., description="New data")


AnyDataT = TypeVar("AnyDataT")


class DataMixin(BaseModel, Generic[AnyDataT]):
    data: AnyDataT = Field(..., description="Data")


ModelDataT = TypeVar("ModelDataT", bound=BaseModel)

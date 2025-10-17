from pydantic import BaseModel, Field
from typing import Annotated, Any, Generic
from maleo.types.boolean import BoolT, OptBoolT
from maleo.types.enum import OptStrEnumT
from maleo.types.misc import (
    OptFloatOrIntT,
    OptIntOrStrEnumT,
    OptStrOrStrEnumT,
    OptListOfStrsOrStrEnumsT,
)
from maleo.types.string import OptStrT


class StatusCode(BaseModel):
    status_code: Annotated[int, Field(..., description="Status code", ge=100, le=600)]


class Success(BaseModel, Generic[BoolT]):
    success: BoolT = Field(..., description="Success")


class Code(BaseModel, Generic[OptStrOrStrEnumT]):
    code: OptStrOrStrEnumT = Field(..., description="Code")


class Codes(BaseModel, Generic[OptListOfStrsOrStrEnumsT]):
    codes: OptListOfStrsOrStrEnumsT = Field(..., description="Codes")


class Message(BaseModel):
    message: str = Field(..., description="Message")


class Description(BaseModel):
    description: str = Field(..., description="Description")


class Descriptor(
    Description, Message, Code[OptStrOrStrEnumT], Generic[OptStrOrStrEnumT]
):
    pass


class Order(BaseModel, Generic[OptIntOrStrEnumT]):
    order: OptIntOrStrEnumT = Field(..., description="Order")


class Level(BaseModel, Generic[OptStrEnumT]):
    level: OptStrEnumT = Field(..., description="Level")


class Note(BaseModel, Generic[OptStrT]):
    note: OptStrT = Field(..., description="Note")


class IsDefault(BaseModel, Generic[OptBoolT]):
    is_default: OptBoolT = Field(..., description="Whether is default")


class Other(BaseModel):
    other: Annotated[Any, Field(None, description="Other")] = None


class Age(BaseModel, Generic[OptFloatOrIntT]):
    age: OptFloatOrIntT = Field(..., ge=0, description="Age")

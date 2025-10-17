from pydantic import BaseModel, Field
from typing import Annotated, Generic
from maleo.types.dict import OptStrToAnyDict
from maleo.types.enum import StrEnumT


class BaseOperationAction(BaseModel, Generic[StrEnumT]):
    type: Annotated[StrEnumT, Field(..., description="Action's type")]


class SimpleOperationAction(BaseOperationAction[StrEnumT], Generic[StrEnumT]):
    details: Annotated[OptStrToAnyDict, Field(None, description="Action's details")] = (
        None
    )

from pydantic import BaseModel, Field
from typing import Generic
from maleo.types.boolean import OptBoolT


class IsRoot(BaseModel, Generic[OptBoolT]):
    is_root: OptBoolT = Field(..., description="Whether is root")


class IsParent(BaseModel, Generic[OptBoolT]):
    is_parent: OptBoolT = Field(..., description="Whether is parent")


class IsChild(BaseModel, Generic[OptBoolT]):
    is_child: OptBoolT = Field(..., description="Whether is child")


class IsLeaf(BaseModel, Generic[OptBoolT]):
    is_leaf: OptBoolT = Field(..., description="Whether is leaf")

from pydantic import BaseModel, Field
from typing import Annotated, Generic, TypeVar


ActionT = TypeVar("ActionT", bound=BaseModel)


class ActionMixin(BaseModel, Generic[ActionT]):
    action: Annotated[ActionT, Field(..., description="Action")]

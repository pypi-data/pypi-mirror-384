from enum import StrEnum
from pydantic import BaseModel, Field
from typing import Generic, TypeVar
from maleo.types.string import ListOfStrs


class Domain(StrEnum):
    TENANT = "tenant"
    SYSTEM = "system"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


DomainT = TypeVar("DomainT", bound=Domain)
OptDomain = Domain | None
OptDomainT = TypeVar("OptDomainT", bound=OptDomain)


class DomainMixin(BaseModel, Generic[OptDomainT]):
    domain: OptDomainT = Field(..., description="Domain")


class RolePrefix(StrEnum):
    MEDICAL = "medical"
    TENANT = "tenant"
    SYSTEM = "system"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]

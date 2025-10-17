from enum import StrEnum
from fastapi import Header
from fastapi.requests import HTTPConnection, Request
from fastapi.websockets import WebSocket
from pydantic import BaseModel, Field
from typing import (
    Annotated,
    Callable,
    Generic,
    Literal,
    TypeVar,
    overload,
)
from uuid import UUID
from maleo.enums.connection import Header as HeaderEnum, Protocol, OptProtocol
from maleo.types.string import ListOfStrs
from maleo.types.uuid import OptUUID


class Source(StrEnum):
    HEADER = "header"
    STATE = "state"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


class Impersonation(BaseModel):
    user_id: Annotated[UUID, Field(..., description="User's ID")]
    organization_id: Annotated[
        OptUUID, Field(None, description="Organization's ID")
    ] = None

    @classmethod
    def extract(cls, conn: HTTPConnection) -> "Impersonation | None":
        impersonation = getattr(conn.state, "impersonation", None)
        if isinstance(impersonation, Impersonation):
            return impersonation

        user_id = conn.headers.get(HeaderEnum.X_USER_ID, None)
        if user_id is not None:
            user_id = UUID(user_id)

        organization_id = conn.headers.get(HeaderEnum.X_ORGANIZATION_ID, None)
        if organization_id is not None:
            organization_id = UUID(organization_id)

        if user_id is not None:
            return cls(
                user_id=user_id,
                organization_id=organization_id,
            )

        return None

    @overload
    @classmethod
    def as_dependency(
        cls,
        protocol: None = None,
        /,
    ) -> Callable[[HTTPConnection, OptUUID, OptUUID], "Impersonation | None"]: ...
    @overload
    @classmethod
    def as_dependency(
        cls,
        protocol: Literal[Protocol.HTTP],
        /,
    ) -> Callable[[Request, OptUUID, OptUUID], "Impersonation | None"]: ...
    @overload
    @classmethod
    def as_dependency(
        cls,
        protocol: Literal[Protocol.WEBSOCKET],
        /,
    ) -> Callable[[WebSocket], "Impersonation | None"]: ...
    @classmethod
    def as_dependency(
        cls,
        protocol: OptProtocol = None,
        /,
    ) -> (
        Callable[[HTTPConnection, OptUUID, OptUUID], "Impersonation | None"]
        | Callable[[Request, OptUUID, OptUUID], "Impersonation | None"]
        | Callable[[WebSocket], "Impersonation | None"]
    ):
        def _dependency(
            conn: HTTPConnection,
            # These are for documentation purpose only
            user_id: OptUUID = Header(
                None,
                alias=HeaderEnum.X_USER_ID.value,
                description="User's ID",
            ),
            organization_id: OptUUID = Header(
                None,
                alias=HeaderEnum.X_ORGANIZATION_ID.value,
                description="Organization's ID",
            ),
        ) -> "Impersonation | None":
            return cls.extract(conn)

        def _request_dependency(
            request: Request,
            # These are for documentation purpose only
            user_id: OptUUID = Header(
                None,
                alias=HeaderEnum.X_USER_ID.value,
                description="User's ID",
            ),
            organization_id: OptUUID = Header(
                None,
                alias=HeaderEnum.X_ORGANIZATION_ID.value,
                description="Organization's ID",
            ),
        ) -> "Impersonation | None":
            return cls.extract(request)

        def _websocket_dependency(websocket: WebSocket) -> "Impersonation | None":
            return cls.extract(websocket)

        if protocol is None:
            return _dependency
        elif protocol is Protocol.HTTP:
            return _request_dependency
        elif protocol is Protocol.WEBSOCKET:
            return _websocket_dependency


OptImpersonation = Impersonation | None
OptImpersonationT = TypeVar("OptImpersonationT", bound=OptImpersonation)


class ImpersonationMixin(BaseModel, Generic[OptImpersonationT]):
    impersonation: OptImpersonationT = Field(..., description="Impersonation")

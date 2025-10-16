from datetime import datetime, timezone
from pydantic import BaseModel, Field
from starlette.requests import HTTPConnection
from typing import Annotated, Callable, Generic, TypeVar
from uuid import UUID, uuid4
from maleo.enums.connection import Scheme, Header
from maleo.types.boolean import OptBool
from maleo.types.dict import OptStrToStrDict
from maleo.types.string import OptStr, OptListOfDoubleStrs
from .user_agent import UserAgent, OptUserAgent


class ConnectionContext(BaseModel):
    id: Annotated[UUID, Field(uuid4(), description="Connection's ID")] = uuid4()

    executed_at: Annotated[
        datetime,
        Field(datetime.now(tz=timezone.utc), description="Executed At Timestamp"),
    ] = datetime.now(tz=timezone.utc)

    scheme: Annotated[Scheme, Field(..., description="Connection's scheme (http/ws)")]

    method: Annotated[
        OptStr, Field(None, description="HTTP method (None for WebSocket)")
    ] = None

    url: Annotated[str, Field(..., description="Connection URL")]
    ip_address: Annotated[str, Field("unknown", description="Client's IP address")] = (
        "unknown"
    )
    is_internal: Annotated[
        OptBool, Field(None, description="True if IP is internal")
    ] = None

    headers: Annotated[
        OptListOfDoubleStrs, Field(None, description="Connection's headers")
    ] = None

    path_params: Annotated[
        OptStrToStrDict, Field(None, description="Path parameters")
    ] = None

    query_params: Annotated[OptStr, Field(None, description="Query parameters")] = None

    user_agent: Annotated[OptUserAgent, Field(None, description="User agent")] = None

    referer: Annotated[OptStr, Field(None, description="Referrer URL")] = None

    origin: Annotated[OptStr, Field(None, description="Origin header")] = None

    host: Annotated[OptStr, Field(None, description="Host header")] = None

    forwarded_proto: Annotated[
        OptStr, Field(None, description="Forwarded protocol")
    ] = None

    language: Annotated[OptStr, Field(None, description="Accepted languages")] = None

    @classmethod
    def extract_client_ip(cls, conn: HTTPConnection) -> str:
        x_forwarded_for = conn.headers.get(Header.X_FORWARDED_FOR)
        if x_forwarded_for:
            ips = [ip.strip() for ip in x_forwarded_for.split(",")]
            return ips[0]

        x_real_ip = conn.headers.get(Header.X_REAL_IP)
        if x_real_ip:
            return x_real_ip

        return conn.client.host if conn.client else "unknown"

    @classmethod
    def from_connection(cls, conn: HTTPConnection) -> "ConnectionContext":
        id = getattr(conn.state, "connection_id", None)
        if not id or not isinstance(id, UUID):
            id = uuid4()
            conn.state.connection_id = id

        executed_at = getattr(conn.state, "executed_at", None)
        if not executed_at or not isinstance(executed_at, datetime):
            executed_at = datetime.now(tz=timezone.utc)
            conn.state.executed_at = executed_at

        ip_address = cls.extract_client_ip(conn)

        ua_string = conn.headers.get(Header.USER_AGENT, "")
        user_agent = (
            UserAgent.from_string(user_agent_string=ua_string) if ua_string else None
        )

        return cls(
            id=id,
            executed_at=executed_at,
            scheme=Scheme(conn.url.scheme),
            method=getattr(conn, "method", None),  # WebSocket doesn’t have method
            url=str(conn.url),
            ip_address=ip_address,
            is_internal=(
                None
                if ip_address == "unknown"
                else (
                    ip_address.startswith("10.")
                    or ip_address.startswith("192.168.")
                    or ip_address.startswith("172.")
                    or ip_address.startswith("127.")
                )
            ),
            headers=conn.headers.items(),
            path_params=conn.path_params,
            query_params=(None if not conn.query_params else str(conn.query_params)),
            user_agent=user_agent,
            referer=conn.headers.get(Header.REFERER),
            origin=conn.headers.get(Header.ORIGIN),
            host=conn.headers.get(Header.HOST),
            forwarded_proto=conn.headers.get(Header.X_FORWARDED_PROTO),
            language=conn.headers.get(Header.ACCEPT_LANGUAGE),
        )

    @classmethod
    def as_dependency(cls) -> Callable[[HTTPConnection], "ConnectionContext"]:
        def dependency(conn: HTTPConnection) -> "ConnectionContext":
            return cls.from_connection(conn)

        return dependency


OptConnectionContext = ConnectionContext | None
OptConnectionContextT = TypeVar("OptConnectionContextT", bound=OptConnectionContext)


class ConnectionContextMixin(BaseModel, Generic[OptConnectionContextT]):
    connection_context: OptConnectionContextT = Field(
        ..., description="Connection context"
    )

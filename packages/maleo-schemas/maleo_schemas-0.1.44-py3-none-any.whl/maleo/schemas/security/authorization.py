import httpx
from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from Crypto.PublicKey.RSA import RsaKey
from datetime import timedelta
from enum import StrEnum
from fastapi import status, HTTPException, Security
from fastapi.requests import HTTPConnection, Request
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from fastapi.websockets import WebSocket
from pydantic import BaseModel, Field
from typing import (
    Annotated,
    Callable,
    Generator,
    Generic,
    Literal,
    Self,
    TypeGuard,
    TypeVar,
    overload,
)
from maleo.enums.connection import Header, Protocol, OptProtocol
from maleo.types.misc import BytesOrStr
from maleo.types.string import ListOfStrs, OptStr
from .enums import Domain, OptDomain
from .token import TenantToken, SystemToken, AnyToken, Factory as TokenFactory


class Scheme(StrEnum):
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


SchemeT = TypeVar("SchemeT", bound=Scheme)
OptScheme = Scheme | None


class Source(StrEnum):
    HEADER = "header"
    STATE = "state"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


OptSource = Source | None


class GenericAuthorization(ABC, BaseModel, Generic[SchemeT]):
    scheme: SchemeT = Field(..., description="Authorization's scheme")
    credentials: Annotated[str, Field(..., description="Authorization's credentials")]

    @overload
    @classmethod
    def from_state(
        cls, conn: HTTPConnection, *, auto_error: Literal[False]
    ) -> Self | None: ...
    @overload
    @classmethod
    def from_state(
        cls, conn: HTTPConnection, *, auto_error: Literal[True] = True
    ) -> Self: ...
    @classmethod
    def from_state(
        cls, conn: HTTPConnection, *, auto_error: bool = True
    ) -> Self | None:
        authorization = getattr(conn.state, "authorization", None)
        if isinstance(authorization, cls):
            return authorization

        if auto_error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or unable to determine authorization in state",
            )

        return None

    @classmethod
    @abstractmethod
    def from_header(
        cls, conn: HTTPConnection, *, auto_error: bool = True
    ) -> Self | None:
        """Extract authorization from Header"""

    @overload
    @classmethod
    def extract(
        cls, conn: HTTPConnection, *, auto_error: Literal[False]
    ) -> Self | None: ...
    @overload
    @classmethod
    def extract(
        cls, conn: HTTPConnection, *, auto_error: Literal[True] = True
    ) -> Self: ...
    @classmethod
    def extract(cls, conn: HTTPConnection, *, auto_error: bool = True) -> Self | None:
        authorization = cls.from_state(conn, auto_error=auto_error)
        if isinstance(authorization, cls):
            return authorization

        authorization = cls.from_header(conn, auto_error=auto_error)
        if isinstance(authorization, cls):
            return authorization

        if auto_error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or unable to determine authorization",
            )

        return None

    @overload
    @classmethod
    def as_dependency(
        cls,
        protocol: None = None,
        *,
        auto_error: Literal[False],
    ) -> Callable[
        [HTTPConnection, HTTPAuthorizationCredentials | None, OptStr],
        Self | None,
    ]: ...
    @overload
    @classmethod
    def as_dependency(
        cls,
        protocol: None = None,
        *,
        auto_error: Literal[True] = True,
    ) -> Callable[
        [HTTPConnection, HTTPAuthorizationCredentials | None, OptStr], Self
    ]: ...
    @overload
    @classmethod
    def as_dependency(
        cls,
        protocol: Literal[Protocol.HTTP],
        *,
        auto_error: Literal[False],
    ) -> Callable[
        [Request, HTTPAuthorizationCredentials | None, OptStr],
        Self | None,
    ]: ...
    @overload
    @classmethod
    def as_dependency(
        cls,
        protocol: Literal[Protocol.HTTP],
        *,
        auto_error: Literal[True] = True,
    ) -> Callable[[Request, HTTPAuthorizationCredentials | None, OptStr], Self]: ...
    @overload
    @classmethod
    def as_dependency(
        cls, protocol: Literal[Protocol.WEBSOCKET], *, auto_error: Literal[False]
    ) -> Callable[[WebSocket], Self | None]: ...
    @overload
    @classmethod
    def as_dependency(
        cls, protocol: Literal[Protocol.WEBSOCKET], *, auto_error: Literal[True] = True
    ) -> Callable[[WebSocket], Self]: ...
    @classmethod
    def as_dependency(
        cls, protocol: OptProtocol = None, *, auto_error: bool = True
    ) -> (
        Callable[
            [HTTPConnection, HTTPAuthorizationCredentials | None, OptStr],
            Self | None,
        ]
        | Callable[
            [HTTPConnection, HTTPAuthorizationCredentials | None, OptStr],
            Self,
        ]
        | Callable[
            [Request, HTTPAuthorizationCredentials | None, OptStr],
            Self | None,
        ]
        | Callable[
            [Request, HTTPAuthorizationCredentials | None, OptStr],
            Self,
        ]
        | Callable[[WebSocket], Self | None]
        | Callable[[WebSocket], Self]
    ):
        def _dependency(
            conn: HTTPConnection,
            # These are for documentation purpose only
            bearer: Annotated[
                HTTPAuthorizationCredentials | None,
                Security(HTTPBearer(auto_error=False)),
            ],
            api_key: Annotated[
                OptStr,
                Security(APIKeyHeader(name=Header.X_API_KEY.value, auto_error=False)),
            ],
        ) -> Self | None:
            return cls.extract(conn, auto_error=auto_error)

        def _request_dependency(
            request: Request,
            # These are for documentation purpose only
            bearer: Annotated[
                HTTPAuthorizationCredentials | None,
                Security(HTTPBearer(auto_error=False)),
            ],
            api_key: Annotated[
                OptStr,
                Security(APIKeyHeader(name=Header.X_API_KEY.value, auto_error=False)),
            ],
        ) -> Self | None:
            return cls.extract(request, auto_error=auto_error)

        def _websocket_dependency(websocket: WebSocket) -> Self | None:
            return cls.extract(websocket, auto_error=auto_error)

        if protocol is None:
            return _dependency
        elif protocol is Protocol.HTTP:
            return _request_dependency
        elif protocol is Protocol.WEBSOCKET:
            return _websocket_dependency

    @overload
    def parse_token(
        self,
        domain: Literal[Domain.TENANT],
        *,
        key: BytesOrStr | RsaKey,
        audience: str | Iterable[str] | None = None,
        subject: OptStr = None,
        issuer: str | Sequence[str] | None = None,
        leeway: float | timedelta = 0,
    ) -> TenantToken: ...
    @overload
    def parse_token(
        self,
        domain: Literal[Domain.SYSTEM],
        *,
        key: BytesOrStr | RsaKey,
        audience: str | Iterable[str] | None = None,
        subject: OptStr = None,
        issuer: str | Sequence[str] | None = None,
        leeway: float | timedelta = 0,
    ) -> SystemToken: ...
    @overload
    def parse_token(
        self,
        domain: None = None,
        *,
        key: BytesOrStr | RsaKey,
        audience: str | Iterable[str] | None = None,
        subject: OptStr = None,
        issuer: str | Sequence[str] | None = None,
        leeway: float | timedelta = 0,
    ) -> AnyToken: ...
    def parse_token(
        self,
        domain: OptDomain = None,
        *,
        key: BytesOrStr | RsaKey,
        audience: str | Iterable[str] | None = None,
        subject: OptStr = None,
        issuer: str | Sequence[str] | None = None,
        leeway: float | timedelta = 0,
    ) -> AnyToken:
        if self.scheme is not Scheme.BEARER_TOKEN:
            raise ValueError(
                f"Authorization scheme must be '{Scheme.BEARER_TOKEN}' to parse token"
            )
        return TokenFactory.from_string(
            self.credentials,
            domain,
            key=key,
            audience=audience,
            subject=subject,
            issuer=issuer,
            leeway=leeway,
        )


class BaseAuthorization(GenericAuthorization[Scheme]):
    scheme: Annotated[Scheme, Field(..., description="Authorization's scheme")]

    @overload
    @classmethod
    def from_header(
        cls, conn: HTTPConnection, *, auto_error: Literal[False]
    ) -> Self | None: ...
    @overload
    @classmethod
    def from_header(
        cls, conn: HTTPConnection, *, auto_error: Literal[True] = True
    ) -> Self: ...
    @classmethod
    def from_header(
        cls, conn: HTTPConnection, *, auto_error: bool = True
    ) -> Self | None:
        token = conn.headers.get(Header.AUTHORIZATION.value, "")
        scheme, _, credentials = token.partition(" ")
        if token and scheme and credentials and scheme.lower() == "bearer":
            return cls(scheme=Scheme.BEARER_TOKEN, credentials=credentials)

        api_key = conn.headers.get(Header.X_API_KEY)
        if api_key is not None:
            return cls(scheme=Scheme.API_KEY, credentials=api_key)

        if auto_error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or unable to determine authorization from Headers",
            )

        return None


class APIKeyAuthorization(GenericAuthorization[Literal[Scheme.API_KEY]]):
    scheme: Annotated[
        Literal[Scheme.API_KEY],
        Field(Scheme.API_KEY, description="Authorization's scheme"),
    ] = Scheme.API_KEY

    @overload
    @classmethod
    def from_header(
        cls, conn: HTTPConnection, *, auto_error: Literal[False]
    ) -> Self | None: ...
    @overload
    @classmethod
    def from_header(
        cls, conn: HTTPConnection, *, auto_error: Literal[True] = True
    ) -> Self: ...
    @classmethod
    def from_header(
        cls, conn: HTTPConnection, *, auto_error: bool = True
    ) -> Self | None:
        api_key = conn.headers.get(Header.X_API_KEY)
        if api_key is not None:
            return cls(scheme=Scheme.API_KEY, credentials=api_key)

        if auto_error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid or unable to determine authorization from {Header.X_API_KEY} Header",
            )

        return None


class BearerTokenAuthorization(GenericAuthorization[Literal[Scheme.BEARER_TOKEN]]):
    scheme: Annotated[
        Literal[Scheme.BEARER_TOKEN],
        Field(Scheme.BEARER_TOKEN, description="Authorization's scheme"),
    ] = Scheme.BEARER_TOKEN

    @overload
    @classmethod
    def from_header(
        cls, conn: HTTPConnection, *, auto_error: Literal[False]
    ) -> Self | None: ...
    @overload
    @classmethod
    def from_header(
        cls, conn: HTTPConnection, *, auto_error: Literal[True] = True
    ) -> Self: ...
    @classmethod
    def from_header(
        cls, conn: HTTPConnection, *, auto_error: bool = True
    ) -> Self | None:
        token = conn.headers.get(Header.AUTHORIZATION.value, "")
        scheme, _, credentials = token.partition(" ")
        if token and scheme and credentials and scheme.lower() == "bearer":
            return cls(scheme=Scheme.BEARER_TOKEN, credentials=credentials)

        if auto_error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid or unable to determine authorization from {Header.AUTHORIZATION} Header",
            )

        return None


AnyAuthorization = BaseAuthorization | BearerTokenAuthorization | APIKeyAuthorization
AnyAuthorizationT = TypeVar("AnyAuthorizationT", bound=AnyAuthorization)
OptAnyAuthorization = AnyAuthorization | None
OptAnyAuthorizationT = TypeVar("OptAnyAuthorizationT", bound=OptAnyAuthorization)


def is_bearer_token(
    authorization: AnyAuthorization,
) -> TypeGuard[BearerTokenAuthorization]:
    return authorization.scheme is Scheme.BEARER_TOKEN


def is_api_key(authorization: AnyAuthorization) -> TypeGuard[APIKeyAuthorization]:
    return authorization.scheme is Scheme.API_KEY


class AuthorizationMixin(BaseModel, Generic[OptAnyAuthorizationT]):
    authorization: OptAnyAuthorizationT = Field(
        ...,
        description="Authorization",
    )


class APIKeyAuth(httpx.Auth):
    def __init__(self, api_key: str) -> None:
        self._auth_header = self._build_auth_header(api_key)

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        request.headers[Header.X_API_KEY.value] = self._auth_header
        yield request

    def _build_auth_header(self, api_key: str) -> str:
        return api_key


class BearerTokenAuth(httpx.Auth):
    def __init__(self, token: str) -> None:
        self._auth_header = self._build_auth_header(token)

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        request.headers[Header.AUTHORIZATION] = self._auth_header
        yield request

    def _build_auth_header(self, token: str) -> str:
        return f"Bearer {token}"


AnyHTTPXAuthorization = APIKeyAuth | BearerTokenAuth


class Factory:
    @overload
    @classmethod
    def extract(
        cls,
        scheme: None = None,
        source: OptSource = None,
        *,
        conn: HTTPConnection,
        auto_error: Literal[False],
    ) -> BaseAuthorization | None: ...
    @overload
    @classmethod
    def extract(
        cls,
        scheme: Literal[Scheme.API_KEY],
        source: OptSource = None,
        *,
        conn: HTTPConnection,
        auto_error: Literal[False],
    ) -> APIKeyAuthorization | None: ...
    @overload
    @classmethod
    def extract(
        cls,
        scheme: Literal[Scheme.BEARER_TOKEN],
        source: OptSource = None,
        *,
        conn: HTTPConnection,
        auto_error: Literal[False],
    ) -> BearerTokenAuthorization | None: ...
    @overload
    @classmethod
    def extract(
        cls,
        scheme: None = None,
        source: OptSource = None,
        *,
        conn: HTTPConnection,
        auto_error: Literal[True] = True,
    ) -> BaseAuthorization: ...
    @overload
    @classmethod
    def extract(
        cls,
        scheme: Literal[Scheme.API_KEY],
        source: OptSource = None,
        *,
        conn: HTTPConnection,
        auto_error: Literal[True] = True,
    ) -> APIKeyAuthorization: ...
    @overload
    @classmethod
    def extract(
        cls,
        scheme: Literal[Scheme.BEARER_TOKEN],
        source: OptSource = None,
        *,
        conn: HTTPConnection,
        auto_error: Literal[True] = True,
    ) -> BearerTokenAuthorization: ...
    @classmethod
    def extract(
        cls,
        scheme: OptScheme = None,
        source: OptSource = None,
        *,
        conn: HTTPConnection,
        auto_error: bool = True,
    ) -> OptAnyAuthorization:
        if scheme is None:
            if source is None:
                return BaseAuthorization.extract(conn, auto_error=auto_error)
            elif source is Source.HEADER:
                return BaseAuthorization.from_header(conn, auto_error=auto_error)
            elif source is Source.STATE:
                return BaseAuthorization.from_state(conn, auto_error=auto_error)
        elif scheme is Scheme.API_KEY:
            if source is None:
                return APIKeyAuthorization.extract(conn, auto_error=auto_error)
            elif source is Source.HEADER:
                return APIKeyAuthorization.from_header(conn, auto_error=auto_error)
            elif source is Source.STATE:
                return APIKeyAuthorization.from_state(conn, auto_error=auto_error)
        elif scheme is Scheme.BEARER_TOKEN:
            if source is None:
                return BearerTokenAuthorization.extract(conn, auto_error=auto_error)
            elif source is Source.HEADER:
                return BearerTokenAuthorization.from_header(conn, auto_error=auto_error)
            elif source is Source.STATE:
                return BearerTokenAuthorization.from_state(conn, auto_error=auto_error)

    @overload
    @classmethod
    def as_dependency(
        cls,
        protocol: None = None,
        *,
        scheme: None = None,
        auto_error: Literal[False],
    ) -> Callable[
        [HTTPConnection, HTTPAuthorizationCredentials | None, OptStr],
        BaseAuthorization | None,
    ]: ...
    @overload
    @classmethod
    def as_dependency(
        cls,
        protocol: None = None,
        *,
        scheme: Literal[Scheme.API_KEY],
        auto_error: Literal[False],
    ) -> Callable[
        [HTTPConnection, HTTPAuthorizationCredentials | None, OptStr],
        APIKeyAuthorization | None,
    ]: ...
    @overload
    @classmethod
    def as_dependency(
        cls,
        protocol: None = None,
        *,
        scheme: Literal[Scheme.BEARER_TOKEN],
        auto_error: Literal[False],
    ) -> Callable[
        [HTTPConnection, HTTPAuthorizationCredentials | None, OptStr],
        BearerTokenAuthorization | None,
    ]: ...
    @overload
    @classmethod
    def as_dependency(
        cls,
        protocol: None = None,
        *,
        scheme: None = None,
        auto_error: Literal[True] = True,
    ) -> Callable[
        [HTTPConnection, HTTPAuthorizationCredentials | None, OptStr],
        BaseAuthorization,
    ]: ...
    @overload
    @classmethod
    def as_dependency(
        cls,
        protocol: None = None,
        *,
        scheme: Literal[Scheme.API_KEY],
        auto_error: Literal[True] = True,
    ) -> Callable[
        [HTTPConnection, HTTPAuthorizationCredentials | None, OptStr],
        APIKeyAuthorization,
    ]: ...
    @overload
    @classmethod
    def as_dependency(
        cls,
        protocol: None = None,
        *,
        scheme: Literal[Scheme.BEARER_TOKEN],
        auto_error: Literal[True] = True,
    ) -> Callable[
        [HTTPConnection, HTTPAuthorizationCredentials | None, OptStr],
        BearerTokenAuthorization,
    ]: ...

    @overload
    @classmethod
    def as_dependency(
        cls,
        protocol: Literal[Protocol.HTTP] = Protocol.HTTP,
        *,
        scheme: None = None,
        auto_error: Literal[False],
    ) -> Callable[
        [Request, HTTPAuthorizationCredentials | None, OptStr],
        BaseAuthorization | None,
    ]: ...
    @overload
    @classmethod
    def as_dependency(
        cls,
        protocol: Literal[Protocol.HTTP] = Protocol.HTTP,
        *,
        scheme: Literal[Scheme.API_KEY],
        auto_error: Literal[False],
    ) -> Callable[
        [Request, HTTPAuthorizationCredentials | None, OptStr],
        APIKeyAuthorization | None,
    ]: ...
    @overload
    @classmethod
    def as_dependency(
        cls,
        protocol: Literal[Protocol.HTTP] = Protocol.HTTP,
        *,
        scheme: Literal[Scheme.BEARER_TOKEN],
        auto_error: Literal[False],
    ) -> Callable[
        [Request, HTTPAuthorizationCredentials | None, OptStr],
        BearerTokenAuthorization | None,
    ]: ...
    @overload
    @classmethod
    def as_dependency(
        cls,
        protocol: Literal[Protocol.HTTP] = Protocol.HTTP,
        *,
        scheme: None = None,
        auto_error: Literal[True] = True,
    ) -> Callable[
        [Request, HTTPAuthorizationCredentials | None, OptStr],
        BaseAuthorization,
    ]: ...
    @overload
    @classmethod
    def as_dependency(
        cls,
        protocol: Literal[Protocol.HTTP] = Protocol.HTTP,
        *,
        scheme: Literal[Scheme.API_KEY],
        auto_error: Literal[True] = True,
    ) -> Callable[
        [Request, HTTPAuthorizationCredentials | None, OptStr],
        APIKeyAuthorization,
    ]: ...
    @overload
    @classmethod
    def as_dependency(
        cls,
        protocol: Literal[Protocol.HTTP] = Protocol.HTTP,
        *,
        scheme: Literal[Scheme.BEARER_TOKEN],
        auto_error: Literal[True] = True,
    ) -> Callable[
        [Request, HTTPAuthorizationCredentials | None, OptStr],
        BearerTokenAuthorization,
    ]: ...

    @overload
    @classmethod
    def as_dependency(
        cls,
        protocol: Literal[Protocol.WEBSOCKET],
        *,
        scheme: None = None,
        auto_error: Literal[False],
    ) -> Callable[[WebSocket], BaseAuthorization | None]: ...
    @overload
    @classmethod
    def as_dependency(
        cls,
        protocol: Literal[Protocol.WEBSOCKET],
        *,
        scheme: Literal[Scheme.API_KEY],
        auto_error: Literal[False],
    ) -> Callable[[WebSocket], APIKeyAuthorization | None]: ...
    @overload
    @classmethod
    def as_dependency(
        cls,
        protocol: Literal[Protocol.WEBSOCKET],
        *,
        scheme: Literal[Scheme.BEARER_TOKEN],
        auto_error: Literal[False],
    ) -> Callable[[WebSocket], BearerTokenAuthorization | None]: ...
    @overload
    @classmethod
    def as_dependency(
        cls,
        protocol: Literal[Protocol.WEBSOCKET],
        *,
        scheme: None = None,
        auto_error: Literal[True] = True,
    ) -> Callable[[WebSocket], BaseAuthorization]: ...
    @overload
    @classmethod
    def as_dependency(
        cls,
        protocol: Literal[Protocol.WEBSOCKET],
        *,
        scheme: Literal[Scheme.API_KEY],
        auto_error: Literal[True] = True,
    ) -> Callable[[WebSocket], APIKeyAuthorization]: ...
    @overload
    @classmethod
    def as_dependency(
        cls,
        protocol: Literal[Protocol.WEBSOCKET],
        *,
        scheme: Literal[Scheme.BEARER_TOKEN],
        auto_error: Literal[True] = True,
    ) -> Callable[[WebSocket], BearerTokenAuthorization]: ...

    @classmethod
    def as_dependency(
        cls,
        protocol: OptProtocol = None,
        *,
        scheme: OptScheme = None,
        auto_error: bool = True,
    ) -> (
        Callable[
            [HTTPConnection, HTTPAuthorizationCredentials | None, OptStr],
            OptAnyAuthorization,
        ]
        | Callable[
            [HTTPConnection, HTTPAuthorizationCredentials | None, OptStr],
            AnyAuthorization,
        ]
        | Callable[
            [Request, HTTPAuthorizationCredentials | None, OptStr],
            OptAnyAuthorization,
        ]
        | Callable[
            [Request, HTTPAuthorizationCredentials | None, OptStr],
            AnyAuthorization,
        ]
        | Callable[[WebSocket], OptAnyAuthorization]
        | Callable[[WebSocket], AnyAuthorization]
    ):
        if scheme is None:
            return BaseAuthorization.as_dependency(protocol, auto_error=auto_error)
        elif scheme is Scheme.API_KEY:
            return APIKeyAuthorization.as_dependency(protocol, auto_error=auto_error)
        elif scheme is Scheme.BEARER_TOKEN:
            return BearerTokenAuthorization.as_dependency(
                protocol, auto_error=auto_error
            )

    @overload
    @classmethod
    def httpx_auth(
        cls,
        scheme: Literal[Scheme.API_KEY],
        *,
        authorization: str | APIKeyAuthorization,
    ) -> APIKeyAuth: ...
    @overload
    @classmethod
    def httpx_auth(
        cls,
        scheme: Literal[Scheme.BEARER_TOKEN] = Scheme.BEARER_TOKEN,
        *,
        authorization: str | BearerTokenAuthorization,
    ) -> BearerTokenAuth: ...
    @classmethod
    def httpx_auth(
        cls,
        scheme: Scheme = Scheme.BEARER_TOKEN,
        *,
        authorization: str | AnyAuthorization,
    ) -> AnyHTTPXAuthorization:
        if isinstance(authorization, str):
            token = authorization
        else:
            token = authorization.credentials
        if scheme is Scheme.API_KEY:
            return APIKeyAuth(token)
        elif scheme is Scheme.BEARER_TOKEN:
            return BearerTokenAuth(token)

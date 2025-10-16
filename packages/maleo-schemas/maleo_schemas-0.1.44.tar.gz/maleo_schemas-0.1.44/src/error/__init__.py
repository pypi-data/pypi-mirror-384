from pydantic import BaseModel, Field
from typing import Any, Generic, Literal, Type, TypeVar, overload
from typing_extensions import Annotated
from maleo.types.string import OptListOfStrs, OptStr
from .descriptor import (
    ErrorDescriptorT,
    ErrorDescriptorMixin,
    BadRequestErrorDescriptor,
    UnauthorizedErrorDescriptor,
    ForbiddenErrorDescriptor,
    NotFoundErrorDescriptor,
    MethodNotAllowedErrorDescriptor,
    ConflictErrorDescriptor,
    UnprocessableEntityErrorDescriptor,
    TooManyRequestsErrorDescriptor,
    InternalServerErrorDescriptor,
    NotImplementedErrorDescriptor,
    BadGatewayErrorDescriptor,
    ServiceUnavailableErrorDescriptor,
    Factory as ErrorDescriptorFactory,
)
from .enums import ErrorCode
from .metadata import ErrorMetadata, ErrorMetadataMixin
from .spec import (
    ErrorSpecT,
    ErrorSpecMixin,
    BadRequestErrorSpec,
    UnauthorizedErrorSpec,
    ForbiddenErrorSpec,
    NotFoundErrorSpec,
    MethodNotAllowedErrorSpec,
    ConflictErrorSpec,
    UnprocessableEntityErrorSpec,
    TooManyRequestsErrorSpec,
    InternalServerErrorSpec,
    NotImplementedErrorSpec,
    BadGatewayErrorSpec,
    ServiceUnavailableErrorSpec,
    Factory as ErrorSpecFactory,
)


class Error(
    ErrorMetadataMixin,
    ErrorDescriptorMixin[ErrorDescriptorT],
    ErrorSpecMixin[ErrorSpecT],
    Generic[ErrorSpecT, ErrorDescriptorT],
):
    pass


class BadRequestError(Error[BadRequestErrorSpec, BadRequestErrorDescriptor]):
    spec: Annotated[
        BadRequestErrorSpec, Field(..., description="Bad request error spec")
    ] = BadRequestErrorSpec()
    descriptor: Annotated[
        BadRequestErrorDescriptor,
        Field(..., description="Bad request error descriptor"),
    ] = BadRequestErrorDescriptor()


class UnauthorizedError(Error[UnauthorizedErrorSpec, UnauthorizedErrorDescriptor]):
    spec: Annotated[
        UnauthorizedErrorSpec, Field(..., description="Unauthorized error spec")
    ] = UnauthorizedErrorSpec()
    descriptor: Annotated[
        UnauthorizedErrorDescriptor,
        Field(..., description="Unauthorized error descriptor"),
    ] = UnauthorizedErrorDescriptor()


class ForbiddenError(Error[ForbiddenErrorSpec, ForbiddenErrorDescriptor]):
    spec: Annotated[
        ForbiddenErrorSpec, Field(..., description="Forbidden error spec")
    ] = ForbiddenErrorSpec()
    descriptor: Annotated[
        ForbiddenErrorDescriptor, Field(..., description="Forbidden error descriptor")
    ] = ForbiddenErrorDescriptor()


class NotFoundError(Error[NotFoundErrorSpec, NotFoundErrorDescriptor]):
    spec: Annotated[
        NotFoundErrorSpec, Field(..., description="Not found error spec")
    ] = NotFoundErrorSpec()
    descriptor: Annotated[
        NotFoundErrorDescriptor, Field(..., description="Not found error descriptor")
    ] = NotFoundErrorDescriptor()


class MethodNotAllowedError(
    Error[MethodNotAllowedErrorSpec, MethodNotAllowedErrorDescriptor]
):
    spec: Annotated[
        MethodNotAllowedErrorSpec,
        Field(..., description="Method not allowed error spec"),
    ] = MethodNotAllowedErrorSpec()
    descriptor: Annotated[
        MethodNotAllowedErrorDescriptor,
        Field(..., description="Method not allowed error descriptor"),
    ] = MethodNotAllowedErrorDescriptor()


class ConflictError(Error[ConflictErrorSpec, ConflictErrorDescriptor]):
    spec: Annotated[
        ConflictErrorSpec, Field(..., description="Conflict error spec")
    ] = ConflictErrorSpec()
    descriptor: Annotated[
        ConflictErrorDescriptor, Field(..., description="Conflict error descriptor")
    ] = ConflictErrorDescriptor()


class UnprocessableEntityError(
    Error[UnprocessableEntityErrorSpec, UnprocessableEntityErrorDescriptor]
):
    spec: Annotated[
        UnprocessableEntityErrorSpec,
        Field(..., description="Unprocessable entity error spec"),
    ] = UnprocessableEntityErrorSpec()
    descriptor: Annotated[
        UnprocessableEntityErrorDescriptor,
        Field(..., description="Unprocessable entity error descriptor"),
    ] = UnprocessableEntityErrorDescriptor()


class TooManyRequestsError(
    Error[TooManyRequestsErrorSpec, TooManyRequestsErrorDescriptor]
):
    spec: Annotated[
        TooManyRequestsErrorSpec, Field(..., description="Too many requests error spec")
    ] = TooManyRequestsErrorSpec()
    descriptor: Annotated[
        TooManyRequestsErrorDescriptor,
        Field(..., description="Too many requests error descriptor"),
    ] = TooManyRequestsErrorDescriptor()


class InternalServerError(
    Error[InternalServerErrorSpec, InternalServerErrorDescriptor]
):
    spec: Annotated[
        InternalServerErrorSpec, Field(..., description="Internal server error spec")
    ] = InternalServerErrorSpec()
    descriptor: Annotated[
        InternalServerErrorDescriptor,
        Field(..., description="Internal server error descriptor"),
    ] = InternalServerErrorDescriptor()


class NotImplementedError(
    Error[NotImplementedErrorSpec, NotImplementedErrorDescriptor]
):
    spec: Annotated[
        NotImplementedErrorSpec, Field(..., description="Not implemented error spec")
    ] = NotImplementedErrorSpec()
    descriptor: Annotated[
        NotImplementedErrorDescriptor,
        Field(..., description="Not implemented error descriptor"),
    ] = NotImplementedErrorDescriptor()


class BadGatewayError(Error[BadGatewayErrorSpec, BadGatewayErrorDescriptor]):
    spec: Annotated[
        BadGatewayErrorSpec, Field(..., description="Bad gateway error spec")
    ] = BadGatewayErrorSpec()
    descriptor: Annotated[
        BadGatewayErrorDescriptor,
        Field(..., description="Bad gateway error descriptor"),
    ] = BadGatewayErrorDescriptor()


class ServiceUnavailableError(
    Error[ServiceUnavailableErrorSpec, ServiceUnavailableErrorDescriptor]
):
    spec: Annotated[
        ServiceUnavailableErrorSpec,
        Field(..., description="Service unavailable error spec"),
    ] = ServiceUnavailableErrorSpec()
    descriptor: Annotated[
        ServiceUnavailableErrorDescriptor,
        Field(..., description="Service unavailable error descriptor"),
    ] = ServiceUnavailableErrorDescriptor()


AnyErrorType = (
    Type[BadRequestError]
    | Type[UnauthorizedError]
    | Type[ForbiddenError]
    | Type[NotFoundError]
    | Type[MethodNotAllowedError]
    | Type[ConflictError]
    | Type[UnprocessableEntityError]
    | Type[TooManyRequestsError]
    | Type[InternalServerError]
    | Type[NotImplementedError]
    | Type[BadGatewayError]
    | Type[ServiceUnavailableError]
)
AnyError = (
    BadRequestError
    | UnauthorizedError
    | ForbiddenError
    | NotFoundError
    | MethodNotAllowedError
    | ConflictError
    | UnprocessableEntityError
    | TooManyRequestsError
    | InternalServerError
    | NotImplementedError
    | BadGatewayError
    | ServiceUnavailableError
)
AnyErrorT = TypeVar("AnyErrorT", bound=AnyError)
OptAnyError = AnyError | None
OptAnyErrorT = TypeVar("OptAnyErrorT", bound=OptAnyError)


class Factory:
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.BAD_REQUEST, 400],
        /,
    ) -> Type[BadRequestError]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.UNAUTHORIZED, 401],
        /,
    ) -> Type[UnauthorizedError]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.FORBIDDEN, 403],
        /,
    ) -> Type[ForbiddenError]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.NOT_FOUND, 404],
        /,
    ) -> Type[NotFoundError]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.METHOD_NOT_ALLOWED, 405],
        /,
    ) -> Type[MethodNotAllowedError]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.CONFLICT, 409],
        /,
    ) -> Type[ConflictError]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.UNPROCESSABLE_ENTITY, 422],
        /,
    ) -> Type[UnprocessableEntityError]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.TOO_MANY_REQUESTS, 429],
        /,
    ) -> Type[TooManyRequestsError]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.INTERNAL_SERVER_ERROR, 500],
        /,
    ) -> Type[InternalServerError]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.NOT_IMPLEMENTED, 501],
        /,
    ) -> Type[NotImplementedError]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.BAD_GATEWAY, 502],
        /,
    ) -> Type[BadGatewayError]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.SERVICE_UNAVAILABLE, 503],
        /,
    ) -> Type[ServiceUnavailableError]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: ErrorCode | int,
        /,
    ) -> AnyErrorType: ...
    @staticmethod
    def cls_from_code(
        code: ErrorCode | int,
        /,
    ) -> AnyErrorType:
        if code is ErrorCode.BAD_REQUEST or code == 400:
            return BadRequestError
        elif code is ErrorCode.UNAUTHORIZED or code == 401:
            return UnauthorizedError
        elif code is ErrorCode.FORBIDDEN or code == 403:
            return ForbiddenError
        elif code is ErrorCode.NOT_FOUND or code == 404:
            return NotFoundError
        elif code is ErrorCode.METHOD_NOT_ALLOWED or code == 405:
            return MethodNotAllowedError
        elif code is ErrorCode.CONFLICT or code == 409:
            return ConflictError
        elif code is ErrorCode.UNPROCESSABLE_ENTITY or code == 422:
            return UnprocessableEntityError
        elif code is ErrorCode.TOO_MANY_REQUESTS or code == 429:
            return TooManyRequestsError
        elif code is ErrorCode.INTERNAL_SERVER_ERROR or code == 500:
            return InternalServerError
        elif code is ErrorCode.NOT_IMPLEMENTED or code == 501:
            return NotImplementedError
        elif code is ErrorCode.BAD_GATEWAY or code == 502:
            return BadGatewayError
        elif code is ErrorCode.SERVICE_UNAVAILABLE or code == 503:
            return ServiceUnavailableError
        raise ValueError(f"Unable to determine error class for code: {code}")

    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.BAD_REQUEST, 400],
        *,
        message: OptStr = None,
        description: OptStr = None,
        details: Any = None,
        traceback: OptListOfStrs = None,
    ) -> BadRequestError: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.UNAUTHORIZED, 401],
        *,
        message: OptStr = None,
        description: OptStr = None,
        details: Any = None,
        traceback: OptListOfStrs = None,
    ) -> UnauthorizedError: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.FORBIDDEN, 403],
        *,
        message: OptStr = None,
        description: OptStr = None,
        details: Any = None,
        traceback: OptListOfStrs = None,
    ) -> ForbiddenError: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.NOT_FOUND, 404],
        *,
        message: OptStr = None,
        description: OptStr = None,
        details: Any = None,
        traceback: OptListOfStrs = None,
    ) -> NotFoundError: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.METHOD_NOT_ALLOWED, 405],
        *,
        message: OptStr = None,
        description: OptStr = None,
        details: Any = None,
        traceback: OptListOfStrs = None,
    ) -> MethodNotAllowedError: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.CONFLICT, 409],
        *,
        message: OptStr = None,
        description: OptStr = None,
        details: Any = None,
        traceback: OptListOfStrs = None,
    ) -> ConflictError: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.UNPROCESSABLE_ENTITY, 422],
        *,
        message: OptStr = None,
        description: OptStr = None,
        details: Any = None,
        traceback: OptListOfStrs = None,
    ) -> UnprocessableEntityError: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.TOO_MANY_REQUESTS, 429],
        *,
        message: OptStr = None,
        description: OptStr = None,
        details: Any = None,
        traceback: OptListOfStrs = None,
    ) -> TooManyRequestsError: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.INTERNAL_SERVER_ERROR, 500],
        *,
        message: OptStr = None,
        description: OptStr = None,
        details: Any = None,
        traceback: OptListOfStrs = None,
    ) -> InternalServerError: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.NOT_IMPLEMENTED, 501],
        *,
        message: OptStr = None,
        description: OptStr = None,
        details: Any = None,
        traceback: OptListOfStrs = None,
    ) -> NotImplementedError: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.BAD_GATEWAY, 502],
        *,
        message: OptStr = None,
        description: OptStr = None,
        details: Any = None,
        traceback: OptListOfStrs = None,
    ) -> BadGatewayError: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.SERVICE_UNAVAILABLE, 503],
        *,
        message: OptStr = None,
        description: OptStr = None,
        details: Any = None,
        traceback: OptListOfStrs = None,
    ) -> ServiceUnavailableError: ...
    @overload
    @staticmethod
    def from_code(
        code: ErrorCode | int,
        *,
        message: OptStr = None,
        description: OptStr = None,
        details: Any = None,
        traceback: OptListOfStrs = None,
    ) -> AnyError: ...
    @staticmethod
    def from_code(
        code: ErrorCode | int,
        *,
        message: OptStr = None,
        description: OptStr = None,
        details: Any = None,
        traceback: OptListOfStrs = None,
    ) -> AnyError:
        return Factory.cls_from_code(code)(
            spec=ErrorSpecFactory.from_code(code),  # type: ignore
            descriptor=ErrorDescriptorFactory.from_code(
                code, message=message, description=description
            ),  # type: ignore
            metadata=ErrorMetadata(details=details, traceback=traceback),
        )


class ErrorMixin(BaseModel, Generic[OptAnyErrorT]):
    error: OptAnyErrorT = Field(..., description="Error")

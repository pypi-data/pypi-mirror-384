from pydantic import BaseModel, Field
from typing import Generic, Literal, Type, TypeVar, overload
from typing_extensions import Annotated
from ..mixins.general import StatusCode
from .enums import ErrorType as ErrorTypeEnum
from .enums import ErrorCode


class ErrorType(BaseModel):
    type: Annotated[
        ErrorTypeEnum,
        Field(ErrorTypeEnum.INTERNAL_SERVER_ERROR, description="Error type"),
    ] = ErrorTypeEnum.INTERNAL_SERVER_ERROR


class ErrorSpec(StatusCode, ErrorType):
    status_code: Annotated[
        int, Field(500, description="Status code", ge=400, le=600)
    ] = 500


ErrorSpecT = TypeVar("ErrorSpecT", bound=ErrorSpec)


class ErrorSpecMixin(BaseModel, Generic[ErrorSpecT]):
    spec: Annotated[ErrorSpecT, Field(..., description="Error's Spec")]


class BadRequestErrorSpec(ErrorSpec):
    type: ErrorTypeEnum = ErrorTypeEnum.BAD_REQUEST
    status_code: int = 400


class UnauthorizedErrorSpec(ErrorSpec):
    type: ErrorTypeEnum = ErrorTypeEnum.UNAUTHORIZED
    status_code: int = 401


class ForbiddenErrorSpec(ErrorSpec):
    type: ErrorTypeEnum = ErrorTypeEnum.FORBIDDEN
    status_code: int = 403


class NotFoundErrorSpec(ErrorSpec):
    type: ErrorTypeEnum = ErrorTypeEnum.NOT_FOUND
    status_code: int = 404


class MethodNotAllowedErrorSpec(ErrorSpec):
    type: ErrorTypeEnum = ErrorTypeEnum.METHOD_NOT_ALLOWED
    status_code: int = 405


class ConflictErrorSpec(ErrorSpec):
    type: ErrorTypeEnum = ErrorTypeEnum.CONFLICT
    status_code: int = 409


class UnprocessableEntityErrorSpec(ErrorSpec):
    type: ErrorTypeEnum = ErrorTypeEnum.UNPROCESSABLE_ENTITY
    status_code: int = 422


class TooManyRequestsErrorSpec(ErrorSpec):
    type: ErrorTypeEnum = ErrorTypeEnum.TOO_MANY_REQUESTS
    status_code: int = 429


class InternalServerErrorSpec(ErrorSpec):
    type: ErrorTypeEnum = ErrorTypeEnum.INTERNAL_SERVER_ERROR
    status_code: int = 500


class NotImplementedErrorSpec(ErrorSpec):
    type: ErrorTypeEnum = ErrorTypeEnum.NOT_IMPLEMENTED
    status_code: int = 501


class BadGatewayErrorSpec(ErrorSpec):
    type: ErrorTypeEnum = ErrorTypeEnum.BAD_GATEWAY
    status_code: int = 502


class ServiceUnavailableErrorSpec(ErrorSpec):
    type: ErrorTypeEnum = ErrorTypeEnum.SERVICE_UNAVAILABLE
    status_code: int = 503


AnyErrorSpecType = (
    Type[BadRequestErrorSpec]
    | Type[UnauthorizedErrorSpec]
    | Type[ForbiddenErrorSpec]
    | Type[NotFoundErrorSpec]
    | Type[MethodNotAllowedErrorSpec]
    | Type[ConflictErrorSpec]
    | Type[UnprocessableEntityErrorSpec]
    | Type[TooManyRequestsErrorSpec]
    | Type[InternalServerErrorSpec]
    | Type[NotImplementedErrorSpec]
    | Type[BadGatewayErrorSpec]
    | Type[ServiceUnavailableErrorSpec]
)
AnyErrorSpec = (
    BadRequestErrorSpec
    | UnauthorizedErrorSpec
    | ForbiddenErrorSpec
    | NotFoundErrorSpec
    | MethodNotAllowedErrorSpec
    | ConflictErrorSpec
    | UnprocessableEntityErrorSpec
    | TooManyRequestsErrorSpec
    | InternalServerErrorSpec
    | NotImplementedErrorSpec
    | BadGatewayErrorSpec
    | ServiceUnavailableErrorSpec
)


class Factory:
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.BAD_REQUEST, 400],
        /,
    ) -> Type[BadRequestErrorSpec]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.UNAUTHORIZED, 401],
        /,
    ) -> Type[UnauthorizedErrorSpec]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.FORBIDDEN, 403],
        /,
    ) -> Type[ForbiddenErrorSpec]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.NOT_FOUND, 404],
        /,
    ) -> Type[NotFoundErrorSpec]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.METHOD_NOT_ALLOWED, 405],
        /,
    ) -> Type[MethodNotAllowedErrorSpec]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.CONFLICT, 409],
        /,
    ) -> Type[ConflictErrorSpec]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.UNPROCESSABLE_ENTITY, 422],
        /,
    ) -> Type[UnprocessableEntityErrorSpec]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.TOO_MANY_REQUESTS, 429],
        /,
    ) -> Type[TooManyRequestsErrorSpec]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.INTERNAL_SERVER_ERROR, 500],
        /,
    ) -> Type[InternalServerErrorSpec]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.NOT_IMPLEMENTED, 501],
        /,
    ) -> Type[NotImplementedErrorSpec]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.BAD_GATEWAY, 502],
        /,
    ) -> Type[BadGatewayErrorSpec]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.SERVICE_UNAVAILABLE, 503],
        /,
    ) -> Type[ServiceUnavailableErrorSpec]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: ErrorCode | int,
        /,
    ) -> AnyErrorSpecType: ...
    @staticmethod
    def cls_from_code(
        code: ErrorCode | int,
        /,
    ) -> AnyErrorSpecType:
        if code is ErrorCode.BAD_REQUEST or code == 400:
            return BadRequestErrorSpec
        elif code is ErrorCode.UNAUTHORIZED or code == 401:
            return UnauthorizedErrorSpec
        elif code is ErrorCode.FORBIDDEN or code == 403:
            return ForbiddenErrorSpec
        elif code is ErrorCode.NOT_FOUND or code == 404:
            return NotFoundErrorSpec
        elif code is ErrorCode.METHOD_NOT_ALLOWED or code == 405:
            return MethodNotAllowedErrorSpec
        elif code is ErrorCode.CONFLICT or code == 409:
            return ConflictErrorSpec
        elif code is ErrorCode.UNPROCESSABLE_ENTITY or code == 422:
            return UnprocessableEntityErrorSpec
        elif code is ErrorCode.TOO_MANY_REQUESTS or code == 429:
            return TooManyRequestsErrorSpec
        elif code is ErrorCode.INTERNAL_SERVER_ERROR or code == 500:
            return InternalServerErrorSpec
        elif code is ErrorCode.NOT_IMPLEMENTED or code == 501:
            return NotImplementedErrorSpec
        elif code is ErrorCode.BAD_GATEWAY or code == 502:
            return BadGatewayErrorSpec
        elif code is ErrorCode.SERVICE_UNAVAILABLE or code == 503:
            return ServiceUnavailableErrorSpec
        raise ValueError(f"Unable to determine error descriptor class for code: {code}")

    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.BAD_REQUEST, 400],
        /,
    ) -> BadRequestErrorSpec: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.UNAUTHORIZED, 401],
        /,
    ) -> UnauthorizedErrorSpec: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.FORBIDDEN, 403],
        /,
    ) -> ForbiddenErrorSpec: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.NOT_FOUND, 404],
        /,
    ) -> NotFoundErrorSpec: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.METHOD_NOT_ALLOWED, 405],
        /,
    ) -> MethodNotAllowedErrorSpec: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.CONFLICT, 409],
        /,
    ) -> ConflictErrorSpec: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.UNPROCESSABLE_ENTITY, 422],
        /,
    ) -> UnprocessableEntityErrorSpec: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.TOO_MANY_REQUESTS, 429],
        /,
    ) -> TooManyRequestsErrorSpec: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.INTERNAL_SERVER_ERROR, 500],
        /,
    ) -> InternalServerErrorSpec: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.NOT_IMPLEMENTED, 501],
        /,
    ) -> NotImplementedErrorSpec: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.BAD_GATEWAY, 502],
        /,
    ) -> BadGatewayErrorSpec: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.SERVICE_UNAVAILABLE, 503],
        /,
    ) -> ServiceUnavailableErrorSpec: ...
    @overload
    @staticmethod
    def from_code(
        code: ErrorCode | int,
        /,
    ) -> AnyErrorSpec: ...
    @staticmethod
    def from_code(
        code: ErrorCode | int,
        /,
    ) -> AnyErrorSpec:
        return Factory.cls_from_code(code)()

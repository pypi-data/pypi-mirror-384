from pydantic import BaseModel, Field
from typing import Generic, Literal, Type, TypeVar, overload
from typing_extensions import Annotated
from maleo.types.string import OptStr
from ..mixins.general import Descriptor
from .enums import ErrorCode


class ErrorDescriptor(Descriptor[ErrorCode]):
    code: Annotated[
        ErrorCode, Field(ErrorCode.INTERNAL_SERVER_ERROR, description="Error's code")
    ] = ErrorCode.INTERNAL_SERVER_ERROR
    message: Annotated[str, Field("Error", description="Error's message")] = "Error"
    description: Annotated[
        str, Field("An error occurred", description="Error's description")
    ] = "An error occurred"


ErrorDescriptorT = TypeVar("ErrorDescriptorT", bound=ErrorDescriptor)


class ErrorDescriptorMixin(BaseModel, Generic[ErrorDescriptorT]):
    descriptor: ErrorDescriptorT = Field(..., description="Error's Descriptor")


class BadRequestErrorDescriptor(ErrorDescriptor):
    code: ErrorCode = ErrorCode.BAD_REQUEST
    message: str = "Bad Request"
    description: str = "Bad/Unexpected parameters given"


class UnauthorizedErrorDescriptor(ErrorDescriptor):
    code: ErrorCode = ErrorCode.UNAUTHORIZED
    message: str = "Unauthorized"
    description: str = "Authentication is required or invalid"


class ForbiddenErrorDescriptor(ErrorDescriptor):
    code: ErrorCode = ErrorCode.FORBIDDEN
    message: str = "Forbidden"
    description: str = "Insufficient permission found"


class NotFoundErrorDescriptor(ErrorDescriptor):
    code: ErrorCode = ErrorCode.NOT_FOUND
    message: str = "Not Found"
    description: str = "The requested resource could not be found"


class MethodNotAllowedErrorDescriptor(ErrorDescriptor):
    code: ErrorCode = ErrorCode.METHOD_NOT_ALLOWED
    message: str = "Method Not Allowed"
    description: str = "The HTTP method is not supported for this resource"


class ConflictErrorDescriptor(ErrorDescriptor):
    code: ErrorCode = ErrorCode.CONFLICT
    message: str = "Conflict"
    description: str = "Failed processing request due to conflicting state"


class UnprocessableEntityErrorDescriptor(ErrorDescriptor):
    code: ErrorCode = ErrorCode.UNPROCESSABLE_ENTITY
    message: str = "Unprocessable Entity"
    description: str = "The request was well-formed but could not be processed"


class TooManyRequestsErrorDescriptor(ErrorDescriptor):
    code: ErrorCode = ErrorCode.TOO_MANY_REQUESTS
    message: str = "Too Many Requests"
    description: str = "You have sent too many requests in a given time frame"


class InternalServerErrorDescriptor(ErrorDescriptor):
    code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR
    message: str = "Internal Server Error"
    description: str = "An unexpected error occurred on the server"


class NotImplementedErrorDescriptor(ErrorDescriptor):
    code: ErrorCode = ErrorCode.NOT_IMPLEMENTED
    message: str = "Not Implemented"
    description: str = "This functionality is not supported by the server"


class BadGatewayErrorDescriptor(ErrorDescriptor):
    code: ErrorCode = ErrorCode.BAD_GATEWAY
    message: str = "Bad Gateway"
    description: str = "The server received an invalid response from an upstream server"


class ServiceUnavailableErrorDescriptor(ErrorDescriptor):
    code: ErrorCode = ErrorCode.SERVICE_UNAVAILABLE
    message: str = "Service Unavailable"
    description: str = "The server is temporarily unable to handle the request"


AnyErrorDescriptorType = (
    Type[BadRequestErrorDescriptor]
    | Type[UnauthorizedErrorDescriptor]
    | Type[ForbiddenErrorDescriptor]
    | Type[NotFoundErrorDescriptor]
    | Type[MethodNotAllowedErrorDescriptor]
    | Type[ConflictErrorDescriptor]
    | Type[UnprocessableEntityErrorDescriptor]
    | Type[TooManyRequestsErrorDescriptor]
    | Type[InternalServerErrorDescriptor]
    | Type[NotImplementedErrorDescriptor]
    | Type[BadGatewayErrorDescriptor]
    | Type[ServiceUnavailableErrorDescriptor]
)
AnyErrorDescriptor = (
    BadRequestErrorDescriptor
    | UnauthorizedErrorDescriptor
    | ForbiddenErrorDescriptor
    | NotFoundErrorDescriptor
    | MethodNotAllowedErrorDescriptor
    | ConflictErrorDescriptor
    | UnprocessableEntityErrorDescriptor
    | TooManyRequestsErrorDescriptor
    | InternalServerErrorDescriptor
    | NotImplementedErrorDescriptor
    | BadGatewayErrorDescriptor
    | ServiceUnavailableErrorDescriptor
)


class Factory:
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.BAD_REQUEST, 400],
        /,
    ) -> Type[BadRequestErrorDescriptor]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.UNAUTHORIZED, 401],
        /,
    ) -> Type[UnauthorizedErrorDescriptor]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.FORBIDDEN, 403],
        /,
    ) -> Type[ForbiddenErrorDescriptor]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.NOT_FOUND, 404],
        /,
    ) -> Type[NotFoundErrorDescriptor]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.METHOD_NOT_ALLOWED, 405],
        /,
    ) -> Type[MethodNotAllowedErrorDescriptor]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.CONFLICT, 409],
        /,
    ) -> Type[ConflictErrorDescriptor]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.UNPROCESSABLE_ENTITY, 422],
        /,
    ) -> Type[UnprocessableEntityErrorDescriptor]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.TOO_MANY_REQUESTS, 429],
        /,
    ) -> Type[TooManyRequestsErrorDescriptor]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.INTERNAL_SERVER_ERROR, 500],
        /,
    ) -> Type[InternalServerErrorDescriptor]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.NOT_IMPLEMENTED, 501],
        /,
    ) -> Type[NotImplementedErrorDescriptor]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.BAD_GATEWAY, 502],
        /,
    ) -> Type[BadGatewayErrorDescriptor]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.SERVICE_UNAVAILABLE, 503],
        /,
    ) -> Type[ServiceUnavailableErrorDescriptor]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: ErrorCode | int,
        /,
    ) -> AnyErrorDescriptorType: ...
    @staticmethod
    def cls_from_code(
        code: ErrorCode | int,
        /,
    ) -> AnyErrorDescriptorType:
        if code is ErrorCode.BAD_REQUEST or code == 400:
            return BadRequestErrorDescriptor
        elif code is ErrorCode.UNAUTHORIZED or code == 401:
            return UnauthorizedErrorDescriptor
        elif code is ErrorCode.FORBIDDEN or code == 403:
            return ForbiddenErrorDescriptor
        elif code is ErrorCode.NOT_FOUND or code == 404:
            return NotFoundErrorDescriptor
        elif code is ErrorCode.METHOD_NOT_ALLOWED or code == 405:
            return MethodNotAllowedErrorDescriptor
        elif code is ErrorCode.CONFLICT or code == 409:
            return ConflictErrorDescriptor
        elif code is ErrorCode.UNPROCESSABLE_ENTITY or code == 422:
            return UnprocessableEntityErrorDescriptor
        elif code is ErrorCode.TOO_MANY_REQUESTS or code == 429:
            return TooManyRequestsErrorDescriptor
        elif code is ErrorCode.INTERNAL_SERVER_ERROR or code == 500:
            return InternalServerErrorDescriptor
        elif code is ErrorCode.NOT_IMPLEMENTED or code == 501:
            return NotImplementedErrorDescriptor
        elif code is ErrorCode.BAD_GATEWAY or code == 502:
            return BadGatewayErrorDescriptor
        elif code is ErrorCode.SERVICE_UNAVAILABLE or code == 503:
            return ServiceUnavailableErrorDescriptor
        raise ValueError(f"Unable to determine error descriptor class for code: {code}")

    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.BAD_REQUEST, 400],
        *,
        message: OptStr = None,
        description: OptStr = None,
    ) -> BadRequestErrorDescriptor: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.UNAUTHORIZED, 401],
        *,
        message: OptStr = None,
        description: OptStr = None,
    ) -> UnauthorizedErrorDescriptor: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.FORBIDDEN, 403],
        *,
        message: OptStr = None,
        description: OptStr = None,
    ) -> ForbiddenErrorDescriptor: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.NOT_FOUND, 404],
        *,
        message: OptStr = None,
        description: OptStr = None,
    ) -> NotFoundErrorDescriptor: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.METHOD_NOT_ALLOWED, 405],
        *,
        message: OptStr = None,
        description: OptStr = None,
    ) -> MethodNotAllowedErrorDescriptor: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.CONFLICT, 409],
        *,
        message: OptStr = None,
        description: OptStr = None,
    ) -> ConflictErrorDescriptor: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.UNPROCESSABLE_ENTITY, 422],
        *,
        message: OptStr = None,
        description: OptStr = None,
    ) -> UnprocessableEntityErrorDescriptor: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.TOO_MANY_REQUESTS, 429],
        *,
        message: OptStr = None,
        description: OptStr = None,
    ) -> TooManyRequestsErrorDescriptor: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.INTERNAL_SERVER_ERROR, 500],
        *,
        message: OptStr = None,
        description: OptStr = None,
    ) -> InternalServerErrorDescriptor: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.NOT_IMPLEMENTED, 501],
        *,
        message: OptStr = None,
        description: OptStr = None,
    ) -> NotImplementedErrorDescriptor: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.BAD_GATEWAY, 502],
        *,
        message: OptStr = None,
        description: OptStr = None,
    ) -> BadGatewayErrorDescriptor: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.SERVICE_UNAVAILABLE, 503],
        *,
        message: OptStr = None,
        description: OptStr = None,
    ) -> ServiceUnavailableErrorDescriptor: ...
    @overload
    @staticmethod
    def from_code(
        code: ErrorCode | int,
        *,
        message: OptStr = None,
        description: OptStr = None,
    ) -> AnyErrorDescriptor: ...
    @staticmethod
    def from_code(
        code: ErrorCode | int,
        *,
        message: OptStr = None,
        description: OptStr = None,
    ) -> AnyErrorDescriptor:
        obj = {}
        if message is not None:
            obj["message"] = message
        if description is not None:
            obj["description"] = description
        return Factory.cls_from_code(code).model_validate(obj)

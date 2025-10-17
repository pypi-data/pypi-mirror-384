from pydantic import BaseModel, Field
from typing import (
    Annotated,
    Any,
    Generic,
    Literal,
    Type,
    TypeVar,
    overload,
)
from maleo.types.boolean import BoolT
from maleo.types.dict import StrToAnyDict
from maleo.types.misc import IntOrStr, StrOrStrEnumT
from maleo.types.string import OptStr, OptListOfDoubleStrs
from .data import DataPair, AnyDataT, ModelDataT
from .error.descriptor import (
    ErrorDescriptor,
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
)
from .error.enums import ErrorCode
from .metadata import AnyMetadataT, ModelMetadataT
from .mixins.general import Success, Descriptor
from .pagination import OptPaginationT, PaginationT
from .payload import (
    Payload,
    NoDataPayload,
    SingleDataPayload,
    CreateSingleDataPayload,
    ReadSingleDataPayload,
    UpdateSingleDataPayload,
    DeleteSingleDataPayload,
    OptSingleDataPayload,
    MultipleDataPayload,
    CreateMultipleDataPayload,
    ReadMultipleDataPayload,
    UpdateMultipleDataPayload,
    DeleteMultipleDataPayload,
    OptMultipleDataPayload,
)
from .success.descriptor import (
    SuccessDescriptor,
    AnyDataSuccessDescriptor,
    NoDataSuccessDescriptor,
    SingleDataSuccessDescriptor,
    OptSingleDataSuccessDescriptor,
    CreateSingleDataSuccessDescriptor,
    ReadSingleDataSuccessDescriptor,
    UpdateSingleDataSuccessDescriptor,
    DeleteSingleDataSuccessDescriptor,
    MultipleDataSuccessDescriptor,
    OptMultipleDataSuccessDescriptor,
    CreateMultipleDataSuccessDescriptor,
    ReadMultipleDataSuccessDescriptor,
    UpdateMultipleDataSuccessDescriptor,
    DeleteMultipleDataSuccessDescriptor,
)
from .success.enums import SuccessCode


class ResponseContext(BaseModel):
    status_code: Annotated[int, Field(..., description="Status code")]
    media_type: Annotated[OptStr, Field(None, description="Media type (Optional)")] = (
        None
    )
    headers: Annotated[
        OptListOfDoubleStrs, Field(None, description="Response's headers")
    ] = None


OptResponseContext = ResponseContext | None
OptResponseContextT = TypeVar("OptResponseContextT", bound=OptResponseContext)


class ResponseContextMixin(BaseModel, Generic[OptResponseContextT]):
    response_context: OptResponseContextT = Field(..., description="Response's context")


class Response(
    Payload[AnyDataT, OptPaginationT, AnyMetadataT],
    Descriptor[StrOrStrEnumT],
    Success[BoolT],
    BaseModel,
    Generic[BoolT, StrOrStrEnumT, AnyDataT, OptPaginationT, AnyMetadataT],
):
    pass


OptResponse = Response | None


# Error Response
class ErrorResponse(
    NoDataPayload[None],
    ErrorDescriptor,
    Response[Literal[False], ErrorCode, None, None, None],
):
    success: Literal[False] = False
    data: None = None
    pagination: None = None
    metadata: None = None
    other: Any = "Please try again later or contact administrator"


OptErrorResponse = ErrorResponse | None


class BadRequestResponse(
    BadRequestErrorDescriptor,
    ErrorResponse,
):
    pass


OptBadRequestResponse = BadRequestResponse | None


class UnauthorizedResponse(
    UnauthorizedErrorDescriptor,
    ErrorResponse,
):
    pass


OptUnauthorizedResponse = UnauthorizedResponse | None


class ForbiddenResponse(
    ForbiddenErrorDescriptor,
    ErrorResponse,
):
    pass


OptForbiddenResponse = ForbiddenResponse | None


class NotFoundResponse(
    NotFoundErrorDescriptor,
    ErrorResponse,
):
    pass


OptNotFoundResponse = NotFoundResponse | None


class MethodNotAllowedResponse(
    MethodNotAllowedErrorDescriptor,
    ErrorResponse,
):
    pass


OptMethodNotAllowedResponse = MethodNotAllowedResponse | None


class ConflictResponse(
    ConflictErrorDescriptor,
    ErrorResponse,
):
    pass


OptConflictResponse = ConflictResponse | None


class UnprocessableEntityResponse(
    UnprocessableEntityErrorDescriptor,
    ErrorResponse,
):
    pass


OptUnprocessableEntityResponse = UnprocessableEntityResponse | None


class TooManyRequestsResponse(
    TooManyRequestsErrorDescriptor,
    ErrorResponse,
):
    pass


OptTooManyRequestsResponse = TooManyRequestsResponse | None


class InternalServerErrorResponse(
    InternalServerErrorDescriptor,
    ErrorResponse,
):
    pass


OptInternalServerErrorResponse = InternalServerErrorResponse | None


class NotImplementedResponse(
    NotImplementedErrorDescriptor,
    ErrorResponse,
):
    pass


OptNotImplementedResponse = NotImplementedResponse | None


class BadGatewayResponse(
    BadGatewayErrorDescriptor,
    ErrorResponse,
):
    pass


OptBadGatewayResponse = BadGatewayResponse | None


class ServiceUnavailableResponse(
    ServiceUnavailableErrorDescriptor,
    ErrorResponse,
):
    pass


OptServiceUnavailableResponse = ServiceUnavailableResponse | None


AnyErrorResponseType = (
    Type[BadRequestResponse]
    | Type[UnauthorizedResponse]
    | Type[ForbiddenResponse]
    | Type[NotFoundResponse]
    | Type[MethodNotAllowedResponse]
    | Type[ConflictResponse]
    | Type[UnprocessableEntityResponse]
    | Type[TooManyRequestsResponse]
    | Type[InternalServerErrorResponse]
    | Type[NotImplementedResponse]
    | Type[BadGatewayResponse]
    | Type[ServiceUnavailableResponse]
)
AnyErrorResponse = (
    BadRequestResponse
    | UnauthorizedResponse
    | ForbiddenResponse
    | NotFoundResponse
    | MethodNotAllowedResponse
    | ConflictResponse
    | UnprocessableEntityResponse
    | TooManyRequestsResponse
    | InternalServerErrorResponse
    | NotImplementedResponse
    | BadGatewayResponse
    | ServiceUnavailableResponse
)
ErrorResponseT = TypeVar("ErrorResponseT", bound=AnyErrorResponse)
OptAnyErrorResponse = AnyErrorResponse | None


class ErrorFactory:
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.BAD_REQUEST, 400],
        /,
    ) -> Type[BadRequestResponse]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.UNAUTHORIZED, 401],
        /,
    ) -> Type[UnauthorizedResponse]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.FORBIDDEN, 403],
        /,
    ) -> Type[ForbiddenResponse]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.NOT_FOUND, 404],
        /,
    ) -> Type[NotFoundResponse]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.METHOD_NOT_ALLOWED, 405],
        /,
    ) -> Type[MethodNotAllowedResponse]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.CONFLICT, 409],
        /,
    ) -> Type[ConflictResponse]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.UNPROCESSABLE_ENTITY, 422],
        /,
    ) -> Type[UnprocessableEntityResponse]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.TOO_MANY_REQUESTS, 429],
        /,
    ) -> Type[TooManyRequestsResponse]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.INTERNAL_SERVER_ERROR, 500],
        /,
    ) -> Type[InternalServerErrorResponse]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.NOT_IMPLEMENTED, 501],
        /,
    ) -> Type[NotImplementedResponse]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.BAD_GATEWAY, 502],
        /,
    ) -> Type[BadGatewayResponse]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: Literal[ErrorCode.SERVICE_UNAVAILABLE, 503],
        /,
    ) -> Type[ServiceUnavailableResponse]: ...
    @overload
    @staticmethod
    def cls_from_code(
        code: ErrorCode | int,
        /,
    ) -> AnyErrorResponseType: ...
    @staticmethod
    def cls_from_code(
        code: ErrorCode | int,
        /,
    ) -> AnyErrorResponseType:
        if code is ErrorCode.BAD_REQUEST or code == 400:
            return BadRequestResponse
        elif code is ErrorCode.UNAUTHORIZED or code == 401:
            return UnauthorizedResponse
        elif code is ErrorCode.FORBIDDEN or code == 403:
            return ForbiddenResponse
        elif code is ErrorCode.NOT_FOUND or code == 404:
            return NotFoundResponse
        elif code is ErrorCode.METHOD_NOT_ALLOWED or code == 405:
            return MethodNotAllowedResponse
        elif code is ErrorCode.CONFLICT or code == 409:
            return ConflictResponse
        elif code is ErrorCode.UNPROCESSABLE_ENTITY or code == 422:
            return UnprocessableEntityResponse
        elif code is ErrorCode.TOO_MANY_REQUESTS or code == 429:
            return TooManyRequestsResponse
        elif code is ErrorCode.INTERNAL_SERVER_ERROR or code == 500:
            return InternalServerErrorResponse
        elif code is ErrorCode.NOT_IMPLEMENTED or code == 501:
            return NotImplementedResponse
        elif code is ErrorCode.BAD_GATEWAY or code == 502:
            return BadGatewayResponse
        elif code is ErrorCode.SERVICE_UNAVAILABLE or code == 503:
            return ServiceUnavailableResponse
        raise ValueError(f"Unable to determine error response class for code: {code}")

    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.BAD_REQUEST, 400],
        *,
        message: OptStr = None,
        description: OptStr = None,
        other: Any = None,
    ) -> BadRequestResponse: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.UNAUTHORIZED, 401],
        *,
        message: OptStr = None,
        description: OptStr = None,
        other: Any = None,
    ) -> UnauthorizedResponse: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.FORBIDDEN, 403],
        *,
        message: OptStr = None,
        description: OptStr = None,
        other: Any = None,
    ) -> ForbiddenResponse: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.NOT_FOUND, 404],
        *,
        message: OptStr = None,
        description: OptStr = None,
        other: Any = None,
    ) -> NotFoundResponse: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.METHOD_NOT_ALLOWED, 405],
        *,
        message: OptStr = None,
        description: OptStr = None,
        other: Any = None,
    ) -> MethodNotAllowedResponse: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.CONFLICT, 409],
        *,
        message: OptStr = None,
        description: OptStr = None,
        other: Any = None,
    ) -> ConflictResponse: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.UNPROCESSABLE_ENTITY, 422],
        *,
        message: OptStr = None,
        description: OptStr = None,
        other: Any = None,
    ) -> UnprocessableEntityResponse: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.TOO_MANY_REQUESTS, 429],
        *,
        message: OptStr = None,
        description: OptStr = None,
        other: Any = None,
    ) -> TooManyRequestsResponse: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.INTERNAL_SERVER_ERROR, 500],
        *,
        message: OptStr = None,
        description: OptStr = None,
        other: Any = None,
    ) -> InternalServerErrorResponse: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.NOT_IMPLEMENTED, 501],
        *,
        message: OptStr = None,
        description: OptStr = None,
        other: Any = None,
    ) -> NotImplementedResponse: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.BAD_GATEWAY, 502],
        *,
        message: OptStr = None,
        description: OptStr = None,
        other: Any = None,
    ) -> BadGatewayResponse: ...
    @overload
    @staticmethod
    def from_code(
        code: Literal[ErrorCode.SERVICE_UNAVAILABLE, 503],
        *,
        message: OptStr = None,
        description: OptStr = None,
        other: Any = None,
    ) -> ServiceUnavailableResponse: ...
    @overload
    @staticmethod
    def from_code(
        code: ErrorCode | int,
        *,
        message: OptStr = None,
        description: OptStr = None,
        other: Any = None,
    ) -> AnyErrorResponse: ...
    @staticmethod
    def from_code(
        code: ErrorCode | int,
        *,
        message: OptStr = None,
        description: OptStr = None,
        other: Any = None,
    ) -> AnyErrorResponse:
        obj = {}
        if message is not None:
            obj["message"] = message
        if description is not None:
            obj["description"] = description
        if other is not None:
            obj["other"] = other
        return ErrorFactory.cls_from_code(code).model_validate(obj)


OTHER_RESPONSES: dict[
    IntOrStr,
    StrToAnyDict,
] = {
    400: {
        "description": "Bad Request Response",
        "model": BadRequestResponse,
    },
    401: {
        "description": "Unauthorized Response",
        "model": UnauthorizedResponse,
    },
    403: {
        "description": "Forbidden Response",
        "model": ForbiddenResponse,
    },
    404: {
        "description": "Not Found Response",
        "model": NotFoundResponse,
    },
    405: {
        "description": "Method Not Allowed Response",
        "model": MethodNotAllowedResponse,
    },
    409: {
        "description": "Conflict Response",
        "model": ConflictResponse,
    },
    422: {
        "description": "Unprocessable Entity Response",
        "model": UnprocessableEntityResponse,
    },
    429: {
        "description": "Too Many Requests Response",
        "model": TooManyRequestsResponse,
    },
    500: {
        "description": "Internal Server Error Response",
        "model": InternalServerErrorResponse,
    },
    501: {
        "description": "Not Implemented Response",
        "model": NotImplementedResponse,
    },
    502: {
        "description": "Bad Gateway Response",
        "model": BadGatewayResponse,
    },
    503: {
        "description": "Service Unavailable Response",
        "model": ServiceUnavailableResponse,
    },
}


class SuccessResponse(
    SuccessDescriptor,
    Response[Literal[True], SuccessCode, AnyDataT, OptPaginationT, AnyMetadataT],
    Generic[AnyDataT, OptPaginationT, AnyMetadataT],
):
    success: Literal[True] = True


class AnyDataResponse(
    AnyDataSuccessDescriptor,
    SuccessResponse[AnyDataT, OptPaginationT, AnyMetadataT],
    Generic[AnyDataT, OptPaginationT, AnyMetadataT],
):
    pass


class NoDataResponse(
    NoDataPayload[ModelMetadataT],
    NoDataSuccessDescriptor,
    SuccessResponse[None, None, ModelMetadataT],
    Generic[ModelMetadataT],
):
    data: None = None
    pagination: None = None

    @classmethod
    def new(
        cls,
        *,
        message: OptStr = None,
        description: OptStr = None,
        metadata: ModelMetadataT = None,
        other: Any = None,
    ) -> "NoDataResponse[ModelMetadataT]":
        descriptor = NoDataSuccessDescriptor()
        return cls(
            message=message if message is not None else descriptor.message,
            description=(
                description if description is not None else descriptor.description
            ),
            metadata=metadata,
            other=other,
        )


class SingleDataResponse(
    SingleDataPayload[ModelDataT, ModelMetadataT],
    SingleDataSuccessDescriptor,
    SuccessResponse[ModelDataT, None, ModelMetadataT],
    Generic[ModelDataT, ModelMetadataT],
):
    pagination: None = None

    @classmethod
    def new(
        cls,
        *,
        message: OptStr = None,
        description: OptStr = None,
        data: ModelDataT,
        metadata: ModelMetadataT = None,
        other: Any = None,
    ) -> "SingleDataResponse[ModelDataT, ModelMetadataT]":
        descriptor = SingleDataSuccessDescriptor()
        return cls(
            message=message if message is not None else descriptor.message,
            description=(
                description if description is not None else descriptor.description
            ),
            data=data,
            metadata=metadata,
            other=other,
        )


class CreateSingleDataResponse(
    CreateSingleDataPayload[ModelDataT, ModelMetadataT],
    CreateSingleDataSuccessDescriptor,
    SuccessResponse[DataPair[None, ModelDataT], None, ModelMetadataT],
    Generic[ModelDataT, ModelMetadataT],
):
    pagination: None = None

    @classmethod
    def new(
        cls,
        *,
        message: OptStr = None,
        description: OptStr = None,
        data: ModelDataT,
        metadata: ModelMetadataT = None,
        other: Any = None,
    ) -> "CreateSingleDataResponse[ModelDataT, ModelMetadataT]":
        descriptor = CreateSingleDataSuccessDescriptor()
        return cls(
            message=message if message is not None else descriptor.message,
            description=(
                description if description is not None else descriptor.description
            ),
            data=DataPair[None, ModelDataT](
                old=None,
                new=data,
            ),
            metadata=metadata,
            other=other,
        )


class ReadSingleDataResponse(
    ReadSingleDataPayload[ModelDataT, ModelMetadataT],
    ReadSingleDataSuccessDescriptor,
    SuccessResponse[DataPair[ModelDataT, None], None, ModelMetadataT],
    Generic[ModelDataT, ModelMetadataT],
):
    pagination: None = None

    @classmethod
    def new(
        cls,
        *,
        message: OptStr = None,
        description: OptStr = None,
        data: ModelDataT,
        metadata: ModelMetadataT = None,
        other: Any = None,
    ) -> "ReadSingleDataResponse[ModelDataT, ModelMetadataT]":
        descriptor = ReadSingleDataSuccessDescriptor()
        return cls(
            message=message if message is not None else descriptor.message,
            description=(
                description if description is not None else descriptor.description
            ),
            data=DataPair[ModelDataT, None](
                old=data,
                new=None,
            ),
            metadata=metadata,
            other=other,
        )


class UpdateSingleDataResponse(
    UpdateSingleDataPayload[ModelDataT, ModelMetadataT],
    UpdateSingleDataSuccessDescriptor,
    SuccessResponse[DataPair[ModelDataT, ModelDataT], None, ModelMetadataT],
    Generic[ModelDataT, ModelMetadataT],
):
    pagination: None = None

    @classmethod
    def new(
        cls,
        *,
        message: OptStr = None,
        description: OptStr = None,
        old_data: ModelDataT,
        new_data: ModelDataT,
        metadata: ModelMetadataT = None,
        other: Any = None,
    ) -> "UpdateSingleDataResponse[ModelDataT, ModelMetadataT]":
        descriptor = UpdateSingleDataSuccessDescriptor()
        return cls(
            message=message if message is not None else descriptor.message,
            description=(
                description if description is not None else descriptor.description
            ),
            data=DataPair[ModelDataT, ModelDataT](
                old=old_data,
                new=new_data,
            ),
            metadata=metadata,
            other=other,
        )


class DeleteSingleDataResponse(
    DeleteSingleDataPayload[ModelDataT, ModelMetadataT],
    DeleteSingleDataSuccessDescriptor,
    SuccessResponse[DataPair[ModelDataT, None], None, ModelMetadataT],
    Generic[ModelDataT, ModelMetadataT],
):
    pagination: None = None

    @classmethod
    def new(
        cls,
        *,
        message: OptStr = None,
        description: OptStr = None,
        data: ModelDataT,
        metadata: ModelMetadataT = None,
        other: Any = None,
    ) -> "DeleteSingleDataResponse[ModelDataT, ModelMetadataT]":
        descriptor = DeleteSingleDataSuccessDescriptor()
        return cls(
            message=message if message is not None else descriptor.message,
            description=(
                description if description is not None else descriptor.description
            ),
            data=DataPair[ModelDataT, None](
                old=data,
                new=None,
            ),
            metadata=metadata,
            other=other,
        )


class OptSingleDataResponse(
    OptSingleDataPayload[ModelDataT, ModelMetadataT],
    OptSingleDataSuccessDescriptor,
    SuccessResponse[ModelDataT | None, None, ModelMetadataT],
    Generic[ModelDataT, ModelMetadataT],
):
    pagination: None = None

    @classmethod
    def new(
        cls,
        *,
        message: OptStr = None,
        description: OptStr = None,
        data: ModelDataT | None = None,
        metadata: ModelMetadataT = None,
        other: Any = None,
    ) -> "OptSingleDataResponse[ModelDataT, ModelMetadataT]":
        descriptor = OptSingleDataSuccessDescriptor()
        return cls(
            message=message if message is not None else descriptor.message,
            description=(
                description if description is not None else descriptor.description
            ),
            data=data,
            metadata=metadata,
            other=other,
        )


class MultipleDataResponse(
    MultipleDataPayload[ModelDataT, PaginationT, ModelMetadataT],
    MultipleDataSuccessDescriptor,
    SuccessResponse[list[ModelDataT], PaginationT, ModelMetadataT],
    Generic[ModelDataT, PaginationT, ModelMetadataT],
):
    @classmethod
    def new(
        cls,
        *,
        message: OptStr = None,
        description: OptStr = None,
        data: list[ModelDataT],
        pagination: PaginationT,
        metadata: ModelMetadataT = None,
        other: Any = None,
    ) -> "MultipleDataResponse[ModelDataT, PaginationT, ModelMetadataT]":
        descriptor = MultipleDataSuccessDescriptor()
        return cls(
            message=message if message is not None else descriptor.message,
            description=(
                description if description is not None else descriptor.description
            ),
            data=data,
            pagination=pagination,
            metadata=metadata,
            other=other,
        )


class CreateMultipleDataResponse(
    CreateMultipleDataPayload[ModelDataT, PaginationT, ModelMetadataT],
    CreateMultipleDataSuccessDescriptor,
    SuccessResponse[DataPair[None, list[ModelDataT]], PaginationT, ModelMetadataT],
    Generic[ModelDataT, PaginationT, ModelMetadataT],
):
    @classmethod
    def new(
        cls,
        *,
        message: OptStr = None,
        description: OptStr = None,
        data: list[ModelDataT],
        pagination: PaginationT,
        metadata: ModelMetadataT = None,
        other: Any = None,
    ) -> "CreateMultipleDataResponse[ModelDataT, PaginationT, ModelMetadataT]":
        descriptor = CreateMultipleDataSuccessDescriptor()
        return cls(
            message=message if message is not None else descriptor.message,
            description=(
                description if description is not None else descriptor.description
            ),
            data=DataPair[None, list[ModelDataT]](
                old=None,
                new=data,
            ),
            pagination=pagination,
            metadata=metadata,
            other=other,
        )


class ReadMultipleDataResponse(
    ReadMultipleDataPayload[ModelDataT, PaginationT, ModelMetadataT],
    ReadMultipleDataSuccessDescriptor,
    SuccessResponse[DataPair[list[ModelDataT], None], PaginationT, ModelMetadataT],
    Generic[ModelDataT, PaginationT, ModelMetadataT],
):
    @classmethod
    def new(
        cls,
        *,
        message: OptStr = None,
        description: OptStr = None,
        data: list[ModelDataT],
        pagination: PaginationT,
        metadata: ModelMetadataT = None,
        other: Any = None,
    ) -> "ReadMultipleDataResponse[ModelDataT, PaginationT, ModelMetadataT]":
        descriptor = ReadMultipleDataSuccessDescriptor()
        return cls(
            message=message if message is not None else descriptor.message,
            description=(
                description if description is not None else descriptor.description
            ),
            data=DataPair[list[ModelDataT], None](
                old=data,
                new=None,
            ),
            pagination=pagination,
            metadata=metadata,
            other=other,
        )


class UpdateMultipleDataResponse(
    UpdateMultipleDataPayload[ModelDataT, PaginationT, ModelMetadataT],
    UpdateMultipleDataSuccessDescriptor,
    SuccessResponse[
        DataPair[list[ModelDataT], list[ModelDataT]], PaginationT, ModelMetadataT
    ],
    Generic[ModelDataT, PaginationT, ModelMetadataT],
):
    @classmethod
    def new(
        cls,
        *,
        message: OptStr = None,
        description: OptStr = None,
        old_data: list[ModelDataT],
        new_data: list[ModelDataT],
        pagination: PaginationT,
        metadata: ModelMetadataT = None,
        other: Any = None,
    ) -> "UpdateMultipleDataResponse[ModelDataT, PaginationT, ModelMetadataT]":
        descriptor = UpdateMultipleDataSuccessDescriptor()
        return cls(
            message=message if message is not None else descriptor.message,
            description=(
                description if description is not None else descriptor.description
            ),
            data=DataPair[list[ModelDataT], list[ModelDataT]](
                old=old_data,
                new=new_data,
            ),
            pagination=pagination,
            metadata=metadata,
            other=other,
        )


class DeleteMultipleDataResponse(
    DeleteMultipleDataPayload[ModelDataT, PaginationT, ModelMetadataT],
    DeleteMultipleDataSuccessDescriptor,
    SuccessResponse[DataPair[list[ModelDataT], None], PaginationT, ModelMetadataT],
    Generic[ModelDataT, PaginationT, ModelMetadataT],
):
    @classmethod
    def new(
        cls,
        *,
        message: OptStr = None,
        description: OptStr = None,
        data: list[ModelDataT],
        pagination: PaginationT,
        metadata: ModelMetadataT = None,
        other: Any = None,
    ) -> "DeleteMultipleDataResponse[ModelDataT, PaginationT, ModelMetadataT]":
        descriptor = DeleteMultipleDataSuccessDescriptor()
        return cls(
            message=message if message is not None else descriptor.message,
            description=(
                description if description is not None else descriptor.description
            ),
            data=DataPair[list[ModelDataT], None](
                old=data,
                new=None,
            ),
            pagination=pagination,
            metadata=metadata,
            other=other,
        )


class OptMultipleDataResponse(
    OptMultipleDataPayload[ModelDataT, PaginationT, ModelMetadataT],
    OptMultipleDataSuccessDescriptor,
    SuccessResponse[list[ModelDataT] | None, PaginationT, ModelMetadataT],
    Generic[ModelDataT, PaginationT, ModelMetadataT],
):
    @classmethod
    def new(
        cls,
        *,
        message: OptStr = None,
        description: OptStr = None,
        data: list[ModelDataT] | None = None,
        pagination: PaginationT,
        metadata: ModelMetadataT = None,
        other: Any = None,
    ) -> "OptMultipleDataResponse[ModelDataT, PaginationT, ModelMetadataT]":
        descriptor = OptMultipleDataSuccessDescriptor()
        return cls(
            message=message if message is not None else descriptor.message,
            description=(
                description if description is not None else descriptor.description
            ),
            data=data,
            pagination=pagination,
            metadata=metadata,
            other=other,
        )


AnySuccessResponse = (
    AnyDataResponse[ModelDataT, OptPaginationT, ModelMetadataT]
    | NoDataResponse[ModelMetadataT]
    | SingleDataResponse[ModelDataT, ModelMetadataT]
    | CreateSingleDataResponse[ModelDataT, ModelMetadataT]
    | ReadSingleDataResponse[ModelDataT, ModelMetadataT]
    | UpdateSingleDataResponse[ModelDataT, ModelMetadataT]
    | DeleteSingleDataResponse[ModelDataT, ModelMetadataT]
    | OptSingleDataResponse[ModelDataT, ModelMetadataT]
    | MultipleDataResponse[ModelDataT, PaginationT, ModelMetadataT]
    | CreateMultipleDataResponse[ModelDataT, PaginationT, ModelMetadataT]
    | ReadMultipleDataResponse[ModelDataT, PaginationT, ModelMetadataT]
    | UpdateMultipleDataResponse[ModelDataT, PaginationT, ModelMetadataT]
    | DeleteMultipleDataResponse[ModelDataT, PaginationT, ModelMetadataT]
    | OptMultipleDataResponse[ModelDataT, PaginationT, ModelMetadataT]
)
SuccessResponseT = TypeVar("SuccessResponseT", bound=AnySuccessResponse)


AnyResponse = AnyErrorResponse | AnySuccessResponse
ResponseT = TypeVar("ResponseT", bound=AnyResponse)


class ResponseMixin(BaseModel, Generic[ResponseT]):
    response: ResponseT = Field(..., description="Response")

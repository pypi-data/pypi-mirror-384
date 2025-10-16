import traceback as tb
from fastapi.responses import JSONResponse
from typing import Any, Generic, Literal, Type, overload
from uuid import uuid4
from maleo.types.string import ListOfStrs, OptStr
from maleo.types.uuid import OptUUID
from ..application import ApplicationContext, OptApplicationContext
from ..connection import ConnectionContext, OptConnectionContext
from ..error.enums import ErrorCode
from ..error.metadata import ErrorMetadata
from ..error import (
    BadRequestError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    MethodNotAllowedError,
    ConflictError,
    UnprocessableEntityError,
    TooManyRequestsError,
    InternalServerError as InternalServerErrorSchema,
    NotImplementedError,
    BadGatewayError,
    ServiceUnavailableError,
    AnyErrorT,
)
from ..operation.action.resource import (
    ResourceOperationActions,
    AnyResourceOperationAction,
)
from ..operation.action.system import SystemOperationAction
from ..operation.action.websocket import WebSocketOperationAction
from ..operation.context import Context
from ..operation.enums import OperationType
from ..operation.mixins import Timestamp, OptTimestamp
from ..operation.request import (
    CreateFailedRequestOperation,
    ReadFailedRequestOperation,
    UpdateFailedRequestOperation,
    DeleteFailedRequestOperation,
    FailedFactory as FailedRequestOperationFactory,
)
from ..operation.resource import (
    CreateFailedResourceOperation,
    ReadFailedResourceOperation,
    UpdateFailedResourceOperation,
    DeleteFailedResourceOperation,
    FailedFactory as FailedResourceOperationFactory,
)
from ..operation.system import FailedSystemOperation
from ..operation.websocket import FailedWebSocketOperation
from ..resource import Resource, OptResource
from ..response import (
    BadRequestResponse,
    UnauthorizedResponse,
    ForbiddenResponse,
    NotFoundResponse,
    MethodNotAllowedResponse,
    ConflictResponse,
    UnprocessableEntityResponse,
    TooManyRequestsResponse,
    InternalServerErrorResponse,
    NotImplementedResponse,
    BadGatewayResponse,
    ServiceUnavailableResponse,
    OptAnyErrorResponse,
    ErrorResponseT,
    ResponseContext,
)
from ..security.authentication import OptAnyAuthentication
from ..security.authorization import OptAnyAuthorization
from ..security.impersonation import OptImpersonation


class MaleoException(
    Exception,
    Generic[
        AnyErrorT,
        ErrorResponseT,
    ],
):
    error_cls: Type[AnyErrorT]
    response_cls: Type[ErrorResponseT]

    @overload
    def __init__(
        self,
        *args: object,
        details: Any = None,
        operation_type: Literal[OperationType.REQUEST],
        application_context: OptApplicationContext = None,
        operation_id: OptUUID = None,
        operation_context: Context,
        operation_action: AnyResourceOperationAction,
        operation_timestamp: OptTimestamp = None,
        operation_summary: OptStr = None,
        connection_context: ConnectionContext,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: OptAnyErrorResponse = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        *args: object,
        details: Any = None,
        operation_type: Literal[OperationType.RESOURCE],
        application_context: OptApplicationContext = None,
        operation_id: OptUUID = None,
        operation_context: Context,
        operation_action: AnyResourceOperationAction,
        resource: Resource,
        operation_timestamp: OptTimestamp = None,
        operation_summary: OptStr = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: OptAnyErrorResponse = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        *args: object,
        details: Any = None,
        operation_type: Literal[OperationType.REQUEST, OperationType.RESOURCE],
        application_context: OptApplicationContext = None,
        operation_id: OptUUID = None,
        operation_context: Context,
        operation_action: AnyResourceOperationAction,
        resource: OptResource = None,
        operation_timestamp: OptTimestamp = None,
        operation_summary: OptStr = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: OptAnyErrorResponse = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        *args: object,
        details: Any = None,
        operation_type: Literal[OperationType.SYSTEM],
        application_context: OptApplicationContext = None,
        operation_id: OptUUID = None,
        operation_context: Context,
        operation_action: SystemOperationAction,
        operation_timestamp: OptTimestamp = None,
        operation_summary: OptStr = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: OptAnyErrorResponse = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        *args: object,
        details: Any = None,
        operation_type: Literal[OperationType.WEBSOCKET],
        application_context: OptApplicationContext = None,
        operation_id: OptUUID = None,
        operation_context: Context,
        operation_action: WebSocketOperationAction,
        operation_timestamp: OptTimestamp = None,
        operation_summary: OptStr = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: OptAnyErrorResponse = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        *args: object,
        details: Any = None,
        operation_type: OperationType,
        application_context: OptApplicationContext = None,
        operation_id: OptUUID = None,
        operation_context: Context,
        operation_action: (
            AnyResourceOperationAction
            | SystemOperationAction
            | WebSocketOperationAction
        ),
        resource: OptResource = None,
        operation_timestamp: OptTimestamp = None,
        operation_summary: OptStr = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: OptAnyErrorResponse = None,
    ) -> None: ...
    def __init__(
        self,
        *args: object,
        details: Any = None,
        operation_type: OperationType,
        application_context: OptApplicationContext = None,
        operation_id: OptUUID = None,
        operation_context: Context,
        operation_action: (
            AnyResourceOperationAction
            | SystemOperationAction
            | WebSocketOperationAction
        ),
        resource: OptResource = None,
        operation_timestamp: OptTimestamp = None,
        operation_summary: OptStr = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: OptAnyErrorResponse = None,
    ) -> None:
        super().__init__(*args)
        self.details = details
        self.operation_type = operation_type

        self.application_context = (
            application_context
            if application_context is not None
            else ApplicationContext.from_env()
        )

        self.operation_id = operation_id if operation_id is not None else uuid4()
        self.operation_context = operation_context
        self.operation_action = operation_action
        self.resource = resource

        self.operation_timestamp = (
            operation_timestamp if operation_timestamp is not None else Timestamp.now()
        )

        self.operation_summary = (
            operation_summary
            if operation_summary is not None
            else f"{self.operation_type.capitalize()} operation failed due to exception being raised"
        )

        self.connection_context = connection_context
        self.authentication = authentication
        self.authorization = authorization
        self.impersonation = impersonation

        if response is not None:
            self.response: ErrorResponseT = self.response_cls.model_validate(
                response.model_dump()
            )
            if self.response.other is None and self.details is not None:
                self.response.other = self.details
        else:
            self.response: ErrorResponseT = self.response_cls(other=self.details)

        self.error: AnyErrorT = self.error_cls(
            metadata=ErrorMetadata(details=self.details, traceback=self.traceback)
        )

    @property
    def traceback(self) -> ListOfStrs:
        return tb.format_exception(self)

    @property
    def operation(self) -> (
        CreateFailedRequestOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
        | ReadFailedRequestOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
        | UpdateFailedRequestOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
        | DeleteFailedRequestOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
        | CreateFailedResourceOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
        | ReadFailedResourceOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
        | UpdateFailedResourceOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
        | DeleteFailedResourceOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
        | FailedSystemOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
        | FailedWebSocketOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
    ):
        if self.operation_type is OperationType.REQUEST:
            if not isinstance(self.operation_action, ResourceOperationActions):
                raise ValueError(
                    ErrorCode.BAD_REQUEST,
                    f"Invalid operation_action to generate request operation: {type(self.operation_action)}",
                )
            if self.connection_context is None:
                raise ValueError(
                    ErrorCode.BAD_REQUEST,
                    "Failed generating request operation from MaleoException. Request context is not given",
                )
            response = JSONResponse(
                content=self.response.model_dump(mode="json"),
                status_code=self.error.spec.status_code,
            )
            response_context = ResponseContext(
                status_code=response.status_code,
                media_type=response.media_type,
                headers=response.headers.items(),
            )

            return FailedRequestOperationFactory[
                AnyErrorT,
                ErrorResponseT,
            ].generate(
                self.operation_action,
                application_context=self.application_context,
                id=self.operation_id,
                context=self.operation_context,
                timestamp=self.operation_timestamp,
                summary=self.operation_summary,
                error=self.error,
                connection_context=self.connection_context,
                authentication=self.authentication,
                authorization=self.authorization,
                impersonation=self.impersonation,
                response=self.response,
                response_context=response_context,
            )
        elif self.operation_type is OperationType.RESOURCE:
            if not isinstance(self.operation_action, ResourceOperationActions):
                raise ValueError(
                    ErrorCode.BAD_REQUEST,
                    f"Invalid operation_action to generate resource operation: {type(self.operation_action)}",
                )
            if self.resource is None:
                raise ValueError(
                    ErrorCode.BAD_REQUEST,
                    "Failed generating resource operation from MaleoException. Resource is not given",
                )
            return FailedResourceOperationFactory[
                AnyErrorT,
                ErrorResponseT,
            ].generate(
                self.operation_action,
                application_context=self.application_context,
                id=self.operation_id,
                context=self.operation_context,
                timestamp=self.operation_timestamp,
                summary=self.operation_summary,
                error=self.error,
                connection_context=self.connection_context,
                authentication=self.authentication,
                authorization=self.authorization,
                impersonation=self.impersonation,
                resource=self.resource,
                response=self.response,
            )
        elif self.operation_type is OperationType.SYSTEM:
            if not isinstance(self.operation_action, SystemOperationAction):
                raise ValueError(
                    ErrorCode.BAD_REQUEST,
                    f"Invalid operation_action to generate system operation: {type(self.operation_action)}",
                )
            return FailedSystemOperation[
                AnyErrorT,
                ErrorResponseT,
            ](
                application_context=self.application_context,
                id=self.operation_id,
                context=self.operation_context,
                action=self.operation_action,
                timestamp=self.operation_timestamp,
                summary=self.operation_summary,
                error=self.error,
                connection_context=self.connection_context,
                authentication=self.authentication,
                authorization=self.authorization,
                impersonation=self.impersonation,
                response=self.response,
            )
        elif self.operation_type is OperationType.WEBSOCKET:
            if not isinstance(self.operation_action, WebSocketOperationAction):
                raise ValueError(
                    ErrorCode.BAD_REQUEST,
                    f"Invalid operation_action to generate websocket operation: {type(self.operation_action)}",
                )
            return FailedWebSocketOperation[
                AnyErrorT,
                ErrorResponseT,
            ](
                application_context=self.application_context,
                id=self.operation_id,
                context=self.operation_context,
                action=self.operation_action,
                timestamp=self.operation_timestamp,
                summary=self.operation_summary,
                error=self.error,
                connection_context=self.connection_context,
                authentication=self.authentication,
                authorization=self.authorization,
                impersonation=self.impersonation,
                response=self.response,
            )

        raise ValueError(
            ErrorCode.BAD_REQUEST,
            f"Invalid operation_type to generate any operation from maleo exception: {self.operation_type}",
        )

    @overload
    def generate_operation(
        self,
        operation_type: Literal[OperationType.REQUEST],
        /,
    ) -> (
        CreateFailedRequestOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
        | ReadFailedRequestOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
        | UpdateFailedRequestOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
        | DeleteFailedRequestOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
    ): ...
    @overload
    def generate_operation(
        self,
        operation_type: Literal[OperationType.RESOURCE],
        /,
    ) -> (
        CreateFailedResourceOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
        | ReadFailedResourceOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
        | UpdateFailedResourceOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
        | DeleteFailedResourceOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
    ): ...
    @overload
    def generate_operation(
        self,
        operation_type: Literal[OperationType.SYSTEM],
        /,
    ) -> FailedSystemOperation[AnyErrorT, ErrorResponseT]: ...
    @overload
    def generate_operation(
        self,
        operation_type: Literal[OperationType.WEBSOCKET],
        /,
    ) -> FailedWebSocketOperation[AnyErrorT, ErrorResponseT]: ...
    def generate_operation(
        self,
        operation_type: OperationType,
        /,
    ) -> (
        CreateFailedRequestOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
        | ReadFailedRequestOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
        | UpdateFailedRequestOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
        | DeleteFailedRequestOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
        | CreateFailedResourceOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
        | ReadFailedResourceOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
        | UpdateFailedResourceOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
        | DeleteFailedResourceOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
        | FailedSystemOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
        | FailedWebSocketOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
    ):
        if operation_type != self.operation_type:
            raise ValueError(
                ErrorCode.INTERNAL_SERVER_ERROR,
                (
                    "Failed generating operation for MaleoException ",
                    "due to mismatched operation_type. ",
                    f"Expected '{self.operation_type}' ",
                    f"but received {operation_type}",
                ),
            )

        if operation_type is OperationType.SYSTEM:
            if not isinstance(self.operation_action, SystemOperationAction):
                raise ValueError(
                    ErrorCode.BAD_REQUEST,
                    f"Invalid operation_action to generate system operation: {type(self.operation_action)}",
                )
            return FailedSystemOperation[
                AnyErrorT,
                ErrorResponseT,
            ](
                application_context=self.application_context,
                id=self.operation_id,
                context=self.operation_context,
                action=self.operation_action,
                timestamp=self.operation_timestamp,
                summary=self.operation_summary,
                error=self.error,
                connection_context=self.connection_context,
                authentication=self.authentication,
                authorization=self.authorization,
                impersonation=self.impersonation,
                response=self.response,
            )
        elif operation_type is OperationType.WEBSOCKET:
            if not isinstance(self.operation_action, WebSocketOperationAction):
                raise ValueError(
                    ErrorCode.BAD_REQUEST,
                    f"Invalid operation_action to generate websocket operation: {type(self.operation_action)}",
                )
            return FailedWebSocketOperation[
                AnyErrorT,
                ErrorResponseT,
            ](
                application_context=self.application_context,
                id=self.operation_id,
                context=self.operation_context,
                action=self.operation_action,
                timestamp=self.operation_timestamp,
                summary=self.operation_summary,
                error=self.error,
                connection_context=self.connection_context,
                authentication=self.authentication,
                authorization=self.authorization,
                impersonation=self.impersonation,
                response=self.response,
            )
        else:
            if not isinstance(self.operation_action, ResourceOperationActions):
                raise ValueError(
                    ErrorCode.BAD_REQUEST,
                    f"Invalid operation_action to generate {operation_type} operation: {type(self.operation_action)}",
                )

            if operation_type is OperationType.REQUEST:
                if self.connection_context is None:
                    raise ValueError(
                        ErrorCode.BAD_REQUEST,
                        "Failed generating request operation from MaleoException. Request context is not given",
                    )
                response = JSONResponse(
                    content=self.response.model_dump(mode="json"),
                    status_code=self.error.spec.status_code,
                )
                response_context = ResponseContext(
                    status_code=response.status_code,
                    media_type=response.media_type,
                    headers=response.headers.items(),
                )

                return FailedRequestOperationFactory[
                    AnyErrorT,
                    ErrorResponseT,
                ].generate(
                    self.operation_action,
                    application_context=self.application_context,
                    id=self.operation_id,
                    context=self.operation_context,
                    timestamp=self.operation_timestamp,
                    summary=self.operation_summary,
                    error=self.error,
                    connection_context=self.connection_context,
                    authentication=self.authentication,
                    authorization=self.authorization,
                    impersonation=self.impersonation,
                    response=self.response,
                    response_context=response_context,
                )
            elif operation_type is OperationType.RESOURCE:
                if self.resource is None:
                    raise ValueError(
                        ErrorCode.BAD_REQUEST,
                        "Failed generating resource operation from MaleoException. Resource is not given",
                    )
                return FailedResourceOperationFactory[
                    AnyErrorT,
                    ErrorResponseT,
                ].generate(
                    self.operation_action,
                    application_context=self.application_context,
                    id=self.operation_id,
                    context=self.operation_context,
                    timestamp=self.operation_timestamp,
                    summary=self.operation_summary,
                    error=self.error,
                    connection_context=self.connection_context,
                    authentication=self.authentication,
                    authorization=self.authorization,
                    impersonation=self.impersonation,
                    resource=self.resource,
                    response=self.response,
                )


class ClientException(
    MaleoException[
        AnyErrorT,
        ErrorResponseT,
    ],
    Generic[
        AnyErrorT,
        ErrorResponseT,
    ],
):
    """Base class for all client error (HTTP 4xx) responses"""


class BadRequest(
    ClientException[
        BadRequestError,
        BadRequestResponse,
    ]
):
    error_cls = BadRequestError
    response_cls = BadRequestResponse


class Unauthorized(
    ClientException[
        UnauthorizedError,
        UnauthorizedResponse,
    ]
):
    error_cls = UnauthorizedError
    response_cls = UnauthorizedResponse


class Forbidden(
    ClientException[
        ForbiddenError,
        ForbiddenResponse,
    ]
):
    error_cls = ForbiddenError
    response_cls = ForbiddenResponse


class NotFound(
    ClientException[
        NotFoundError,
        NotFoundResponse,
    ]
):
    error_cls = NotFoundError
    response_cls = NotFoundResponse


class MethodNotAllowed(
    ClientException[
        MethodNotAllowedError,
        MethodNotAllowedResponse,
    ]
):
    error_cls = MethodNotAllowedError
    response_cls = MethodNotAllowedResponse


class Conflict(
    ClientException[
        ConflictError,
        ConflictResponse,
    ]
):
    error_cls = ConflictError
    response_cls = ConflictResponse


class UnprocessableEntity(
    ClientException[
        UnprocessableEntityError,
        UnprocessableEntityResponse,
    ]
):
    error_cls = UnprocessableEntityError
    response_cls = UnprocessableEntityResponse


class TooManyRequests(
    ClientException[
        TooManyRequestsError,
        TooManyRequestsResponse,
    ]
):
    error_cls = TooManyRequestsError
    response_cls = TooManyRequestsResponse


class ServerException(
    MaleoException[
        AnyErrorT,
        ErrorResponseT,
    ],
    Generic[
        AnyErrorT,
        ErrorResponseT,
    ],
):
    """Base class for all server error (HTTP 5xx) responses"""


class InternalServerError(
    ServerException[
        InternalServerErrorSchema,
        InternalServerErrorResponse,
    ]
):
    error_cls = InternalServerErrorSchema
    response_cls = InternalServerErrorResponse


class NotImplemented(
    ServerException[
        NotImplementedError,
        NotImplementedResponse,
    ]
):
    error_cls = NotImplementedError
    response_cls = NotImplementedResponse


class BadGateway(
    ServerException[
        BadGatewayError,
        BadGatewayResponse,
    ]
):
    error_cls = BadGatewayError
    response_cls = BadGatewayResponse


class ServiceUnavailable(
    ServerException[
        ServiceUnavailableError,
        ServiceUnavailableResponse,
    ]
):
    error_cls = ServiceUnavailableError
    response_cls = ServiceUnavailableResponse


AnyExceptionType = (
    Type[BadRequest]
    | Type[Unauthorized]
    | Type[Forbidden]
    | Type[NotFound]
    | Type[MethodNotAllowed]
    | Type[Conflict]
    | Type[UnprocessableEntity]
    | Type[TooManyRequests]
    | Type[InternalServerError]
    | Type[NotImplemented]
    | Type[BadGateway]
    | Type[ServiceUnavailable]
)
AnyException = (
    BadRequest
    | Unauthorized
    | Forbidden
    | NotFound
    | MethodNotAllowed
    | Conflict
    | UnprocessableEntity
    | TooManyRequests
    | InternalServerError
    | NotImplemented
    | BadGateway
    | ServiceUnavailable
)

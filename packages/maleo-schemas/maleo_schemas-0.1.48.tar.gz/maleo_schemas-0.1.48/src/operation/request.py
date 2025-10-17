from copy import deepcopy
from typing import Any, Generic, Literal, Type, overload
from uuid import UUID
from maleo.types.boolean import BoolT
from ..application import ApplicationContext
from ..connection import ConnectionContext
from ..error import OptAnyErrorT, AnyErrorT
from ..pagination import OptAnyPagination
from ..response import (
    ResponseContext,
    ResponseT,
    ErrorResponseT,
    AnyDataResponse,
)
from ..security.authentication import OptAnyAuthentication
from ..security.authorization import OptAnyAuthorization
from ..security.impersonation import OptImpersonation
from .action.resource import (
    AnyResourceOperationActionT,
    CreateResourceOperationAction,
    ReadResourceOperationAction,
    UpdateResourceOperationAction,
    DeleteResourceOperationAction,
    ResourceOperationActions,
    AnyResourceOperationAction,
    OptAnyResourceOperationAction,
    Factory as ResourceOperationActionFactory,
)
from .base import BaseOperation
from .context import Context as OperationContext
from .enums import (
    OperationType,
    ResourceOperationType,
    OptResourceOperationType,
    OptResourceOperationCreateType,
    OptResourceOperationUpdateType,
    OptResourceOperationDataUpdateType,
    OptResourceOperationStatusUpdateType,
)
from .mixins import Timestamp


class RequestOperation(
    BaseOperation[
        AnyResourceOperationActionT,
        None,
        BoolT,
        OptAnyErrorT,
        ConnectionContext,
        ResponseT,
        ResponseContext,
    ],
    Generic[
        AnyResourceOperationActionT,
        BoolT,
        OptAnyErrorT,
        ResponseT,
    ],
):
    type: OperationType = OperationType.REQUEST
    resource: None = None


class FailedRequestOperation(
    RequestOperation[
        AnyResourceOperationActionT,
        Literal[False],
        AnyErrorT,
        ErrorResponseT,
    ],
    Generic[
        AnyResourceOperationActionT,
        AnyErrorT,
        ErrorResponseT,
    ],
):
    success: Literal[False] = False
    summary: str = "Failed processing request"


class CreateFailedRequestOperation(
    FailedRequestOperation[
        CreateResourceOperationAction,
        AnyErrorT,
        ErrorResponseT,
    ],
    Generic[
        AnyErrorT,
        ErrorResponseT,
    ],
):
    pass


class ReadFailedRequestOperation(
    FailedRequestOperation[
        ReadResourceOperationAction,
        AnyErrorT,
        ErrorResponseT,
    ],
    Generic[
        AnyErrorT,
        ErrorResponseT,
    ],
):
    pass


class UpdateFailedRequestOperation(
    FailedRequestOperation[
        UpdateResourceOperationAction,
        AnyErrorT,
        ErrorResponseT,
    ],
    Generic[
        AnyErrorT,
        ErrorResponseT,
    ],
):
    pass


class DeleteFailedRequestOperation(
    FailedRequestOperation[
        DeleteResourceOperationAction,
        AnyErrorT,
        ErrorResponseT,
    ],
    Generic[
        AnyErrorT,
        ErrorResponseT,
    ],
):
    pass


class SuccessfulRequestOperation(
    RequestOperation[
        AnyResourceOperationActionT,
        Literal[True],
        None,
        AnyDataResponse[Any, OptAnyPagination, Any],
    ],
    Generic[AnyResourceOperationActionT],
):
    success: Literal[True] = True
    error: None = None
    summary: str = "Successfully processed request"


class CreateSuccessfulRequestOperation(
    SuccessfulRequestOperation[CreateResourceOperationAction]
):
    pass


class ReadSuccessfulRequestOperation(
    SuccessfulRequestOperation[ReadResourceOperationAction]
):
    pass


class UpdateSuccessfulRequestOperation(
    SuccessfulRequestOperation[UpdateResourceOperationAction]
):
    pass


class DeleteSuccessfulRequestOperation(
    SuccessfulRequestOperation[DeleteResourceOperationAction]
):
    pass


AnySuccessfulRequestOperationType = (
    Type[CreateSuccessfulRequestOperation]
    | Type[ReadSuccessfulRequestOperation]
    | Type[UpdateSuccessfulRequestOperation]
    | Type[DeleteSuccessfulRequestOperation]
)


AnySuccessfulRequestOperation = (
    CreateSuccessfulRequestOperation
    | ReadSuccessfulRequestOperation
    | UpdateSuccessfulRequestOperation
    | DeleteSuccessfulRequestOperation
)


class FailedFactory(Generic[AnyErrorT, ErrorResponseT]):
    @overload
    @classmethod
    def operation_cls_from_action(cls, action: CreateResourceOperationAction) -> Type[
        CreateFailedRequestOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
    ]: ...
    @overload
    @classmethod
    def operation_cls_from_action(cls, action: ReadResourceOperationAction) -> Type[
        ReadFailedRequestOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
    ]: ...
    @overload
    @classmethod
    def operation_cls_from_action(cls, action: UpdateResourceOperationAction) -> Type[
        UpdateFailedRequestOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
    ]: ...
    @overload
    @classmethod
    def operation_cls_from_action(cls, action: DeleteResourceOperationAction) -> Type[
        DeleteFailedRequestOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
    ]: ...
    @overload
    @classmethod
    def operation_cls_from_action(cls, action: AnyResourceOperationAction) -> (
        Type[
            CreateFailedRequestOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        ]
        | Type[
            ReadFailedRequestOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        ]
        | Type[
            UpdateFailedRequestOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        ]
        | Type[
            DeleteFailedRequestOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        ]
    ): ...
    @classmethod
    def operation_cls_from_action(cls, action: AnyResourceOperationAction) -> (
        Type[
            CreateFailedRequestOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        ]
        | Type[
            ReadFailedRequestOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        ]
        | Type[
            UpdateFailedRequestOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        ]
        | Type[
            DeleteFailedRequestOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        ]
    ):
        if isinstance(action, CreateResourceOperationAction):
            operation_cls = CreateFailedRequestOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        elif isinstance(action, ReadResourceOperationAction):
            operation_cls = ReadFailedRequestOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        elif isinstance(action, UpdateResourceOperationAction):
            operation_cls = UpdateFailedRequestOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        elif isinstance(action, DeleteResourceOperationAction):
            operation_cls = DeleteFailedRequestOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        return operation_cls

    @overload
    @classmethod
    def operation_cls_from_type(
        cls,
        type_: Literal[ResourceOperationType.CREATE],
    ) -> Type[
        CreateFailedRequestOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
    ]: ...
    @overload
    @classmethod
    def operation_cls_from_type(
        cls,
        type_: Literal[ResourceOperationType.READ],
    ) -> Type[
        ReadFailedRequestOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
    ]: ...
    @overload
    @classmethod
    def operation_cls_from_type(
        cls,
        type_: Literal[ResourceOperationType.UPDATE],
    ) -> Type[
        UpdateFailedRequestOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
    ]: ...
    @overload
    @classmethod
    def operation_cls_from_type(
        cls,
        type_: Literal[ResourceOperationType.DELETE],
    ) -> Type[
        DeleteFailedRequestOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
    ]: ...
    @classmethod
    def operation_cls_from_type(
        cls,
        type_: ResourceOperationType,
    ) -> (
        Type[
            CreateFailedRequestOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        ]
        | Type[
            ReadFailedRequestOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        ]
        | Type[
            UpdateFailedRequestOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        ]
        | Type[
            DeleteFailedRequestOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        ]
    ):
        if type_ is ResourceOperationType.CREATE:
            operation_cls = CreateFailedRequestOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        elif type_ is ResourceOperationType.READ:
            operation_cls = ReadFailedRequestOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        elif type_ is ResourceOperationType.UPDATE:
            operation_cls = UpdateFailedRequestOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        elif type_ is ResourceOperationType.DELETE:
            operation_cls = DeleteFailedRequestOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        return operation_cls

    @overload
    @classmethod
    def generate(
        cls,
        action: CreateResourceOperationAction,
        *,
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        timestamp: Timestamp,
        summary: str,
        error: AnyErrorT,
        connection_context: ConnectionContext,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: ErrorResponseT,
        response_context: ResponseContext,
    ) -> CreateFailedRequestOperation[AnyErrorT, ErrorResponseT]: ...
    @overload
    @classmethod
    def generate(
        cls,
        action: ReadResourceOperationAction,
        *,
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        timestamp: Timestamp,
        summary: str,
        error: AnyErrorT,
        connection_context: ConnectionContext,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: ErrorResponseT,
        response_context: ResponseContext,
    ) -> ReadFailedRequestOperation[AnyErrorT, ErrorResponseT]: ...
    @overload
    @classmethod
    def generate(
        cls,
        action: UpdateResourceOperationAction,
        *,
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        timestamp: Timestamp,
        summary: str,
        error: AnyErrorT,
        connection_context: ConnectionContext,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: ErrorResponseT,
        response_context: ResponseContext,
    ) -> UpdateFailedRequestOperation[AnyErrorT, ErrorResponseT]: ...
    @overload
    @classmethod
    def generate(
        cls,
        action: DeleteResourceOperationAction,
        *,
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        timestamp: Timestamp,
        summary: str,
        error: AnyErrorT,
        connection_context: ConnectionContext,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: ErrorResponseT,
        response_context: ResponseContext,
    ) -> DeleteFailedRequestOperation[AnyErrorT, ErrorResponseT]: ...
    @overload
    @classmethod
    def generate(
        cls,
        action: AnyResourceOperationAction,
        *,
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        timestamp: Timestamp,
        summary: str,
        error: AnyErrorT,
        connection_context: ConnectionContext,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: ErrorResponseT,
        response_context: ResponseContext,
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
    @classmethod
    def generate(
        cls,
        *,
        type_: Literal[ResourceOperationType.CREATE],
        create_type: OptResourceOperationCreateType = ...,
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        timestamp: Timestamp,
        summary: str,
        error: AnyErrorT,
        connection_context: ConnectionContext,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: ErrorResponseT,
        response_context: ResponseContext,
    ) -> CreateFailedRequestOperation[AnyErrorT, ErrorResponseT]: ...
    @overload
    @classmethod
    def generate(
        cls,
        *,
        type_: Literal[ResourceOperationType.READ],
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        timestamp: Timestamp,
        summary: str,
        error: AnyErrorT,
        connection_context: ConnectionContext,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: ErrorResponseT,
        response_context: ResponseContext,
    ) -> ReadFailedRequestOperation[AnyErrorT, ErrorResponseT]: ...
    @overload
    @classmethod
    def generate(
        cls,
        *,
        type_: Literal[ResourceOperationType.UPDATE],
        update_type: OptResourceOperationUpdateType = ...,
        data_update_type: OptResourceOperationDataUpdateType = ...,
        status_update_type: OptResourceOperationStatusUpdateType = ...,
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        timestamp: Timestamp,
        summary: str,
        error: AnyErrorT,
        connection_context: ConnectionContext,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: ErrorResponseT,
        response_context: ResponseContext,
    ) -> UpdateFailedRequestOperation[AnyErrorT, ErrorResponseT]: ...
    @overload
    @classmethod
    def generate(
        cls,
        *,
        type_: Literal[ResourceOperationType.DELETE],
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        timestamp: Timestamp,
        summary: str,
        error: AnyErrorT,
        connection_context: ConnectionContext,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: ErrorResponseT,
        response_context: ResponseContext,
    ) -> DeleteFailedRequestOperation[AnyErrorT, ErrorResponseT]: ...
    @overload
    @classmethod
    def generate(
        cls,
        *,
        type_: ResourceOperationType,
        create_type: OptResourceOperationCreateType = None,
        update_type: OptResourceOperationUpdateType = None,
        data_update_type: OptResourceOperationDataUpdateType = None,
        status_update_type: OptResourceOperationStatusUpdateType = None,
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        timestamp: Timestamp,
        summary: str,
        error: AnyErrorT,
        connection_context: ConnectionContext,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: ErrorResponseT,
        response_context: ResponseContext,
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
    @classmethod
    def generate(
        cls,
        action: OptAnyResourceOperationAction = None,
        *,
        type_: OptResourceOperationType = None,
        create_type: OptResourceOperationCreateType = None,
        update_type: OptResourceOperationUpdateType = None,
        data_update_type: OptResourceOperationDataUpdateType = None,
        status_update_type: OptResourceOperationStatusUpdateType = None,
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        timestamp: Timestamp,
        summary: str,
        error: AnyErrorT,
        connection_context: ConnectionContext,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: ErrorResponseT,
        response_context: ResponseContext,
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
    ):
        if (action is None and type_ is None) or (
            action is not None and type_ is not None
        ):
            raise ValueError("Only either 'action' or 'type' must be given")

        common_kwargs = {
            "application_context": application_context,
            "id": id,
            "context": context,
            "timestamp": timestamp,
            "summary": summary,
            "error": error,
            "connection_context": connection_context,
            "authentication": authentication,
            "authorization": authorization,
            "impersonation": impersonation,
            "response": response,
            "response_context": response_context,
        }

        if action is not None:
            if not isinstance(action, ResourceOperationActions):
                raise ValueError(f"Invalid 'action' type: '{type(action)}'")

            kwargs = deepcopy(common_kwargs)
            kwargs["action"] = action

            return cls.operation_cls_from_action(action).model_validate(kwargs)

        elif type_ is not None:
            action = ResourceOperationActionFactory.generate(
                type_,
                create_type=create_type,
                update_type=update_type,
                data_update_type=data_update_type,
                status_update_type=status_update_type,
            )
            kwargs = deepcopy(common_kwargs)
            kwargs["action"] = action
            return cls.operation_cls_from_type(type_).model_validate(kwargs)

        # This should never happen due to initial validation,
        # but type checker needs to see all paths covered
        raise ValueError("Neither 'action' nor 'type' provided")


class SuccessfulFactory:
    @overload
    @classmethod
    def operation_cls_from_action(
        cls, action: CreateResourceOperationAction
    ) -> Type[CreateSuccessfulRequestOperation]: ...
    @overload
    @classmethod
    def operation_cls_from_action(
        cls, action: ReadResourceOperationAction
    ) -> Type[ReadSuccessfulRequestOperation]: ...
    @overload
    @classmethod
    def operation_cls_from_action(
        cls, action: UpdateResourceOperationAction
    ) -> Type[UpdateSuccessfulRequestOperation]: ...
    @overload
    @classmethod
    def operation_cls_from_action(
        cls, action: DeleteResourceOperationAction
    ) -> Type[DeleteSuccessfulRequestOperation]: ...
    @overload
    @classmethod
    def operation_cls_from_action(
        cls, action: AnyResourceOperationAction
    ) -> AnySuccessfulRequestOperationType: ...
    @classmethod
    def operation_cls_from_action(
        cls, action: AnyResourceOperationAction
    ) -> AnySuccessfulRequestOperationType:
        if isinstance(action, CreateResourceOperationAction):
            operation_cls = CreateSuccessfulRequestOperation
        elif isinstance(action, ReadResourceOperationAction):
            operation_cls = ReadSuccessfulRequestOperation
        elif isinstance(action, UpdateResourceOperationAction):
            operation_cls = UpdateSuccessfulRequestOperation
        elif isinstance(action, DeleteResourceOperationAction):
            operation_cls = DeleteSuccessfulRequestOperation
        return operation_cls

    @overload
    @classmethod
    def operation_cls_from_type(
        cls,
        type_: Literal[ResourceOperationType.CREATE],
    ) -> Type[CreateSuccessfulRequestOperation]: ...
    @overload
    @classmethod
    def operation_cls_from_type(
        cls,
        type_: Literal[ResourceOperationType.READ],
    ) -> Type[ReadSuccessfulRequestOperation]: ...
    @overload
    @classmethod
    def operation_cls_from_type(
        cls,
        type_: Literal[ResourceOperationType.UPDATE],
    ) -> Type[UpdateSuccessfulRequestOperation]: ...
    @overload
    @classmethod
    def operation_cls_from_type(
        cls,
        type_: Literal[ResourceOperationType.DELETE],
    ) -> Type[DeleteSuccessfulRequestOperation]: ...
    @classmethod
    def operation_cls_from_type(
        cls,
        type_: ResourceOperationType,
    ) -> AnySuccessfulRequestOperationType:
        if type_ is ResourceOperationType.CREATE:
            operation_cls = CreateSuccessfulRequestOperation
        elif type_ is ResourceOperationType.READ:
            operation_cls = ReadSuccessfulRequestOperation
        elif type_ is ResourceOperationType.UPDATE:
            operation_cls = UpdateSuccessfulRequestOperation
        elif type_ is ResourceOperationType.DELETE:
            operation_cls = DeleteSuccessfulRequestOperation
        return operation_cls

    @overload
    @classmethod
    def generate(
        cls,
        action: CreateResourceOperationAction,
        *,
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        timestamp: Timestamp,
        summary: str,
        connection_context: ConnectionContext,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: AnyDataResponse[Any, OptAnyPagination, Any],
        response_context: ResponseContext,
    ) -> CreateSuccessfulRequestOperation: ...
    @overload
    @classmethod
    def generate(
        cls,
        action: ReadResourceOperationAction,
        *,
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        timestamp: Timestamp,
        summary: str,
        connection_context: ConnectionContext,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: AnyDataResponse[Any, OptAnyPagination, Any],
        response_context: ResponseContext,
    ) -> ReadSuccessfulRequestOperation: ...
    @overload
    @classmethod
    def generate(
        cls,
        action: UpdateResourceOperationAction,
        *,
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        timestamp: Timestamp,
        summary: str,
        connection_context: ConnectionContext,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: AnyDataResponse[Any, OptAnyPagination, Any],
        response_context: ResponseContext,
    ) -> UpdateSuccessfulRequestOperation: ...
    @overload
    @classmethod
    def generate(
        cls,
        action: DeleteResourceOperationAction,
        *,
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        timestamp: Timestamp,
        summary: str,
        connection_context: ConnectionContext,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: AnyDataResponse[Any, OptAnyPagination, Any],
        response_context: ResponseContext,
    ) -> DeleteSuccessfulRequestOperation: ...
    @overload
    @classmethod
    def generate(
        cls,
        action: AnyResourceOperationAction,
        *,
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        timestamp: Timestamp,
        summary: str,
        connection_context: ConnectionContext,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: AnyDataResponse[Any, OptAnyPagination, Any],
        response_context: ResponseContext,
    ) -> AnySuccessfulRequestOperation: ...
    @overload
    @classmethod
    def generate(
        cls,
        *,
        type_: Literal[ResourceOperationType.CREATE],
        create_type: OptResourceOperationCreateType = ...,
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        timestamp: Timestamp,
        summary: str,
        connection_context: ConnectionContext,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: AnyDataResponse[Any, OptAnyPagination, Any],
        response_context: ResponseContext,
    ) -> CreateSuccessfulRequestOperation: ...
    @overload
    @classmethod
    def generate(
        cls,
        *,
        type_: Literal[ResourceOperationType.READ],
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        timestamp: Timestamp,
        summary: str,
        connection_context: ConnectionContext,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: AnyDataResponse[Any, OptAnyPagination, Any],
        response_context: ResponseContext,
    ) -> ReadSuccessfulRequestOperation: ...
    @overload
    @classmethod
    def generate(
        cls,
        *,
        type_: Literal[ResourceOperationType.UPDATE],
        update_type: OptResourceOperationUpdateType = ...,
        data_update_type: OptResourceOperationDataUpdateType = ...,
        status_update_type: OptResourceOperationStatusUpdateType = ...,
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        timestamp: Timestamp,
        summary: str,
        connection_context: ConnectionContext,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: AnyDataResponse[Any, OptAnyPagination, Any],
        response_context: ResponseContext,
    ) -> UpdateSuccessfulRequestOperation: ...
    @overload
    @classmethod
    def generate(
        cls,
        *,
        type_: Literal[ResourceOperationType.DELETE],
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        timestamp: Timestamp,
        summary: str,
        connection_context: ConnectionContext,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: AnyDataResponse[Any, OptAnyPagination, Any],
        response_context: ResponseContext,
    ) -> DeleteSuccessfulRequestOperation: ...
    @overload
    @classmethod
    def generate(
        cls,
        *,
        type_: ResourceOperationType,
        create_type: OptResourceOperationCreateType = None,
        update_type: OptResourceOperationUpdateType = None,
        data_update_type: OptResourceOperationDataUpdateType = None,
        status_update_type: OptResourceOperationStatusUpdateType = None,
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        timestamp: Timestamp,
        summary: str,
        connection_context: ConnectionContext,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: AnyDataResponse[Any, OptAnyPagination, Any],
        response_context: ResponseContext,
    ) -> AnySuccessfulRequestOperation: ...
    @classmethod
    def generate(
        cls,
        action: OptAnyResourceOperationAction = None,
        *,
        type_: OptResourceOperationType = None,
        create_type: OptResourceOperationCreateType = None,
        update_type: OptResourceOperationUpdateType = None,
        data_update_type: OptResourceOperationDataUpdateType = None,
        status_update_type: OptResourceOperationStatusUpdateType = None,
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        timestamp: Timestamp,
        summary: str,
        connection_context: ConnectionContext,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: AnyDataResponse[Any, OptAnyPagination, Any],
        response_context: ResponseContext,
    ) -> AnySuccessfulRequestOperation:
        if (action is None and type_ is None) or (
            action is not None and type_ is not None
        ):
            raise ValueError("Only either 'action' or 'type' must be given")

        common_kwargs = {
            "application_context": application_context,
            "id": id,
            "context": context,
            "timestamp": timestamp,
            "summary": summary,
            "connection_context": connection_context,
            "authentication": authentication,
            "authorization": authorization,
            "impersonation": impersonation,
            "response": response,
            "response_context": response_context,
        }

        if action is not None:
            if not isinstance(action, ResourceOperationActions):
                raise ValueError(f"Invalid 'action' type: '{type(action)}'")

            kwargs = deepcopy(common_kwargs)
            kwargs["action"] = action

            return cls.operation_cls_from_action(action).model_validate(kwargs)

        if type_ is not None:
            action = ResourceOperationActionFactory.generate(
                type_,
                create_type=create_type,
                update_type=update_type,
                data_update_type=data_update_type,
                status_update_type=status_update_type,
            )
            kwargs = deepcopy(common_kwargs)
            kwargs["action"] = action
            return cls.operation_cls_from_type(type_).model_validate(kwargs)

        # This should never happen due to initial validation,
        # but type checker needs to see all paths covered
        raise ValueError("Neither 'action' nor 'type' provided")

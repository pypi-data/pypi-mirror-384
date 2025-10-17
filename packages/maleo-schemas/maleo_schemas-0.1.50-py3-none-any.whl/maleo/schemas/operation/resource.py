from copy import deepcopy
from typing import Generic, Literal, Type, overload
from uuid import UUID
from maleo.types.boolean import BoolT
from ..application import ApplicationContext
from ..connection import OptConnectionContext
from ..data import ModelDataT
from ..error import OptAnyErrorT, AnyErrorT
from ..metadata import ModelMetadataT
from ..pagination import PaginationT
from ..resource import Resource
from ..response import (
    ResponseT,
    ErrorResponseT,
    SuccessResponseT,
    NoDataResponse,
    CreateSingleDataResponse,
    ReadSingleDataResponse,
    UpdateSingleDataResponse,
    DeleteSingleDataResponse,
    CreateMultipleDataResponse,
    ReadMultipleDataResponse,
    UpdateMultipleDataResponse,
    DeleteMultipleDataResponse,
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


class ResourceOperation(
    BaseOperation[
        AnyResourceOperationActionT,
        Resource,
        BoolT,
        OptAnyErrorT,
        OptConnectionContext,
        ResponseT,
        None,
    ],
    Generic[
        AnyResourceOperationActionT,
        BoolT,
        OptAnyErrorT,
        ResponseT,
    ],
):
    type: OperationType = OperationType.RESOURCE
    response_context: None = None


class FailedResourceOperation(
    ResourceOperation[
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


class CreateFailedResourceOperation(
    FailedResourceOperation[
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


class ReadFailedResourceOperation(
    FailedResourceOperation[
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


class UpdateFailedResourceOperation(
    FailedResourceOperation[
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


class DeleteFailedResourceOperation(
    FailedResourceOperation[
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


class SuccessfulResourceOperation(
    ResourceOperation[
        AnyResourceOperationActionT,
        Literal[True],
        None,
        SuccessResponseT,
    ],
    Generic[
        AnyResourceOperationActionT,
        SuccessResponseT,
    ],
):
    success: Literal[True] = True
    error: None = None


class NoDataResourceOperation(
    SuccessfulResourceOperation[
        AnyResourceOperationActionT,
        NoDataResponse[ModelMetadataT],
    ],
    Generic[
        AnyResourceOperationActionT,
        ModelMetadataT,
    ],
):
    pass


class CreateSingleResourceOperation(
    SuccessfulResourceOperation[
        CreateResourceOperationAction,
        CreateSingleDataResponse[ModelDataT, ModelMetadataT],
    ],
    Generic[
        ModelDataT,
        ModelMetadataT,
    ],
):
    pass


class ReadSingleResourceOperation(
    SuccessfulResourceOperation[
        ReadResourceOperationAction,
        ReadSingleDataResponse[ModelDataT, ModelMetadataT],
    ],
    Generic[
        ModelDataT,
        ModelMetadataT,
    ],
):
    pass


class UpdateSingleResourceOperation(
    SuccessfulResourceOperation[
        UpdateResourceOperationAction,
        UpdateSingleDataResponse[ModelDataT, ModelMetadataT],
    ],
    Generic[
        ModelDataT,
        ModelMetadataT,
    ],
):
    pass


class DeleteSingleResourceOperation(
    SuccessfulResourceOperation[
        DeleteResourceOperationAction,
        DeleteSingleDataResponse[ModelDataT, ModelMetadataT],
    ],
    Generic[
        ModelDataT,
        ModelMetadataT,
    ],
):
    pass


class CreateMultipleResourceOperation(
    SuccessfulResourceOperation[
        CreateResourceOperationAction,
        CreateMultipleDataResponse[ModelDataT, PaginationT, ModelMetadataT],
    ],
    Generic[
        ModelDataT,
        PaginationT,
        ModelMetadataT,
    ],
):
    pass


class ReadMultipleResourceOperation(
    SuccessfulResourceOperation[
        ReadResourceOperationAction,
        ReadMultipleDataResponse[ModelDataT, PaginationT, ModelMetadataT],
    ],
    Generic[
        ModelDataT,
        PaginationT,
        ModelMetadataT,
    ],
):
    pass


class UpdateMultipleResourceOperation(
    SuccessfulResourceOperation[
        UpdateResourceOperationAction,
        UpdateMultipleDataResponse[ModelDataT, PaginationT, ModelMetadataT],
    ],
    Generic[
        ModelDataT,
        PaginationT,
        ModelMetadataT,
    ],
):
    pass


class DeleteMultipleResourceOperation(
    SuccessfulResourceOperation[
        DeleteResourceOperationAction,
        DeleteMultipleDataResponse[ModelDataT, PaginationT, ModelMetadataT],
    ],
    Generic[
        ModelDataT,
        PaginationT,
        ModelMetadataT,
    ],
):
    pass


class FailedFactory(Generic[AnyErrorT, ErrorResponseT]):
    @overload
    @classmethod
    def operation_cls_from_action(cls, action: CreateResourceOperationAction) -> Type[
        CreateFailedResourceOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
    ]: ...
    @overload
    @classmethod
    def operation_cls_from_action(cls, action: ReadResourceOperationAction) -> Type[
        ReadFailedResourceOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
    ]: ...
    @overload
    @classmethod
    def operation_cls_from_action(cls, action: UpdateResourceOperationAction) -> Type[
        UpdateFailedResourceOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
    ]: ...
    @overload
    @classmethod
    def operation_cls_from_action(cls, action: DeleteResourceOperationAction) -> Type[
        DeleteFailedResourceOperation[
            AnyErrorT,
            ErrorResponseT,
        ]
    ]: ...
    @overload
    @classmethod
    def operation_cls_from_action(cls, action: AnyResourceOperationAction) -> (
        Type[
            CreateFailedResourceOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        ]
        | Type[
            ReadFailedResourceOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        ]
        | Type[
            UpdateFailedResourceOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        ]
        | Type[
            DeleteFailedResourceOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        ]
    ): ...
    @classmethod
    def operation_cls_from_action(cls, action: AnyResourceOperationAction) -> (
        Type[
            CreateFailedResourceOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        ]
        | Type[
            ReadFailedResourceOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        ]
        | Type[
            UpdateFailedResourceOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        ]
        | Type[
            DeleteFailedResourceOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        ]
    ):
        if isinstance(action, CreateResourceOperationAction):
            operation_cls = CreateFailedResourceOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        elif isinstance(action, ReadResourceOperationAction):
            operation_cls = ReadFailedResourceOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        elif isinstance(action, UpdateResourceOperationAction):
            operation_cls = UpdateFailedResourceOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        elif isinstance(action, DeleteResourceOperationAction):
            operation_cls = DeleteFailedResourceOperation[
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
        CreateFailedResourceOperation[
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
        ReadFailedResourceOperation[
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
        UpdateFailedResourceOperation[
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
        DeleteFailedResourceOperation[
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
            CreateFailedResourceOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        ]
        | Type[
            ReadFailedResourceOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        ]
        | Type[
            UpdateFailedResourceOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        ]
        | Type[
            DeleteFailedResourceOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        ]
    ):
        if type_ is ResourceOperationType.CREATE:
            operation_cls = CreateFailedResourceOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        elif type_ is ResourceOperationType.READ:
            operation_cls = ReadFailedResourceOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        elif type_ is ResourceOperationType.UPDATE:
            operation_cls = UpdateFailedResourceOperation[
                AnyErrorT,
                ErrorResponseT,
            ]
        elif type_ is ResourceOperationType.DELETE:
            operation_cls = DeleteFailedResourceOperation[
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
        resource: Resource,
        timestamp: Timestamp,
        summary: str,
        error: AnyErrorT,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: ErrorResponseT,
    ) -> CreateFailedResourceOperation[AnyErrorT, ErrorResponseT]: ...
    @overload
    @classmethod
    def generate(
        cls,
        action: ReadResourceOperationAction,
        *,
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        resource: Resource,
        timestamp: Timestamp,
        summary: str,
        error: AnyErrorT,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: ErrorResponseT,
    ) -> ReadFailedResourceOperation[AnyErrorT, ErrorResponseT]: ...
    @overload
    @classmethod
    def generate(
        cls,
        action: UpdateResourceOperationAction,
        *,
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        resource: Resource,
        timestamp: Timestamp,
        summary: str,
        error: AnyErrorT,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: ErrorResponseT,
    ) -> UpdateFailedResourceOperation[AnyErrorT, ErrorResponseT]: ...
    @overload
    @classmethod
    def generate(
        cls,
        action: DeleteResourceOperationAction,
        *,
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        resource: Resource,
        timestamp: Timestamp,
        summary: str,
        error: AnyErrorT,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: ErrorResponseT,
    ) -> DeleteFailedResourceOperation[AnyErrorT, ErrorResponseT]: ...
    @overload
    @classmethod
    def generate(
        cls,
        action: AnyResourceOperationAction,
        *,
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        resource: Resource,
        timestamp: Timestamp,
        summary: str,
        error: AnyErrorT,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: ErrorResponseT,
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
    @classmethod
    def generate(
        cls,
        *,
        type_: Literal[ResourceOperationType.CREATE],
        create_type: OptResourceOperationCreateType = ...,
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        resource: Resource,
        timestamp: Timestamp,
        summary: str,
        error: AnyErrorT,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: ErrorResponseT,
    ) -> CreateFailedResourceOperation[AnyErrorT, ErrorResponseT]: ...
    @overload
    @classmethod
    def generate(
        cls,
        *,
        type_: Literal[ResourceOperationType.READ],
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        resource: Resource,
        timestamp: Timestamp,
        summary: str,
        error: AnyErrorT,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: ErrorResponseT,
    ) -> ReadFailedResourceOperation[AnyErrorT, ErrorResponseT]: ...
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
        resource: Resource,
        timestamp: Timestamp,
        summary: str,
        error: AnyErrorT,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: ErrorResponseT,
    ) -> UpdateFailedResourceOperation[AnyErrorT, ErrorResponseT]: ...
    @overload
    @classmethod
    def generate(
        cls,
        *,
        type_: Literal[ResourceOperationType.DELETE],
        application_context: ApplicationContext,
        id: UUID,
        context: OperationContext,
        resource: Resource,
        timestamp: Timestamp,
        summary: str,
        error: AnyErrorT,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: ErrorResponseT,
    ) -> DeleteFailedResourceOperation[AnyErrorT, ErrorResponseT]: ...
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
        resource: Resource,
        timestamp: Timestamp,
        summary: str,
        error: AnyErrorT,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: ErrorResponseT,
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
        resource: Resource,
        timestamp: Timestamp,
        summary: str,
        error: AnyErrorT,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        response: ErrorResponseT,
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
    ):
        if (action is None and type_ is None) or (
            action is not None and type_ is not None
        ):
            raise ValueError("Only either 'action' or 'type' must be given")

        common_kwargs = {
            "application_context": application_context,
            "id": id,
            "context": context,
            "resource": resource,
            "timestamp": timestamp,
            "summary": summary,
            "error": error,
            "connection_context": connection_context,
            "authentication": authentication,
            "authorization": authorization,
            "impersonation": impersonation,
            "response": response,
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

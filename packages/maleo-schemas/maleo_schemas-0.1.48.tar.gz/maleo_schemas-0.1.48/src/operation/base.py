import traceback
from logging import Logger
from typing import Generic
from maleo.logging.enums import Level
from maleo.types.boolean import BoolT, OptBool
from maleo.types.dict import (
    OptStrToStrDict,
    StrToAnyDict,
    StrToStrDict,
)
from maleo.utils.merger import merge_dicts
from ..application import ApplicationContextMixin
from ..connection import OptConnectionContextT, ConnectionContextMixin
from ..error import OptAnyErrorT, ErrorMixin
from ..mixins.general import Success
from ..resource import OptResourceT, ResourceMixin
from ..response import (
    OptResponseContextT,
    ResponseContextMixin,
    ResponseT,
    ResponseMixin,
)
from ..security.authentication import (
    OptAnyAuthentication,
    AuthenticationMixin,
)
from ..security.authorization import OptAnyAuthorization, AuthorizationMixin
from ..security.impersonation import OptImpersonation, ImpersonationMixin
from .action import (
    ActionMixin,
    ActionT,
)
from .context import ContextMixin
from .mixins import Id, OperationType, Summary, TimestampMixin


class BaseOperation(
    ResponseContextMixin[OptResponseContextT],
    ResponseMixin[ResponseT],
    ImpersonationMixin[OptImpersonation],
    AuthorizationMixin[OptAnyAuthorization],
    AuthenticationMixin[OptAnyAuthentication],
    ConnectionContextMixin[OptConnectionContextT],
    ErrorMixin[OptAnyErrorT],
    Success[BoolT],
    Summary,
    TimestampMixin,
    ResourceMixin[OptResourceT],
    ActionMixin[ActionT],
    ContextMixin,
    OperationType,
    Id,
    ApplicationContextMixin,
    Generic[
        ActionT,
        OptResourceT,
        BoolT,
        OptAnyErrorT,
        OptConnectionContextT,
        ResponseT,
        OptResponseContextT,
    ],
):
    @property
    def log_message(self) -> str:
        message = f"Operation {self.id} - {self.type} - "

        success_information = str(self.success)

        if self.response_context is not None:
            success_information += f" {self.response_context.status_code}"

        message += f"{success_information} - "

        if self.connection_context is not None:
            message += (
                f"{self.connection_context.method} {self.connection_context.url} - "
                f"IP: {self.connection_context.ip_address} - "
            )

        if self.authentication is None:
            authentication = "No Authentication"
        else:
            if not self.authentication.user.is_authenticated:
                authentication = "Unauthenticated"
            else:
                authentication = (
                    "Authenticated | "
                    f"Organization: {self.authentication.user.organization} | "
                    f"Username: {self.authentication.user.display_name} | "
                    f"Email: {self.authentication.user.identity}"
                )

        message += f"{authentication} - "
        message += self.summary

        return message

    @property
    def labels(self) -> StrToStrDict:
        labels = {
            "environment": self.application_context.environment,
            "service_key": self.application_context.service_key,
            "operation_id": str(self.id),
            "operation_type": self.type,
            "success": str(self.success),
        }

        if self.connection_context is not None:
            if self.connection_context.method is not None:
                labels["method"] = self.connection_context.method
            labels["url"] = self.connection_context.url
        if self.response_context is not None:
            labels["status_code"] = str(self.response_context.status_code)

        return labels

    def log_labels(
        self,
        *,
        additional_labels: OptStrToStrDict = None,
        override_labels: OptStrToStrDict = None,
    ) -> StrToStrDict:
        if override_labels is not None:
            return override_labels

        labels = self.labels
        if additional_labels is not None:
            for k, v in additional_labels.items():
                if k in labels.keys():
                    raise ValueError(
                        f"Key '{k}' already exist in labels, override the labels if necessary"
                    )
                labels[k] = v
            labels = merge_dicts(labels, additional_labels)
        return labels

    def log_extra(
        self,
        *,
        additional_extra: OptStrToStrDict = None,
        override_extra: OptStrToStrDict = None,
        additional_labels: OptStrToStrDict = None,
        override_labels: OptStrToStrDict = None,
    ) -> StrToAnyDict:
        labels = self.log_labels(
            additional_labels=additional_labels, override_labels=override_labels
        )

        if override_extra is not None:
            extra = override_extra
        else:
            extra = {
                "json_fields": {"operation": self.model_dump(mode="json")},
                "labels": labels,
            }
            if additional_extra is not None:
                extra = merge_dicts(extra, additional_extra)

        return extra

    def log(
        self,
        logger: Logger,
        level: Level,
        *,
        exc_info: OptBool = None,
        additional_extra: OptStrToStrDict = None,
        override_extra: OptStrToStrDict = None,
        additional_labels: OptStrToStrDict = None,
        override_labels: OptStrToStrDict = None,
    ):
        try:
            message = self.log_message
            extra = self.log_extra(
                additional_extra=additional_extra,
                override_extra=override_extra,
                additional_labels=additional_labels,
                override_labels=override_labels,
            )
            logger.log(
                level,
                message,
                exc_info=exc_info,
                extra=extra,
            )
        except Exception:
            print(f"Failed logging {self.type} operation:\n{traceback.format_exc()}")

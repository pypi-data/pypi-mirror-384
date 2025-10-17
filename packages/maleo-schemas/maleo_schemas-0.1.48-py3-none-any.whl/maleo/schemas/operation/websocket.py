from typing import Generic, Literal
from maleo.types.boolean import BoolT
from ..connection import OptConnectionContext
from ..error import (
    OptAnyErrorT,
    AnyErrorT,
)
from ..response import ResponseT, ErrorResponseT, SuccessResponseT
from .action.websocket import WebSocketOperationAction
from .base import BaseOperation
from .enums import OperationType


class WebSocketOperation(
    BaseOperation[
        WebSocketOperationAction,
        None,
        BoolT,
        OptAnyErrorT,
        OptConnectionContext,
        ResponseT,
        None,
    ],
    Generic[
        BoolT,
        OptAnyErrorT,
        ResponseT,
    ],
):
    type: OperationType = OperationType.WEBSOCKET
    resource: None = None
    response_context: None = None


class FailedWebSocketOperation(
    WebSocketOperation[
        Literal[False],
        AnyErrorT,
        ErrorResponseT,
    ],
    Generic[AnyErrorT, ErrorResponseT],
):
    success: Literal[False] = False


class SuccessfulWebSocketOperation(
    WebSocketOperation[
        Literal[True],
        None,
        SuccessResponseT,
    ],
    Generic[SuccessResponseT],
):
    success: Literal[True] = True
    error: None = None

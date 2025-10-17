from fastapi import Header
from fastapi.requests import HTTPConnection
from typing import Callable
from uuid import UUID
from maleo.enums.connection import Header as HeaderEnum
from maleo.types.uuid import OptUUID
from .enums import IdSource
from .extractor import extract_operation_id


def get_operation_id(
    source: IdSource = IdSource.STATE, *, generate: bool = False
) -> Callable[..., UUID]:

    def dependency(
        conn: HTTPConnection,
        # the following operation_id is for documentation purpose only
        operation_id: OptUUID = Header(
            None,
            alias=HeaderEnum.X_OPERATION_ID.value,
            description="Operation's ID",
        ),
    ) -> UUID:
        return extract_operation_id(source, conn=conn, generate=generate)

    return dependency

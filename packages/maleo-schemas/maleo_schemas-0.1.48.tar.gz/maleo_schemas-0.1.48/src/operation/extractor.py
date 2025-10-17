from fastapi import status, HTTPException
from fastapi.requests import HTTPConnection
from uuid import UUID, uuid4
from maleo.enums.connection import Header
from .enums import IdSource


def extract_operation_id(
    source: IdSource = IdSource.STATE, *, conn: HTTPConnection, generate: bool = False
) -> UUID:
    if source is IdSource.HEADER:
        operation_id = conn.headers.get(Header.X_OPERATION_ID.value, None)
        try:
            operation_id = UUID(operation_id)
        except Exception:
            pass
    elif source is IdSource.STATE:
        operation_id = getattr(conn.state, "operation_id", None)
    if operation_id is not None and not isinstance(operation_id, UUID):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid operation id: {operation_id}",
        )

    if operation_id is not None:
        return operation_id

    if generate:
        operation_id = uuid4()
        conn.state.operation_id = operation_id
        return operation_id

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unable to determine operation_id",
    )

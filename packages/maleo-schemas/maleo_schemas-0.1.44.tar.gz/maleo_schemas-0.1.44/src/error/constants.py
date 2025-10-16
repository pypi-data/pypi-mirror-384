from typing import Dict
from .enums import ErrorCode, ErrorType


ERROR_CODE_STATUS_CODE_MAP: Dict[ErrorCode, int] = {
    ErrorCode.BAD_REQUEST: 400,
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.FORBIDDEN: 403,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.METHOD_NOT_ALLOWED: 405,
    ErrorCode.CONFLICT: 409,
    ErrorCode.UNPROCESSABLE_ENTITY: 422,
    ErrorCode.TOO_MANY_REQUESTS: 429,
    ErrorCode.INTERNAL_SERVER_ERROR: 500,
    ErrorCode.NOT_IMPLEMENTED: 501,
    ErrorCode.BAD_GATEWAY: 502,
    ErrorCode.SERVICE_UNAVAILABLE: 503,
}


ERROR_TYPE_STATUS_CODE_MAP: Dict[ErrorType, int] = {
    ErrorType.BAD_REQUEST: 400,
    ErrorType.UNAUTHORIZED: 401,
    ErrorType.FORBIDDEN: 403,
    ErrorType.NOT_FOUND: 404,
    ErrorType.METHOD_NOT_ALLOWED: 405,
    ErrorType.CONFLICT: 409,
    ErrorType.UNPROCESSABLE_ENTITY: 422,
    ErrorType.TOO_MANY_REQUESTS: 429,
    ErrorType.INTERNAL_SERVER_ERROR: 500,
    ErrorType.NOT_IMPLEMENTED: 501,
    ErrorType.BAD_GATEWAY: 502,
    ErrorType.SERVICE_UNAVAILABLE: 503,
}


STATUS_CODE_ERROR_TYPE_MAP: Dict[int, ErrorType] = {
    400: ErrorType.BAD_REQUEST,
    401: ErrorType.UNAUTHORIZED,
    403: ErrorType.FORBIDDEN,
    404: ErrorType.NOT_FOUND,
    405: ErrorType.METHOD_NOT_ALLOWED,
    409: ErrorType.CONFLICT,
    422: ErrorType.UNPROCESSABLE_ENTITY,
    429: ErrorType.TOO_MANY_REQUESTS,
    500: ErrorType.INTERNAL_SERVER_ERROR,
    501: ErrorType.NOT_IMPLEMENTED,
    502: ErrorType.BAD_GATEWAY,
    503: ErrorType.SERVICE_UNAVAILABLE,
}

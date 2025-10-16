from enum import StrEnum
from maleo.types.string import ListOfStrs


class IdSource(StrEnum):
    HEADER = "header"
    STATE = "state"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


class OperationType(StrEnum):
    RESOURCE = "resource"
    REQUEST = "request"
    SYSTEM = "system"
    WEBSOCKET = "websocket"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


OptOperationType = OperationType | None


class SystemOperationType(StrEnum):
    BACKGROUND_JOB = "background_job"
    CONFIGURATION_UPDATE = "configuration_update"
    CRON_JOB = "cron_job"
    DATABASE_CONNECTION = "database_connection"
    DISPOSAL = "disposal"
    HEALTH_CHECK = "health_check"
    HEARTBEAT = "heartbeat"
    METRIC_REPORT = "metric_report"
    INITIALIZATION = "initialization"
    STARTUP = "startup"
    SHUTDOWN = "shutdown"
    SYSTEM_ALERT = "system_alert"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


OptSystemOperationType = SystemOperationType | None


class WebSocketOperationType(StrEnum):
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    ERROR = "error"
    RECEIVE = "receive"
    SEND = "send"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


OptWebSocketOperationType = WebSocketOperationType | None


class ResourceOperationType(StrEnum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


OptResourceOperationType = ResourceOperationType | None


class ResourceOperationCreateType(StrEnum):
    NEW = "new"
    RESTORE = "restore"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


OptResourceOperationCreateType = ResourceOperationCreateType | None


class ResourceOperationUpdateType(StrEnum):
    DATA = "data"
    STATUS = "status"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


OptResourceOperationUpdateType = ResourceOperationUpdateType | None


class ResourceOperationDataUpdateType(StrEnum):
    FULL = "full"
    PARTIAL = "partial"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


OptResourceOperationDataUpdateType = ResourceOperationDataUpdateType | None


class ResourceOperationStatusUpdateType(StrEnum):
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    RESTORE = "restore"
    DELETE = "delete"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


OptResourceOperationStatusUpdateType = ResourceOperationStatusUpdateType | None


class Origin(StrEnum):
    SERVICE = "service"
    CLIENT = "client"
    UTILITY = "utility"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


OptOrigin = Origin | None


class Layer(StrEnum):
    INFRASTRUCTURE = "infrastructure"
    CONFIGURATION = "configuration"
    UTILITY = "utility"
    MIDDLEWARE = "middleware"
    CONTROLLER = "controller"
    SERVICE = "service"
    REPOSITORY = "repository"
    INTERNAL = "internal"
    OTHER = "other"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


OptLayer = Layer | None


class Target(StrEnum):
    MONITORING = "monitoring"
    CACHE = "cache"
    CONTROLLER = "controller"
    DATABASE = "database"
    INTERNAL = "internal"
    MICROSERVICE = "microservice"
    SERVICE = "service"
    REPOSITORY = "repository"
    THIRD_PARTY = "third_party"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


OptLayer = Layer | None

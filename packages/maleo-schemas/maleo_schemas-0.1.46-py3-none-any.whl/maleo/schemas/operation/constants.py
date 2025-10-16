from typing import Mapping
from maleo.enums.status import DataStatus, SeqOfDataStatuses
from .enums import ResourceOperationStatusUpdateType


STATUS_UPDATE_RULES: Mapping[ResourceOperationStatusUpdateType, SeqOfDataStatuses] = {
    ResourceOperationStatusUpdateType.DELETE: (DataStatus.INACTIVE, DataStatus.ACTIVE),
    ResourceOperationStatusUpdateType.RESTORE: (DataStatus.DELETED,),
    ResourceOperationStatusUpdateType.DEACTIVATE: (DataStatus.ACTIVE,),
    ResourceOperationStatusUpdateType.ACTIVATE: (DataStatus.INACTIVE,),
}

STATUS_UPDATE_RESULT: Mapping[ResourceOperationStatusUpdateType, DataStatus] = {
    ResourceOperationStatusUpdateType.DELETE: DataStatus.DELETED,
    ResourceOperationStatusUpdateType.RESTORE: DataStatus.ACTIVE,
    ResourceOperationStatusUpdateType.DEACTIVATE: DataStatus.INACTIVE,
    ResourceOperationStatusUpdateType.ACTIVATE: DataStatus.ACTIVE,
}

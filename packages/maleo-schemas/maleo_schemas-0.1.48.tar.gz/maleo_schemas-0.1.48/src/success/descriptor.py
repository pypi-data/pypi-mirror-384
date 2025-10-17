from pydantic import Field
from typing import Annotated
from ..mixins.general import Descriptor
from .enums import SuccessCode


class SuccessDescriptor(Descriptor[SuccessCode]):
    code: Annotated[
        SuccessCode, Field(SuccessCode.ANY_DATA, description="Success's code")
    ] = SuccessCode.ANY_DATA
    message: Annotated[
        str, Field("Any data response", description="Success's message")
    ] = "Any data response"
    description: Annotated[
        str, Field("Response with Any Data", description="Success's description")
    ] = "Response with Any Data"


class AnyDataSuccessDescriptor(SuccessDescriptor):
    code: SuccessCode = SuccessCode.ANY_DATA
    message: str = "Any data response"
    description: str = "Response with Any Data"


class NoDataSuccessDescriptor(SuccessDescriptor):
    code: SuccessCode = SuccessCode.NO_DATA
    message: str = "No data response"
    description: str = "Response with No Data"


class SingleDataSuccessDescriptor(SuccessDescriptor):
    code: SuccessCode = SuccessCode.SINGLE_DATA
    message: str = "Single data response"
    description: str = "Response with Single Data"


class CreateSingleDataSuccessDescriptor(SuccessDescriptor):
    code: SuccessCode = SuccessCode.CREATE_SINGLE_DATA
    message: str = "Create single data response"
    description: str = "Create response with Single Data"


class UpdateSingleDataSuccessDescriptor(SuccessDescriptor):
    code: SuccessCode = SuccessCode.UPDATE_SINGLE_DATA
    message: str = "Update single data response"
    description: str = "Update response with Single Data"


class OptSingleDataSuccessDescriptor(SuccessDescriptor):
    code: SuccessCode = SuccessCode.OPTIONAL_SINGLE_DATA
    message: str = "Optional single data response"
    description: str = "Response with Optional Single Data"


class ReadSingleDataSuccessDescriptor(SuccessDescriptor):
    code: SuccessCode = SuccessCode.READ_SINGLE_DATA
    message: str = "Read single data response"
    description: str = "Read response with Single Data"


class DeleteSingleDataSuccessDescriptor(SuccessDescriptor):
    code: SuccessCode = SuccessCode.DELETE_SINGLE_DATA
    message: str = "Delete single data response"
    description: str = "Delete response with Single Data"


class MultipleDataSuccessDescriptor(SuccessDescriptor):
    code: SuccessCode = SuccessCode.MULTIPLE_DATA
    message: str = "Multiple data response"
    description: str = "Response with Multiple Data"


class CreateMultipleDataSuccessDescriptor(SuccessDescriptor):
    code: SuccessCode = SuccessCode.CREATE_MULTIPLE_DATA
    message: str = "Create multiple data response"
    description: str = "Create response with Multiple Data"


class UpdateMultipleDataSuccessDescriptor(SuccessDescriptor):
    code: SuccessCode = SuccessCode.UPDATE_MULTIPLE_DATA
    message: str = "Update multiple data response"
    description: str = "Update response with Multiple Data"


class OptMultipleDataSuccessDescriptor(SuccessDescriptor):
    code: SuccessCode = SuccessCode.OPTIONAL_MULTIPLE_DATA
    message: str = "Optional multiple data response"
    description: str = "Response with Optional Multiple Data"


class ReadMultipleDataSuccessDescriptor(SuccessDescriptor):
    code: SuccessCode = SuccessCode.READ_MULTIPLE_DATA
    message: str = "Read multiple data response"
    description: str = "Read response with Multiple Data"


class DeleteMultipleDataSuccessDescriptor(SuccessDescriptor):
    code: SuccessCode = SuccessCode.DELETE_MULTIPLE_DATA
    message: str = "Delete multiple data response"
    description: str = "Delete response with Multiple Data"

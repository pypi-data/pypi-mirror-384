from pydantic import BaseModel, Field
from typing import Generic, TypeVar
from uuid import UUID as PythonUUID
from maleo.types.enum import StrEnumT
from maleo.types.integer import OptIntT, OptListOfIntsT
from maleo.types.misc import (
    OptIntOrUUIDT,
    OptListOfIntsOrUUIDsT,
)
from maleo.types.string import OptStrT, OptListOfStrsT
from maleo.types.uuid import OptUUIDT, OptListOfUUIDsT


class IdentifierType(BaseModel, Generic[StrEnumT]):
    identifier_type: StrEnumT = Field(..., description="Identifier's type")


IdentifierValueT = TypeVar("IdentifierValueT")


class IdentifierValue(BaseModel, Generic[IdentifierValueT]):
    identifier_value: IdentifierValueT = Field(..., description="Identifier's value")


class IdentifierTypeValue(
    IdentifierValue[IdentifierValueT],
    IdentifierType[StrEnumT],
    BaseModel,
    Generic[StrEnumT, IdentifierValueT],
):
    pass


# Id
class Id(BaseModel, Generic[OptIntOrUUIDT]):
    id: OptIntOrUUIDT = Field(..., description="Id")


class IntId(BaseModel, Generic[OptIntT]):
    id: OptIntT = Field(..., description="Id (Integer)", ge=1)


class UUIDId(BaseModel, Generic[OptUUIDT]):
    id: OptUUIDT = Field(..., description="Id (UUID)")


# Ids
class Ids(BaseModel, Generic[OptListOfIntsOrUUIDsT]):
    ids: OptListOfIntsOrUUIDsT = Field(..., description="Ids")


class IntIds(BaseModel, Generic[OptListOfIntsT]):
    ids: OptListOfIntsT = Field(..., description="Ids (Integers)")


class UUIDIds(BaseModel, Generic[OptListOfUUIDsT]):
    ids: OptListOfUUIDsT = Field(..., description="Ids (UUIDs)")


# UUID
class UUID(BaseModel, Generic[OptUUIDT]):
    uuid: OptUUIDT = Field(..., description="UUID")


class UUIDs(BaseModel, Generic[OptListOfUUIDsT]):
    uuids: OptListOfUUIDsT = Field(..., description="UUIDs")


# Identifier
class DataIdentifier(
    UUID[PythonUUID],
    IntId[int],
):
    pass


class EntityIdentifier(
    UUID[PythonUUID],
    IntId[int],
):
    pass


EntityIdentifierT = TypeVar("EntityIdentifierT", bound=EntityIdentifier)
OptEntityIdentifier = EntityIdentifier | None
OptEntityIdentifierT = TypeVar("OptEntityIdentifierT", bound=OptEntityIdentifier)


class Key(BaseModel, Generic[OptStrT]):
    key: OptStrT = Field(..., description="Key")


class Keys(BaseModel, Generic[OptListOfStrsT]):
    keys: OptListOfStrsT = Field(..., description="Keys")


class Name(BaseModel, Generic[OptStrT]):
    name: OptStrT = Field(..., description="Name")


class Names(BaseModel, Generic[OptListOfStrsT]):
    names: OptListOfStrsT = Field(..., description="Names")


# ----- ----- ----- Organization ID ----- ----- ----- #


class OrganizationId(BaseModel, Generic[OptIntOrUUIDT]):
    organization_id: OptIntOrUUIDT = Field(..., description="Organization's ID")


class IntOrganizationId(BaseModel, Generic[OptIntT]):
    organization_id: OptIntT = Field(..., description="Organization's ID", ge=1)


class UUIDOrganizationId(BaseModel, Generic[OptUUIDT]):
    organization_id: OptUUIDT = Field(..., description="Organization's ID")


class OrganizationIds(BaseModel, Generic[OptListOfIntsOrUUIDsT]):
    organization_ids: OptListOfIntsOrUUIDsT = Field(
        ..., description="Organization's IDs"
    )


class IntOrganizationIds(BaseModel, Generic[OptListOfIntsT]):
    organization_ids: OptListOfIntsT = Field(..., description="Organization's IDs")


class UUIDOrganizationIds(BaseModel, Generic[OptListOfUUIDsT]):
    organization_ids: OptListOfUUIDsT = Field(..., description="Organization's IDs")


# ----- ----- ----- Parent ID ----- ----- ----- #


class ParentId(BaseModel, Generic[OptIntOrUUIDT]):
    parent_id: OptIntOrUUIDT = Field(..., description="Parent's ID")


class IntParentId(BaseModel, Generic[OptIntT]):
    parent_id: OptIntT = Field(..., description="Parent's ID", ge=1)


class UUIDParentId(BaseModel, Generic[OptUUIDT]):
    parent_id: OptUUIDT = Field(..., description="Parent's ID")


class ParentIds(BaseModel, Generic[OptListOfIntsOrUUIDsT]):
    parent_ids: OptListOfIntsOrUUIDsT = Field(..., description="Parent's IDs")


class IntParentIds(BaseModel, Generic[OptListOfIntsT]):
    parent_ids: OptListOfIntsT = Field(..., description="Parent's IDs")


class UUIDParentIds(BaseModel, Generic[OptListOfUUIDsT]):
    parent_ids: OptListOfUUIDsT = Field(..., description="Parent's IDs")


# ----- ----- ----- Patient ID ----- ----- ----- #


class PatientId(BaseModel, Generic[OptIntOrUUIDT]):
    patient_id: OptIntOrUUIDT = Field(..., description="Patient's ID")


class IntPatientId(BaseModel, Generic[OptIntT]):
    patient_id: OptIntT = Field(..., description="Patient's ID", ge=1)


class UUIDPatientId(BaseModel, Generic[OptUUIDT]):
    patient_id: OptUUIDT = Field(..., description="Patient's ID")


class PatientIds(BaseModel, Generic[OptListOfIntsOrUUIDsT]):
    patient_ids: OptListOfIntsOrUUIDsT = Field(..., description="Patient's IDs")


class IntPatientIds(BaseModel, Generic[OptListOfIntsT]):
    patient_ids: OptListOfIntsT = Field(..., description="Patient's IDs")


class UUIDPatientIds(BaseModel, Generic[OptListOfUUIDsT]):
    patient_ids: OptListOfUUIDsT = Field(..., description="Patient's IDs")


# ----- ----- ----- Source ID ----- ----- ----- #


class SourceId(BaseModel, Generic[OptIntOrUUIDT]):
    source_id: OptIntOrUUIDT = Field(..., description="Source's ID")


class IntSourceId(BaseModel, Generic[OptIntT]):
    source_id: OptIntT = Field(..., description="Source's ID", ge=1)


class UUIDSourceId(BaseModel, Generic[OptUUIDT]):
    source_id: OptUUIDT = Field(..., description="Source's ID")


class SourceIds(BaseModel, Generic[OptListOfIntsOrUUIDsT]):
    source_ids: OptListOfIntsOrUUIDsT = Field(..., description="Source's IDs")


class IntSourceIds(BaseModel, Generic[OptListOfIntsT]):
    source_ids: OptListOfIntsT = Field(..., description="Source's IDs")


class UUIDSourceIds(BaseModel, Generic[OptListOfUUIDsT]):
    source_ids: OptListOfUUIDsT = Field(..., description="Source's IDs")


# ----- ----- ----- Target ID ----- ----- ----- #


class TargetId(BaseModel, Generic[OptIntOrUUIDT]):
    target_id: OptIntOrUUIDT = Field(..., description="Target's ID")


class IntTargetId(BaseModel, Generic[OptIntT]):
    target_id: OptIntT = Field(..., description="Target's ID", ge=1)


class UUIDTargetId(BaseModel, Generic[OptUUIDT]):
    target_id: OptUUIDT = Field(..., description="Target's ID")


class TargetIds(BaseModel, Generic[OptListOfIntsOrUUIDsT]):
    target_ids: OptListOfIntsOrUUIDsT = Field(..., description="Target's IDs")


class IntTargetIds(BaseModel, Generic[OptListOfIntsT]):
    target_ids: OptListOfIntsT = Field(..., description="Target's IDs")


class UUIDTargetIds(BaseModel, Generic[OptListOfUUIDsT]):
    target_ids: OptListOfUUIDsT = Field(..., description="Target's IDs")


# ----- ----- ----- User ID ----- ----- ----- #


class UserId(BaseModel, Generic[OptIntOrUUIDT]):
    user_id: OptIntOrUUIDT = Field(..., description="User's ID")


class IntUserId(BaseModel, Generic[OptIntT]):
    user_id: OptIntT = Field(..., description="User's ID", ge=1)


class UUIDUserId(BaseModel, Generic[OptUUIDT]):
    user_id: OptUUIDT = Field(..., description="User's ID")


class UserIds(BaseModel, Generic[OptListOfIntsOrUUIDsT]):
    user_ids: OptListOfIntsOrUUIDsT = Field(..., description="User's IDs")


class IntUserIds(BaseModel, Generic[OptListOfIntsT]):
    user_ids: OptListOfIntsT = Field(..., description="User's IDs")


class UUIDUserIds(BaseModel, Generic[OptListOfUUIDsT]):
    user_ids: OptListOfUUIDsT = Field(..., description="User's IDs")

from datetime import datetime
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column
from sqlalchemy.types import Integer, Enum, DateTime
from uuid import UUID as PythonUUID, uuid4
from maleo.enums.status import DataStatus as DataStatusEnum
from maleo.types.datetime import OptDatetime
from maleo.types.integer import OptInt
from maleo.types.uuid import OptUUID
from maleo.utils.formatter import CaseFormatter


class TableName:
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return CaseFormatter.to_snake(cls.__name__)  # type: ignore


# Int ID
class IntId:
    id: Mapped[int] = mapped_column(name="id", type_=Integer, nullable=False)


class OptIntId:
    id: Mapped[OptInt] = mapped_column(name="id", type_=Integer)


class IntParentId:
    parent_id: Mapped[int] = mapped_column(
        name="parent_id", type_=Integer, nullable=False
    )


class OptIntParentId:
    parent_id: Mapped[OptInt] = mapped_column(name="parent_id", type_=Integer)


class IntOrganizationId:
    organization_id: Mapped[int] = mapped_column(
        name="organization_id", type_=Integer, nullable=False
    )


class OptIntOrganizationId:
    organization_id: Mapped[OptInt] = mapped_column(
        name="organization_id", type_=Integer
    )


class IntSourceId:
    source_id: Mapped[int] = mapped_column(
        name="source_id", type_=Integer, nullable=False
    )


class OptIntSourceId:
    source_id: Mapped[OptInt] = mapped_column(name="source_id", type_=Integer)


class IntTargetId:
    target_id: Mapped[int] = mapped_column(
        name="target_id", type_=Integer, nullable=False
    )


class OptIntTargetId:
    target_id: Mapped[OptInt] = mapped_column(name="target_id", type_=Integer)


class IntUserId:
    user_id: Mapped[int] = mapped_column(name="user_id", type_=Integer, nullable=False)


class OptIntUserId:
    user_id: Mapped[OptInt] = mapped_column(name="user_id", type_=Integer)


# UUID ID
class UUIDId:
    id: Mapped[int] = mapped_column(
        name="id", type_=PostgresUUID(as_uuid=True), default=uuid4, nullable=False
    )


class OptUUIDId:
    id: Mapped[OptUUID] = mapped_column(name="id", type_=PostgresUUID(as_uuid=True))


class UUIDParentId:
    parent_id: Mapped[int] = mapped_column(
        name="parent_id",
        type_=PostgresUUID(as_uuid=True),
        default=uuid4,
        nullable=False,
    )


class OptUUIDParentId:
    parent_id: Mapped[OptUUID] = mapped_column(
        name="parent_id", type_=PostgresUUID(as_uuid=True)
    )


class UUIDOrganizationId:
    organization_id: Mapped[int] = mapped_column(
        name="organization_id",
        type_=PostgresUUID(as_uuid=True),
        default=uuid4,
        nullable=False,
    )


class OptUUIDOrganizationId:
    organization_id: Mapped[OptUUID] = mapped_column(
        name="organization_id", type_=PostgresUUID(as_uuid=True)
    )


class UUIDSourceId:
    source_id: Mapped[int] = mapped_column(
        name="source_id",
        type_=PostgresUUID(as_uuid=True),
        default=uuid4,
        nullable=False,
    )


class OptUUIDSourceId:
    source_id: Mapped[OptUUID] = mapped_column(
        name="source_id", type_=PostgresUUID(as_uuid=True)
    )


class UUIDTargetId:
    target_id: Mapped[int] = mapped_column(
        name="target_id",
        type_=PostgresUUID(as_uuid=True),
        default=uuid4,
        nullable=False,
    )


class OptUUIDTargetId:
    target_id: Mapped[OptUUID] = mapped_column(
        name="target_id", type_=PostgresUUID(as_uuid=True)
    )


class UUIDUserId:
    user_id: Mapped[int] = mapped_column(
        name="user_id", type_=PostgresUUID(as_uuid=True), default=uuid4, nullable=False
    )


class OptUUIDUserId:
    user_id: Mapped[OptUUID] = mapped_column(
        name="user_id", type_=PostgresUUID(as_uuid=True)
    )


# Identifier
class DataIdentifier:
    id: Mapped[int] = mapped_column(name="id", type_=Integer, primary_key=True)
    uuid: Mapped[PythonUUID] = mapped_column(
        name="uuid",
        type_=PostgresUUID(as_uuid=True),
        default=uuid4,
        unique=True,
        nullable=False,
    )


class CreationTimestamp:
    created_at: Mapped[datetime] = mapped_column(
        name="created_at",
        type_=DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class UpdateTimestamp:
    updated_at: Mapped[datetime] = mapped_column(
        name="updated_at",
        type_=DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class LifecyleTimestamp(UpdateTimestamp, CreationTimestamp):
    pass


class DeletionTimestamp:
    deleted_at: Mapped[OptDatetime] = mapped_column(
        name="deleted_at", type_=DateTime(timezone=True)
    )


class RestorationTimestamp:
    restored_at: Mapped[OptDatetime] = mapped_column(
        name="restored_at", type_=DateTime(timezone=True)
    )


class DeactivationTimestamp:
    deactivated_at: Mapped[OptDatetime] = mapped_column(
        name="deactivated_at", type_=DateTime(timezone=True)
    )


class ActivationTimestamp:
    activated_at: Mapped[datetime] = mapped_column(
        name="activated_at",
        type_=DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class StatusTimestamp(
    ActivationTimestamp, DeactivationTimestamp, RestorationTimestamp, DeletionTimestamp
):
    pass


class DataTimestamp(StatusTimestamp, LifecyleTimestamp):
    pass


class DataStatus:
    status: Mapped[DataStatusEnum] = mapped_column(
        name="status",
        type_=Enum(DataStatusEnum, name="statustype", create_constraints=True),
        default=DataStatusEnum.ACTIVE,
        nullable=False,
    )

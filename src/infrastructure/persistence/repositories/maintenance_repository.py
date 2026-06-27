"""Maintenance record repository."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.prediction.enums import MaintenanceStatus, MaintenanceType
from src.domain.prediction.maintenance_record import MaintenanceRecord
from src.infrastructure.persistence.models.prediction import MaintenanceRecordModel


class MaintenanceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, maintenance_id: UUID, tenant_id: UUID) -> MaintenanceRecord | None:
        result = await self._session.execute(
            select(MaintenanceRecordModel).where(
                MaintenanceRecordModel.id == maintenance_id,
                MaintenanceRecordModel.tenant_id == tenant_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        status: MaintenanceStatus | None = None,
        machine_id: UUID | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[MaintenanceRecord], int]:
        query = select(MaintenanceRecordModel).where(MaintenanceRecordModel.tenant_id == tenant_id)

        if status is not None:
            query = query.where(MaintenanceRecordModel.status == status.value)
        if machine_id is not None:
            query = query.where(MaintenanceRecordModel.machine_id == machine_id)

        count_result = await self._session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            query.order_by(MaintenanceRecordModel.scheduled_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        return [self._to_domain(m) for m in result.scalars().all()], total

    async def add(self, record: MaintenanceRecord) -> MaintenanceRecord:
        model = MaintenanceRecordModel(
            id=record.id,
            tenant_id=record.tenant_id,
            machine_id=record.machine_id,
            prediction_id=record.prediction_id,
            assigned_to=record.assigned_to,
            maintenance_type=record.maintenance_type.value,
            status=record.status.value,
            description=record.description,
            scheduled_at=record.scheduled_at,
            started_at=record.started_at,
            completed_at=record.completed_at,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return record

    async def update(self, record: MaintenanceRecord) -> MaintenanceRecord:
        result = await self._session.execute(
            select(MaintenanceRecordModel).where(
                MaintenanceRecordModel.id == record.id,
                MaintenanceRecordModel.tenant_id == record.tenant_id,
            )
        )
        model = result.scalar_one()
        model.status = record.status.value
        model.started_at = record.started_at
        model.completed_at = record.completed_at
        model.updated_at = record.updated_at
        await self._session.flush()
        return record

    async def has_scheduled_for_machine(self, machine_id: UUID, tenant_id: UUID) -> bool:
        result = await self._session.execute(
            select(func.count())
            .select_from(MaintenanceRecordModel)
            .where(
                MaintenanceRecordModel.machine_id == machine_id,
                MaintenanceRecordModel.tenant_id == tenant_id,
                MaintenanceRecordModel.status.in_(
                    [MaintenanceStatus.SCHEDULED.value, MaintenanceStatus.IN_PROGRESS.value]
                ),
            )
        )
        return result.scalar_one() > 0

    @staticmethod
    def _to_domain(model: MaintenanceRecordModel) -> MaintenanceRecord:
        return MaintenanceRecord(
            id=model.id,
            tenant_id=model.tenant_id,
            machine_id=model.machine_id,
            prediction_id=model.prediction_id,
            assigned_to=model.assigned_to,
            maintenance_type=MaintenanceType(model.maintenance_type),
            status=MaintenanceStatus(model.status),
            description=model.description,
            scheduled_at=model.scheduled_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

"""Maintenance workflow use cases."""

from uuid import UUID

import structlog

from src.application.dto.prediction import (
    CreateMaintenanceRequest,
    MaintenanceListResponse,
    MaintenanceResponse,
)
from src.domain.prediction.maintenance_record import MaintenanceRecord
from src.domain.prediction.enums import MaintenanceStatus
from src.domain.shared.exceptions import EntityNotFoundError
from src.infrastructure.persistence.repositories.machine_repository import MachineRepository
from src.infrastructure.persistence.repositories.maintenance_repository import MaintenanceRepository
from src.infrastructure.persistence.unit_of_work import SQLAlchemyUnitOfWork

logger = structlog.get_logger()


class MaintenanceService:
    def __init__(
        self,
        uow: SQLAlchemyUnitOfWork,
        machine_repo: MachineRepository,
        maintenance_repo: MaintenanceRepository,
    ) -> None:
        self._uow = uow
        self._machine_repo = machine_repo
        self._maintenance_repo = maintenance_repo

    async def list_maintenance(
        self,
        tenant_id: UUID,
        status: str | None = None,
        machine_id: UUID | None = None,
        page: int = 1,
        size: int = 20,
    ) -> MaintenanceListResponse:
        status_enum = MaintenanceStatus(status) if status else None
        size = min(size, 100)
        records, total = await self._maintenance_repo.list_by_tenant(
            tenant_id, status=status_enum, machine_id=machine_id, page=page, size=size
        )
        return MaintenanceListResponse(
            items=[self._to_response(r) for r in records],
            total=total,
            page=page,
            size=size,
        )

    async def create_maintenance(
        self, tenant_id: UUID, request: CreateMaintenanceRequest
    ) -> MaintenanceResponse:
        machine = await self._machine_repo.get_by_id(request.machine_id, tenant_id)
        if machine is None:
            raise EntityNotFoundError("Machine", request.machine_id)

        record = MaintenanceRecord.schedule(
            tenant_id=tenant_id,
            machine_id=request.machine_id,
            maintenance_type=request.maintenance_type,
            description=request.description,
            scheduled_at=request.scheduled_at,
            prediction_id=request.prediction_id,
            assigned_to=request.assigned_to,
        )
        await self._maintenance_repo.add(record)
        await self._uow.commit()
        logger.info("maintenance.created", maintenance_id=str(record.id))
        return self._to_response(record)

    async def start_maintenance(self, tenant_id: UUID, maintenance_id: UUID) -> MaintenanceResponse:
        record = await self._require_record(maintenance_id, tenant_id)
        machine = await self._machine_repo.get_by_id(record.machine_id, tenant_id)
        if machine is None:
            raise EntityNotFoundError("Machine", record.machine_id)

        record.start()
        machine.mark_maintenance()
        await self._maintenance_repo.update(record)
        await self._machine_repo.update(machine)
        await self._uow.commit()
        logger.info("maintenance.started", maintenance_id=str(maintenance_id))
        return self._to_response(record)

    async def complete_maintenance(
        self, tenant_id: UUID, maintenance_id: UUID
    ) -> MaintenanceResponse:
        record = await self._require_record(maintenance_id, tenant_id)
        machine = await self._machine_repo.get_by_id(record.machine_id, tenant_id)
        if machine is None:
            raise EntityNotFoundError("Machine", record.machine_id)

        record.complete()
        machine.complete_maintenance()
        await self._maintenance_repo.update(record)
        await self._machine_repo.update(machine)
        await self._uow.commit()
        logger.info("maintenance.completed", maintenance_id=str(maintenance_id))
        return self._to_response(record)

    async def _require_record(self, maintenance_id: UUID, tenant_id: UUID) -> MaintenanceRecord:
        record = await self._maintenance_repo.get_by_id(maintenance_id, tenant_id)
        if record is None:
            raise EntityNotFoundError("MaintenanceRecord", maintenance_id)
        return record

    @staticmethod
    def _to_response(record: MaintenanceRecord) -> MaintenanceResponse:
        return MaintenanceResponse(
            id=record.id,
            tenant_id=record.tenant_id,
            machine_id=record.machine_id,
            prediction_id=record.prediction_id,
            assigned_to=record.assigned_to,
            maintenance_type=record.maintenance_type,
            status=record.status,
            description=record.description,
            scheduled_at=record.scheduled_at,
            started_at=record.started_at,
            completed_at=record.completed_at,
            created_at=record.created_at,
        )

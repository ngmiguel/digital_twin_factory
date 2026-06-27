"""Maintenance record aggregate root."""

from datetime import datetime
from uuid import UUID

from src.domain.prediction.enums import MaintenanceStatus, MaintenanceType
from src.domain.prediction.events import MaintenanceCompleted, MaintenanceScheduled, MaintenanceStarted
from src.domain.shared.aggregate_root import AggregateRoot
from src.domain.shared.entity import Entity
from src.domain.shared.exceptions import ValidationError


class MaintenanceRecord(AggregateRoot):
    tenant_id: UUID
    machine_id: UUID
    prediction_id: UUID | None
    assigned_to: UUID | None
    maintenance_type: MaintenanceType
    status: MaintenanceStatus
    description: str
    scheduled_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @classmethod
    def schedule(
        cls,
        tenant_id: UUID,
        machine_id: UUID,
        maintenance_type: MaintenanceType,
        description: str,
        scheduled_at: datetime | None = None,
        prediction_id: UUID | None = None,
        assigned_to: UUID | None = None,
    ) -> "MaintenanceRecord":
        if not description.strip():
            raise ValidationError("Description is required", field="description")

        now = Entity.now()
        record = cls(
            id=Entity.new_id(),
            tenant_id=tenant_id,
            machine_id=machine_id,
            prediction_id=prediction_id,
            assigned_to=assigned_to,
            maintenance_type=maintenance_type,
            status=MaintenanceStatus.SCHEDULED,
            description=description.strip(),
            scheduled_at=scheduled_at or now,
            created_at=now,
            updated_at=now,
        )
        record.add_event(
            MaintenanceScheduled.create(
                tenant_id=tenant_id,
                aggregate_id=record.id,
                maintenance_id=record.id,
                machine_id=machine_id,
                maintenance_type=maintenance_type.value,
            )
        )
        return record

    def start(self) -> None:
        if self.status != MaintenanceStatus.SCHEDULED:
            raise ValidationError("Only scheduled maintenance can be started", field="status")
        self.status = MaintenanceStatus.IN_PROGRESS
        self.started_at = Entity.now()
        self.updated_at = Entity.now()
        self.add_event(
            MaintenanceStarted.create(
                tenant_id=self.tenant_id,
                aggregate_id=self.id,
                maintenance_id=self.id,
                machine_id=self.machine_id,
            )
        )

    def complete(self) -> None:
        if self.status != MaintenanceStatus.IN_PROGRESS:
            raise ValidationError("Only in-progress maintenance can be completed", field="status")
        self.status = MaintenanceStatus.COMPLETED
        self.completed_at = Entity.now()
        self.updated_at = Entity.now()
        self.add_event(
            MaintenanceCompleted.create(
                tenant_id=self.tenant_id,
                aggregate_id=self.id,
                maintenance_id=self.id,
                machine_id=self.machine_id,
            )
        )

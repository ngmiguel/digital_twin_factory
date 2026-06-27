"""Alert aggregate root."""

from datetime import datetime
from uuid import UUID

from src.domain.monitoring.enums import AlertSeverity, AlertType
from src.domain.monitoring.events import AlertAcknowledged, AlertRaised, AlertResolved
from src.domain.shared.aggregate_root import AggregateRoot
from src.domain.shared.entity import Entity
from src.domain.shared.exceptions import ValidationError


class Alert(AggregateRoot):
    tenant_id: UUID
    machine_id: UUID
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    metadata: dict[str, object]
    is_acknowledged: bool = False
    acknowledged_by: UUID | None = None
    acknowledged_at: datetime | None = None
    is_resolved: bool = False
    resolved_at: datetime | None = None

    @classmethod
    def raise_alert(
        cls,
        tenant_id: UUID,
        machine_id: UUID,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        metadata: dict[str, object] | None = None,
    ) -> "Alert":
        now = Entity.now()
        alert = cls(
            id=Entity.new_id(),
            tenant_id=tenant_id,
            machine_id=machine_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            metadata=metadata or {},
            is_acknowledged=False,
            is_resolved=False,
            created_at=now,
            updated_at=now,
        )
        alert.add_event(
            AlertRaised.create(
                tenant_id=tenant_id,
                aggregate_id=alert.id,
                alert_id=alert.id,
                machine_id=machine_id,
                severity=severity.value,
                alert_type=alert_type.value,
                message=message,
            )
        )
        return alert

    def acknowledge(self, user_id: UUID) -> None:
        if self.is_resolved:
            raise ValidationError("Cannot acknowledge a resolved alert")
        self.is_acknowledged = True
        self.acknowledged_by = user_id
        self.acknowledged_at = Entity.now()
        self.updated_at = Entity.now()
        self.add_event(
            AlertAcknowledged.create(
                tenant_id=self.tenant_id,
                aggregate_id=self.id,
                alert_id=self.id,
                user_id=user_id,
            )
        )

    def resolve(self, resolution: str) -> None:
        if not resolution.strip():
            raise ValidationError("Resolution message is required", field="resolution")
        self.is_resolved = True
        self.resolved_at = Entity.now()
        self.updated_at = Entity.now()
        self.add_event(
            AlertResolved.create(
                tenant_id=self.tenant_id,
                aggregate_id=self.id,
                alert_id=self.id,
                resolution=resolution,
            )
        )

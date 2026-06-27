"""Monitoring domain events."""

from uuid import UUID

from src.domain.shared.domain_event import DomainEvent


class AlertRaised(DomainEvent):
    alert_id: UUID
    machine_id: UUID
    severity: str
    alert_type: str
    message: str


class AlertAcknowledged(DomainEvent):
    alert_id: UUID
    user_id: UUID


class AlertResolved(DomainEvent):
    alert_id: UUID
    resolution: str

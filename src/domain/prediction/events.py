"""Prediction domain events."""

from uuid import UUID

from src.domain.shared.domain_event import DomainEvent


class FailurePredicted(DomainEvent):
    prediction_id: UUID
    machine_id: UUID
    confidence: float
    prediction_type: str


class MaintenanceScheduled(DomainEvent):
    maintenance_id: UUID
    machine_id: UUID
    maintenance_type: str


class MaintenanceStarted(DomainEvent):
    maintenance_id: UUID
    machine_id: UUID


class MaintenanceCompleted(DomainEvent):
    maintenance_id: UUID
    machine_id: UUID

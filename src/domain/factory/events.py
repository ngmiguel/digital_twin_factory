"""Factory bounded context domain events."""

from uuid import UUID

from src.domain.shared.domain_event import DomainEvent


class FactoryCreated(DomainEvent):
    name: str
    location: str | None = None


class FactoryUpdated(DomainEvent):
    factory_id: UUID


class FactoryDeleted(DomainEvent):
    factory_id: UUID


class ProductionLineAdded(DomainEvent):
    factory_id: UUID
    line_id: UUID
    name: str


class MachineProvisioned(DomainEvent):
    machine_id: UUID
    machine_type: str
    production_line_id: UUID


class MachineStatusChanged(DomainEvent):
    machine_id: UUID
    old_status: str
    new_status: str

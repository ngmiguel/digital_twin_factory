"""Base domain event."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.domain.shared.value_object import ValueObject


class DomainEvent(ValueObject):
    """Base class for all domain events."""

    event_id: UUID
    occurred_at: datetime
    tenant_id: UUID | None = None
    aggregate_id: UUID | None = None

    @classmethod
    def create(
        cls,
        tenant_id: UUID | None = None,
        aggregate_id: UUID | None = None,
        **kwargs: object,
    ) -> "DomainEvent":
        return cls(
            event_id=uuid4(),
            occurred_at=datetime.now(UTC),
            tenant_id=tenant_id,
            aggregate_id=aggregate_id,
            **kwargs,
        )

"""Base aggregate root."""

from pydantic import PrivateAttr

from src.domain.shared.domain_event import DomainEvent
from src.domain.shared.entity import Entity


class AggregateRoot(Entity):
    """Aggregate root with domain event collection."""

    _events: list[DomainEvent] = PrivateAttr(default_factory=list)

    def add_event(self, event: DomainEvent) -> None:
        self._events.append(event)

    def clear_events(self) -> None:
        self._events.clear()

    @property
    def events(self) -> list[DomainEvent]:
        return list(self._events)

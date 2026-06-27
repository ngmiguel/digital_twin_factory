"""In-process domain event bus."""

from collections import defaultdict
from collections.abc import Callable, Coroutine
from typing import Any

from src.domain.shared.domain_event import DomainEvent

EventHandler = Callable[[DomainEvent], Coroutine[Any, Any, None]]


class EventBus:
    """Simple in-process event dispatcher for domain events."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._handlers[event_type].append(handler)

    async def publish(self, event: DomainEvent) -> None:
        event_type = type(event).__name__
        for handler in self._handlers.get(event_type, []):
            await handler(event)

    async def publish_all(self, events: list[DomainEvent]) -> None:
        for event in events:
            await self.publish(event)

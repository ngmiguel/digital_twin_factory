"""WebSocket connection tracking."""

from dataclasses import dataclass, field
from uuid import UUID

from fastapi import WebSocket


@dataclass
class ConnectionManager:
    """Track active WebSocket connections per factory."""

    _connections: dict[str, set[WebSocket]] = field(default_factory=dict)

    def _key(self, tenant_id: UUID, factory_id: UUID) -> str:
        return f"{tenant_id}:{factory_id}"

    async def connect(self, tenant_id: UUID, factory_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        key = self._key(tenant_id, factory_id)
        if key not in self._connections:
            self._connections[key] = set()
        self._connections[key].add(websocket)

    def disconnect(self, tenant_id: UUID, factory_id: UUID, websocket: WebSocket) -> None:
        key = self._key(tenant_id, factory_id)
        if key in self._connections:
            self._connections[key].discard(websocket)
            if not self._connections[key]:
                del self._connections[key]

    def count(self, tenant_id: UUID, factory_id: UUID) -> int:
        key = self._key(tenant_id, factory_id)
        return len(self._connections.get(key, set()))

    @property
    def total_connections(self) -> int:
        return sum(len(conns) for conns in self._connections.values())


factory_connection_manager = ConnectionManager()

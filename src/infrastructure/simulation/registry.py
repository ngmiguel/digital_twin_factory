"""Redis-backed simulation registry for active machines."""

import json
from uuid import UUID

import redis

from src.domain.simulation.simulation_state import SimulationState
from src.infrastructure.config.settings import get_settings

_ACTIVE_SET_KEY = "simulation:active_machines"
_STATE_KEY_PREFIX = "simulation:state:"


class SimulationRegistry:
    """Track active simulations and per-machine state in Redis."""

    def __init__(self, client: redis.Redis) -> None:
        self._client = client

    @classmethod
    def from_settings(cls) -> "SimulationRegistry":
        settings = get_settings()
        client = redis.from_url(settings.redis_url, decode_responses=True)
        return cls(client)

    def _member_key(self, tenant_id: UUID, machine_id: UUID) -> str:
        return f"{tenant_id}:{machine_id}"

    def register(self, tenant_id: UUID, machine_id: UUID) -> None:
        self._client.sadd(_ACTIVE_SET_KEY, self._member_key(tenant_id, machine_id))
        self._save_state(machine_id, SimulationState())

    def unregister(self, tenant_id: UUID, machine_id: UUID) -> None:
        self._client.srem(_ACTIVE_SET_KEY, self._member_key(tenant_id, machine_id))
        self._client.delete(self._state_key(machine_id))

    def list_active(self) -> list[tuple[UUID, UUID]]:
        members = self._client.smembers(_ACTIVE_SET_KEY)
        result: list[tuple[UUID, UUID]] = []
        for member in members:
            tenant_str, machine_str = member.split(":", 1)
            result.append((UUID(tenant_str), UUID(machine_str)))
        return result

    def get_state(self, machine_id: UUID) -> SimulationState:
        raw = self._client.get(self._state_key(machine_id))
        if raw is None:
            return SimulationState()
        data = json.loads(raw)
        return SimulationState(
            tick_count=int(data.get("tick_count", 0)),
            degradation_factor=float(data.get("degradation_factor", 1.0)),
            elapsed_seconds=float(data.get("elapsed_seconds", 0.0)),
        )

    def save_state(self, machine_id: UUID, state: SimulationState) -> None:
        self._save_state(machine_id, state)

    def _state_key(self, machine_id: UUID) -> str:
        return f"{_STATE_KEY_PREFIX}{machine_id}"

    def _save_state(self, machine_id: UUID, state: SimulationState) -> None:
        self._client.set(
            self._state_key(machine_id),
            json.dumps(
                {
                    "tick_count": state.tick_count,
                    "degradation_factor": state.degradation_factor,
                    "elapsed_seconds": state.elapsed_seconds,
                }
            ),
            ex=86400,
        )

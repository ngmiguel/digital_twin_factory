"""Simulation coordination — register machines with Celery/Redis."""

from uuid import UUID

from src.infrastructure.simulation.registry import SimulationRegistry


class SimulationCoordinator:
    """Start and stop virtual machine simulation loops."""

    def __init__(self, registry: SimulationRegistry) -> None:
        self._registry = registry

    def start_simulation(self, tenant_id: UUID, machine_id: UUID) -> None:
        self._registry.register(tenant_id, machine_id)

    def stop_simulation(self, tenant_id: UUID, machine_id: UUID) -> None:
        self._registry.unregister(tenant_id, machine_id)

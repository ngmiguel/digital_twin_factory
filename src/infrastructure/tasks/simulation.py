"""Celery simulation tasks."""

import asyncio
from uuid import UUID

from src.infrastructure.simulation.registry import SimulationRegistry
from src.infrastructure.simulation.tick_runner import run_machine_tick
from src.infrastructure.tasks.celery_app import celery_app


@celery_app.task(name="src.infrastructure.tasks.simulation.simulate_machine_tick", bind=True, max_retries=3)
def simulate_machine_tick(self, machine_id: str, tenant_id: str) -> dict[str, object]:
    try:
        return asyncio.run(run_machine_tick(UUID(machine_id), UUID(tenant_id)))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=1) from exc


@celery_app.task(name="src.infrastructure.tasks.simulation.dispatch_simulation_ticks")
def dispatch_simulation_ticks() -> dict[str, object]:
    registry = SimulationRegistry.from_settings()
    active = registry.list_active()
    dispatched = 0
    for tenant_id, machine_id in active:
        simulate_machine_tick.delay(str(machine_id), str(tenant_id))
        dispatched += 1
    return {"status": "ok", "dispatched": dispatched}

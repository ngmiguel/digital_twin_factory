"""Async simulation tick execution — used by Celery workers."""

import json
from datetime import UTC, datetime
from uuid import UUID

import redis.asyncio as aioredis
import structlog

from src.domain.factory.enums import MachineStatus
from src.domain.simulation.virtual_machine_engine import VirtualMachineEngine
from src.infrastructure.config.settings import get_settings
from src.infrastructure.persistence.database import _session_factory
from src.infrastructure.persistence.repositories.machine_repository import MachineRepository
from src.infrastructure.persistence.repositories.metric_repository import MetricRepository
from src.infrastructure.simulation.registry import SimulationRegistry

logger = structlog.get_logger()
_engine = VirtualMachineEngine()


async def run_machine_tick(machine_id: UUID, tenant_id: UUID) -> dict[str, object]:
    if _session_factory is None:
        raise RuntimeError("Database not initialized")

    settings = get_settings()
    sync_registry = SimulationRegistry.from_settings()
    redis_async = aioredis.from_url(settings.redis_url, decode_responses=True)

    async with _session_factory() as session:
        machine_repo = MachineRepository(session)
        metric_repo = MetricRepository(session)

        machine = await machine_repo.get_by_id(machine_id, tenant_id)
        if machine is None:
            sync_registry.unregister(tenant_id, machine_id)
            return {"status": "skipped", "reason": "machine_not_found"}

        if machine.status not in (MachineStatus.RUNNING, MachineStatus.DEGRADED):
            sync_registry.unregister(tenant_id, machine_id)
            return {"status": "skipped", "reason": "machine_not_running"}

        state = sync_registry.get_state(machine_id)
        result = _engine.tick(machine, state)
        sync_registry.save_state(machine_id, result.state)

        if result.new_status is not None:
            machine.status = result.new_status
            if result.new_status == MachineStatus.FAILURE:
                sync_registry.unregister(tenant_id, machine_id)

        await metric_repo.add_snapshot(machine_id, tenant_id, result.metrics)
        await machine_repo.update(machine)
        await session.commit()

        factory_id = await machine_repo.get_factory_id(machine_id, tenant_id)
        if factory_id is not None:
            channel = f"tenant:{tenant_id}:factory:{factory_id}:metrics"
            payload = json.dumps(
                {
                    "type": "metric",
                    "factory_id": str(factory_id),
                    "machine_id": str(machine_id),
                    "data": {
                        "temperature": result.metrics.temperature,
                        "vibration": result.metrics.vibration,
                        "power_consumption": result.metrics.power_consumption,
                        "production_rate": result.metrics.production_rate,
                        "status": result.metrics.machine_status.value,
                    },
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )
            await redis_async.publish(channel, payload)

            latest_key = f"tenant:{tenant_id}:machine:{machine_id}:latest"
            await redis_async.hset(
                latest_key,
                mapping={
                    "temperature": str(result.metrics.temperature),
                    "vibration": str(result.metrics.vibration),
                    "power_consumption": str(result.metrics.power_consumption),
                    "production_rate": str(result.metrics.production_rate),
                    "status": result.metrics.machine_status.value,
                },
            )
            await redis_async.expire(latest_key, 60)

        await redis_async.aclose()

        logger.info(
            "simulation.tick",
            machine_id=str(machine_id),
            tenant_id=str(tenant_id),
            temperature=result.metrics.temperature,
        )

        return {
            "status": "ok",
            "machine_id": str(machine_id),
            "temperature": result.metrics.temperature,
        }

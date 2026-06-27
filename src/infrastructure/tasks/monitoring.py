"""Celery monitoring tasks."""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog

from src.infrastructure.persistence.database import _session_factory
from src.infrastructure.persistence.repositories.metric_repository import MetricRepository
from src.infrastructure.tasks.celery_app import celery_app
from src.infrastructure.tasks.prediction import detect_anomalies

logger = structlog.get_logger()


async def _aggregate_metrics_for_machine(machine_id: UUID, tenant_id: UUID) -> dict[str, object]:
    if _session_factory is None:
        raise RuntimeError("Database not initialized")

    async with _session_factory() as session:
        metric_repo = MetricRepository(session)
        snapshots = await metric_repo.list_recent(machine_id, tenant_id, hours=1)
        if len(snapshots) < 5:
            return {"status": "skipped", "reason": "insufficient_data"}

        temps = [s.temperature for s in snapshots]
        vibs = [s.vibration for s in snapshots]
        avg_temp = sum(temps) / len(temps)
        avg_vib = sum(vibs) / len(vibs)

        if avg_temp > 80 or avg_vib > 6:
            return {"status": "anomaly_detected", "avg_temp": avg_temp, "avg_vib": avg_vib}

        return {"status": "ok", "avg_temp": avg_temp, "avg_vib": avg_vib}


@celery_app.task(name="src.infrastructure.tasks.monitoring.aggregate_metrics")
def aggregate_metrics(tenant_id: str | None = None) -> dict[str, object]:
    """Aggregate recent metrics and dispatch anomaly detection for active machines."""
    from src.infrastructure.simulation.registry import SimulationRegistry

    registry = SimulationRegistry.from_settings()
    active = registry.list_active()
    dispatched = 0

    for tid, machine_id in active:
        if tenant_id is not None and str(tid) != tenant_id:
            continue
        result = asyncio.run(_aggregate_metrics_for_machine(machine_id, tid))
        if result.get("status") == "anomaly_detected":
            detect_anomalies.delay(str(machine_id), str(tid))
            dispatched += 1

    logger.info("monitoring.aggregate_metrics", dispatched=dispatched)
    return {"status": "ok", "anomaly_checks_dispatched": dispatched}


@celery_app.task(name="src.infrastructure.tasks.maintenance.cleanup_old_metrics")
def cleanup_old_metrics(retention_days: int = 90) -> dict[str, object]:
    """Remove metrics older than retention period."""
    if _session_factory is None:
        return {"status": "error", "reason": "db_not_initialized"}

    cutoff = datetime.now(UTC) - timedelta(days=retention_days)

    async def _cleanup() -> int:
        from sqlalchemy import delete

        from src.infrastructure.persistence.models.metrics import MachineMetricModel

        async with _session_factory() as session:
            result = await session.execute(
                delete(MachineMetricModel).where(MachineMetricModel.recorded_at < cutoff)
            )
            await session.commit()
            return result.rowcount or 0

    deleted = asyncio.run(_cleanup())
    logger.info("maintenance.cleanup_metrics", deleted=deleted, retention_days=retention_days)
    return {"status": "ok", "deleted": deleted}

"""Async prediction runner for Celery workers."""

from uuid import UUID

import structlog

from src.application.handlers.prediction.prediction_service import PredictionService
from src.infrastructure.persistence.database import _session_factory
from src.infrastructure.persistence.repositories.machine_repository import MachineRepository
from src.infrastructure.persistence.repositories.maintenance_repository import MaintenanceRepository
from src.infrastructure.persistence.repositories.metric_repository import MetricRepository
from src.infrastructure.persistence.repositories.prediction_repository import PredictionRepository
from src.infrastructure.persistence.unit_of_work import SQLAlchemyUnitOfWork
from src.infrastructure.simulation.registry import SimulationRegistry

logger = structlog.get_logger()


async def run_failure_prediction_for_machine(machine_id: UUID, tenant_id: UUID) -> dict[str, object]:
    if _session_factory is None:
        raise RuntimeError("Database not initialized")

    async with _session_factory() as session:
        service = PredictionService(
            uow=SQLAlchemyUnitOfWork(session),
            machine_repo=MachineRepository(session),
            metric_repo=MetricRepository(session),
            prediction_repo=PredictionRepository(session),
            maintenance_repo=MaintenanceRepository(session),
        )
        prediction = await service.run_failure_prediction(tenant_id, machine_id)
        if prediction is None:
            return {"status": "skipped", "machine_id": str(machine_id)}
        return {
            "status": "ok",
            "machine_id": str(machine_id),
            "prediction_id": str(prediction.id),
            "confidence": prediction.confidence,
        }


async def run_failure_prediction_all() -> dict[str, object]:
    registry = SimulationRegistry.from_settings()
    active = registry.list_active()
    processed = 0
    created = 0

    for tenant_id, machine_id in active:
        result = await run_failure_prediction_for_machine(machine_id, tenant_id)
        processed += 1
        if result.get("status") == "ok":
            created += 1

    logger.info("prediction.batch", processed=processed, created=created)
    return {"status": "ok", "processed": processed, "created": created}

"""Celery prediction tasks."""

import asyncio
from uuid import UUID

from src.infrastructure.prediction.prediction_runner import (
    run_failure_prediction_all,
    run_failure_prediction_for_machine,
)
from src.infrastructure.tasks.celery_app import celery_app


@celery_app.task(name="src.infrastructure.tasks.prediction.run_failure_prediction", bind=True, max_retries=2)
def run_failure_prediction(self, machine_id: str, tenant_id: str) -> dict[str, object]:
    try:
        return asyncio.run(
            run_failure_prediction_for_machine(UUID(machine_id), UUID(tenant_id))
        )
    except Exception as exc:
        raise self.retry(exc=exc, countdown=5) from exc


@celery_app.task(name="src.infrastructure.tasks.prediction.run_failure_prediction_all")
def run_failure_prediction_all_task() -> dict[str, object]:
    return asyncio.run(run_failure_prediction_all())


@celery_app.task(name="src.infrastructure.tasks.prediction.detect_anomalies")
def detect_anomalies(machine_id: str, tenant_id: str) -> dict[str, object]:
    """Chain to failure prediction when anomaly score exceeds threshold."""
    return run_failure_prediction(machine_id, tenant_id)

"""Celery task definitions."""

from src.infrastructure.tasks.celery_app import celery_app


@celery_app.task(name="src.infrastructure.tasks.monitoring.aggregate_metrics")
def aggregate_metrics(tenant_id: str | None = None) -> dict[str, str]:
    """Aggregate raw metrics into 5-minute buckets. Implemented in feat(monitoring)."""
    return {"status": "pending", "task": "aggregate_metrics"}


@celery_app.task(name="src.infrastructure.tasks.maintenance.cleanup_old_metrics")
def cleanup_old_metrics() -> dict[str, str]:
    """Remove metrics older than retention period. Implemented in feat(monitoring)."""
    return {"status": "pending", "task": "cleanup_old_metrics"}


@celery_app.task(name="src.infrastructure.tasks.maintenance.cleanup_expired_tokens")
def cleanup_expired_tokens() -> dict[str, str]:
    """Remove expired refresh tokens from Redis. Implemented in feat(auth)."""
    return {"status": "pending", "task": "cleanup_expired_tokens"}

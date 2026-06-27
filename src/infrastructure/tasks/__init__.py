"""Celery task definitions."""

from src.infrastructure.tasks.celery_app import celery_app


@celery_app.task(name="src.infrastructure.tasks.maintenance.cleanup_expired_tokens")
def cleanup_expired_tokens() -> dict[str, str]:
    """Remove expired refresh tokens from Redis."""
    return {"status": "pending", "task": "cleanup_expired_tokens"}


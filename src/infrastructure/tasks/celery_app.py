"""Celery application configuration."""

from celery import Celery

from src.infrastructure.config.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "digital_twin_factory",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "src.infrastructure.tasks.simulation.*": {"queue": "simulation"},
        "src.infrastructure.tasks.monitoring.*": {"queue": "monitoring"},
        "src.infrastructure.tasks.prediction.*": {"queue": "prediction"},
        "src.infrastructure.tasks.notification.*": {"queue": "notification"},
        "src.infrastructure.tasks.maintenance.*": {"queue": "maintenance"},
    },
    beat_schedule={
        "aggregate-metrics": {
            "task": "src.infrastructure.tasks.monitoring.aggregate_metrics",
            "schedule": 300.0,
        },
        "cleanup-old-metrics": {
            "task": "src.infrastructure.tasks.maintenance.cleanup_old_metrics",
            "schedule": 86400.0,
        },
        "cleanup-expired-tokens": {
            "task": "src.infrastructure.tasks.maintenance.cleanup_expired_tokens",
            "schedule": 86400.0,
        },
    },
)

celery_app.autodiscover_tasks(
    [
        "src.infrastructure.tasks",
    ]
)

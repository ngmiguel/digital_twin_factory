"""Celery application configuration."""

from celery import Celery
from celery.signals import worker_process_init

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
        "dispatch-simulation-ticks": {
            "task": "src.infrastructure.tasks.simulation.dispatch_simulation_ticks",
            "schedule": 1.0,
        },
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
        "run-failure-predictions": {
            "task": "src.infrastructure.tasks.prediction.run_failure_prediction_all",
            "schedule": 900.0,
        },
    },
)

celery_app.autodiscover_tasks(
    [
        "src.infrastructure.tasks",
        "src.infrastructure.tasks.simulation",
        "src.infrastructure.tasks.monitoring",
        "src.infrastructure.tasks.prediction",
        "src.infrastructure.tasks.maintenance",
    ]
)


@worker_process_init.connect
def init_celery_worker(**_kwargs: object) -> None:
    from src.infrastructure.persistence.database import init_db

    init_db(get_settings())

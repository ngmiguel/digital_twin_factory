"""Celery notification tasks."""

import asyncio
from uuid import UUID

from src.infrastructure.notification.notification_runner import (
    notify_alert_task,
    notify_maintenance_task,
    send_notification_task,
)
from src.infrastructure.tasks.celery_app import celery_app


@celery_app.task(
    name="src.infrastructure.tasks.notification.send_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=5,
)
def send_notification(
    self,
    tenant_id: str,
    user_id: str,
    subject: str,
    body: str,
    alert_id: str | None = None,
    metadata: dict[str, object] | None = None,
) -> dict[str, object]:
    try:
        return asyncio.run(
            send_notification_task(
                UUID(tenant_id),
                UUID(user_id),
                subject,
                body,
                UUID(alert_id) if alert_id else None,
                metadata,
            )
        )
    except Exception as exc:
        raise self.retry(exc=exc, countdown=5) from exc


@celery_app.task(name="src.infrastructure.tasks.notification.notify_alert")
def notify_alert(
    tenant_id: str,
    alert_id: str,
    severity: str,
    message: str,
    machine_id: str,
    alert_type: str,
) -> dict[str, object]:
    return asyncio.run(
        notify_alert_task(
            UUID(tenant_id),
            UUID(alert_id),
            severity,
            message,
            UUID(machine_id),
            alert_type,
        )
    )


@celery_app.task(name="src.infrastructure.tasks.notification.notify_maintenance")
def notify_maintenance(
    tenant_id: str,
    maintenance_id: str,
    machine_id: str,
    description: str,
) -> dict[str, object]:
    return asyncio.run(
        notify_maintenance_task(
            UUID(tenant_id),
            UUID(maintenance_id),
            UUID(machine_id),
            description,
        )
    )

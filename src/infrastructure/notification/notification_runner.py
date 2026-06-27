"""Async notification runner for Celery workers."""

from uuid import UUID

from src.application.handlers.notification.notification_service import NotificationService
from src.infrastructure.cache.redis_client import _redis_client
from src.infrastructure.persistence.database import _session_factory
from src.infrastructure.persistence.repositories.notification_repository import NotificationRepository
from src.infrastructure.persistence.repositories.user_repository import UserRepository
from src.infrastructure.persistence.unit_of_work import SQLAlchemyUnitOfWork


async def send_notification_task(
    tenant_id: UUID,
    user_id: UUID,
    subject: str,
    body: str,
    alert_id: UUID | None = None,
    metadata: dict[str, object] | None = None,
) -> dict[str, object]:
    if _session_factory is None:
        raise RuntimeError("Database not initialized")

    async with _session_factory() as session:
        service = NotificationService(
            uow=SQLAlchemyUnitOfWork(session),
            notification_repo=NotificationRepository(session),
            user_repo=UserRepository(session),
            redis=_redis_client,
        )
        notifications = await service.send_to_user(
            tenant_id, user_id, subject, body, alert_id=alert_id, metadata=metadata
        )
        return {"status": "ok", "count": len(notifications)}


async def notify_alert_task(
    tenant_id: UUID,
    alert_id: UUID,
    severity: str,
    message: str,
    machine_id: UUID,
    alert_type: str,
) -> dict[str, object]:
    if _session_factory is None:
        raise RuntimeError("Database not initialized")

    async with _session_factory() as session:
        service = NotificationService(
            uow=SQLAlchemyUnitOfWork(session),
            notification_repo=NotificationRepository(session),
            user_repo=UserRepository(session),
            redis=_redis_client,
        )
        count = await service.notify_alert(
            tenant_id, alert_id, severity, message, machine_id, alert_type
        )
        return {"status": "ok", "notified_users": count}


async def notify_maintenance_task(
    tenant_id: UUID,
    maintenance_id: UUID,
    machine_id: UUID,
    description: str,
) -> dict[str, object]:
    if _session_factory is None:
        raise RuntimeError("Database not initialized")

    async with _session_factory() as session:
        service = NotificationService(
            uow=SQLAlchemyUnitOfWork(session),
            notification_repo=NotificationRepository(session),
            user_repo=UserRepository(session),
            redis=_redis_client,
        )
        count = await service.notify_maintenance_scheduled(
            tenant_id, maintenance_id, machine_id, description
        )
        return {"status": "ok", "notified_users": count}

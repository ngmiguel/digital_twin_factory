"""Notification delivery use cases."""

import json
from datetime import UTC, datetime
from uuid import UUID

import structlog
from redis.asyncio import Redis

from src.application.dto.notification import NotificationListResponse, NotificationResponse
from src.domain.notification.enums import NotificationChannel, NotificationStatus
from src.domain.notification.notification import Notification
from src.domain.shared.exceptions import EntityNotFoundError
from src.infrastructure.messaging.redis_channels import user_notifications_channel
from src.infrastructure.notification.email_sender import EmailMessage, EmailSender, StubEmailSender
from src.infrastructure.persistence.repositories.notification_repository import NotificationRepository
from src.infrastructure.persistence.repositories.user_repository import UserRepository
from src.infrastructure.persistence.unit_of_work import SQLAlchemyUnitOfWork

logger = structlog.get_logger()

_DEFAULT_ALERT_ROLES = ["maintenance_engineer", "tenant_admin", "factory_manager"]


class NotificationService:
    def __init__(
        self,
        uow: SQLAlchemyUnitOfWork,
        notification_repo: NotificationRepository,
        user_repo: UserRepository,
        redis: Redis | None = None,
        email_sender: EmailSender | None = None,
    ) -> None:
        self._uow = uow
        self._notification_repo = notification_repo
        self._user_repo = user_repo
        self._redis = redis
        self._email_sender = email_sender or StubEmailSender()

    async def list_notifications(
        self,
        tenant_id: UUID,
        user_id: UUID,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> NotificationListResponse:
        status_enum = NotificationStatus(status) if status else None
        size = min(size, 100)
        notifications, total = await self._notification_repo.list_by_user(
            user_id, tenant_id, status=status_enum, page=page, size=size
        )
        return NotificationListResponse(
            items=[self._to_response(n) for n in notifications],
            total=total,
            page=page,
            size=size,
        )

    async def mark_delivered(self, tenant_id: UUID, user_id: UUID, notification_id: UUID) -> NotificationResponse:
        notification = await self._require_notification(notification_id, tenant_id, user_id)
        notification.mark_delivered()
        await self._notification_repo.update(notification)
        await self._uow.commit()
        return self._to_response(notification)

    async def send_to_user(
        self,
        tenant_id: UUID,
        user_id: UUID,
        subject: str,
        body: str,
        channels: list[NotificationChannel] | None = None,
        alert_id: UUID | None = None,
        metadata: dict[str, object] | None = None,
    ) -> list[Notification]:
        channels = channels or [NotificationChannel.IN_APP, NotificationChannel.EMAIL]
        sent: list[Notification] = []

        for channel in channels:
            notification = Notification.create(
                tenant_id=tenant_id,
                user_id=user_id,
                channel=channel,
                subject=subject,
                body=body,
                alert_id=alert_id,
                metadata=metadata,
            )
            success = await self._dispatch(notification)
            if success:
                notification.mark_sent()
                if channel == NotificationChannel.IN_APP:
                    notification.mark_delivered()
            else:
                notification.mark_failed("delivery_failed")

            await self._notification_repo.add(notification)
            sent.append(notification)

        await self._uow.commit()
        logger.info(
            "notification.sent",
            user_id=str(user_id),
            channels=[c.value for c in channels],
        )
        return sent

    async def notify_roles(
        self,
        tenant_id: UUID,
        role_names: list[str],
        subject: str,
        body: str,
        channels: list[NotificationChannel] | None = None,
        alert_id: UUID | None = None,
        metadata: dict[str, object] | None = None,
    ) -> int:
        user_ids = await self._user_repo.list_user_ids_by_roles(tenant_id, role_names)
        count = 0
        for user_id in user_ids:
            await self.send_to_user(
                tenant_id,
                user_id,
                subject,
                body,
                channels=channels,
                alert_id=alert_id,
                metadata=metadata,
            )
            count += 1
        return count

    async def notify_alert(
        self,
        tenant_id: UUID,
        alert_id: UUID,
        severity: str,
        message: str,
        machine_id: UUID,
        alert_type: str,
    ) -> int:
        subject = f"[{severity}] Alert: {alert_type}"
        body = message
        metadata: dict[str, object] = {
            "type": "ALERT",
            "machine_id": str(machine_id),
            "alert_type": alert_type,
            "severity": severity,
        }
        return await self.notify_roles(
            tenant_id,
            _DEFAULT_ALERT_ROLES,
            subject,
            body,
            alert_id=alert_id,
            metadata=metadata,
        )

    async def notify_maintenance_scheduled(
        self,
        tenant_id: UUID,
        maintenance_id: UUID,
        machine_id: UUID,
        description: str,
    ) -> int:
        subject = "Maintenance scheduled"
        body = description
        metadata: dict[str, object] = {
            "type": "MAINTENANCE",
            "maintenance_id": str(maintenance_id),
            "machine_id": str(machine_id),
        }
        return await self.notify_roles(
            tenant_id,
            ["maintenance_engineer"],
            subject,
            body,
            metadata=metadata,
        )

    async def _dispatch(self, notification: Notification) -> bool:
        if notification.channel == NotificationChannel.IN_APP:
            return await self._publish_in_app(notification)
        if notification.channel == NotificationChannel.EMAIL:
            return await self._send_email(notification)
        return False

    async def _publish_in_app(self, notification: Notification) -> bool:
        if self._redis is None:
            logger.warning("notification.redis_unavailable", notification_id=str(notification.id))
            return False

        channel = user_notifications_channel(notification.tenant_id, notification.user_id)
        payload = json.dumps(
            {
                "type": "notification",
                "notification_id": str(notification.id),
                "subject": notification.subject,
                "body": notification.body,
                "metadata": notification.metadata,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        await self._redis.publish(channel, payload)
        return True

    async def _send_email(self, notification: Notification) -> bool:
        email = await self._user_repo.get_email(notification.user_id)
        if email is None:
            return False
        return await self._email_sender.send(
            EmailMessage(to_email=email, subject=notification.subject, body=notification.body)
        )

    async def _require_notification(
        self, notification_id: UUID, tenant_id: UUID, user_id: UUID
    ) -> Notification:
        notification = await self._notification_repo.get_by_id(notification_id, tenant_id)
        if notification is None or notification.user_id != user_id:
            raise EntityNotFoundError("Notification", notification_id)
        return notification

    @staticmethod
    def _to_response(notification: Notification) -> NotificationResponse:
        return NotificationResponse(
            id=notification.id,
            tenant_id=notification.tenant_id,
            user_id=notification.user_id,
            alert_id=notification.alert_id,
            channel=notification.channel,
            status=notification.status,
            subject=notification.subject,
            body=notification.body,
            metadata=notification.metadata,
            sent_at=notification.sent_at,
            delivered_at=notification.delivered_at,
            created_at=notification.created_at,
        )

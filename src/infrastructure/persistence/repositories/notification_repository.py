"""Notification repository."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.notification.enums import NotificationChannel, NotificationStatus
from src.domain.notification.notification import Notification
from src.infrastructure.persistence.models.notification import NotificationModel


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, notification_id: UUID, tenant_id: UUID) -> Notification | None:
        result = await self._session.execute(
            select(NotificationModel).where(
                NotificationModel.id == notification_id,
                NotificationModel.tenant_id == tenant_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_user(
        self,
        user_id: UUID,
        tenant_id: UUID,
        status: NotificationStatus | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[Notification], int]:
        query = select(NotificationModel).where(
            NotificationModel.user_id == user_id,
            NotificationModel.tenant_id == tenant_id,
        )
        if status is not None:
            query = query.where(NotificationModel.status == status.value)

        count_result = await self._session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            query.order_by(NotificationModel.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        return [self._to_domain(m) for m in result.scalars().all()], total

    async def add(self, notification: Notification) -> Notification:
        model = NotificationModel(
            id=notification.id,
            tenant_id=notification.tenant_id,
            user_id=notification.user_id,
            alert_id=notification.alert_id,
            channel=notification.channel.value,
            status=notification.status.value,
            subject=notification.subject,
            body=notification.body,
            notification_metadata=notification.metadata,
            sent_at=notification.sent_at,
            delivered_at=notification.delivered_at,
            created_at=notification.created_at,
            updated_at=notification.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return notification

    async def update(self, notification: Notification) -> Notification:
        result = await self._session.execute(
            select(NotificationModel).where(
                NotificationModel.id == notification.id,
                NotificationModel.tenant_id == notification.tenant_id,
            )
        )
        model = result.scalar_one()
        model.status = notification.status.value
        model.sent_at = notification.sent_at
        model.delivered_at = notification.delivered_at
        model.updated_at = notification.updated_at
        await self._session.flush()
        return notification

    @staticmethod
    def _to_domain(model: NotificationModel) -> Notification:
        return Notification(
            id=model.id,
            tenant_id=model.tenant_id,
            user_id=model.user_id,
            alert_id=model.alert_id,
            channel=NotificationChannel(model.channel),
            status=NotificationStatus(model.status),
            subject=model.subject,
            body=model.body,
            metadata=model.notification_metadata,
            sent_at=model.sent_at,
            delivered_at=model.delivered_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

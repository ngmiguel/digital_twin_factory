"""Notification aggregate root."""

from datetime import datetime
from uuid import UUID

from src.domain.notification.enums import NotificationChannel, NotificationStatus
from src.domain.notification.events import NotificationDelivered, NotificationFailed, NotificationSent
from src.domain.shared.aggregate_root import AggregateRoot
from src.domain.shared.entity import Entity
from src.domain.shared.exceptions import ValidationError


class Notification(AggregateRoot):
    tenant_id: UUID
    user_id: UUID
    alert_id: UUID | None
    channel: NotificationChannel
    status: NotificationStatus
    subject: str
    body: str
    metadata: dict[str, object]
    sent_at: datetime | None = None
    delivered_at: datetime | None = None

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        user_id: UUID,
        channel: NotificationChannel,
        subject: str,
        body: str,
        alert_id: UUID | None = None,
        metadata: dict[str, object] | None = None,
    ) -> "Notification":
        if not subject.strip():
            raise ValidationError("Subject is required", field="subject")
        if not body.strip():
            raise ValidationError("Body is required", field="body")

        now = Entity.now()
        notification = cls(
            id=Entity.new_id(),
            tenant_id=tenant_id,
            user_id=user_id,
            alert_id=alert_id,
            channel=channel,
            status=NotificationStatus.PENDING,
            subject=subject.strip(),
            body=body.strip(),
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
        )
        return notification

    def mark_sent(self) -> None:
        self.status = NotificationStatus.SENT
        self.sent_at = Entity.now()
        self.updated_at = Entity.now()
        self.add_event(
            NotificationSent.create(
                tenant_id=self.tenant_id,
                aggregate_id=self.id,
                notification_id=self.id,
                user_id=self.user_id,
                channel=self.channel.value,
            )
        )

    def mark_delivered(self) -> None:
        self.status = NotificationStatus.DELIVERED
        self.delivered_at = Entity.now()
        self.updated_at = Entity.now()
        self.add_event(
            NotificationDelivered.create(
                tenant_id=self.tenant_id,
                aggregate_id=self.id,
                notification_id=self.id,
                user_id=self.user_id,
            )
        )

    def mark_failed(self, error: str) -> None:
        self.status = NotificationStatus.FAILED
        self.updated_at = Entity.now()
        self.add_event(
            NotificationFailed.create(
                tenant_id=self.tenant_id,
                aggregate_id=self.id,
                notification_id=self.id,
                user_id=self.user_id,
                error=error,
            )
        )

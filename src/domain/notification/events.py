"""Notification domain events."""

from uuid import UUID

from src.domain.shared.domain_event import DomainEvent


class NotificationSent(DomainEvent):
    notification_id: UUID
    user_id: UUID
    channel: str


class NotificationDelivered(DomainEvent):
    notification_id: UUID
    user_id: UUID


class NotificationFailed(DomainEvent):
    notification_id: UUID
    user_id: UUID
    error: str

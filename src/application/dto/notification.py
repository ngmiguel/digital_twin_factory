"""Notification DTOs."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from src.domain.notification.enums import NotificationChannel, NotificationStatus


class NotificationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID
    alert_id: UUID | None
    channel: NotificationChannel
    status: NotificationStatus
    subject: str
    body: str
    metadata: dict[str, Any]
    sent_at: datetime | None
    delivered_at: datetime | None
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    page: int
    size: int

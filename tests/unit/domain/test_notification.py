"""Unit tests for notification domain."""

from uuid import uuid4

import pytest

from src.domain.notification.enums import NotificationChannel, NotificationStatus
from src.domain.notification.notification import Notification
from src.domain.shared.exceptions import ValidationError


def test_notification_create_and_mark_sent() -> None:
    notification = Notification.create(
        tenant_id=uuid4(),
        user_id=uuid4(),
        channel=NotificationChannel.IN_APP,
        subject="Critical alert",
        body="Temperature exceeded threshold",
        alert_id=uuid4(),
    )
    assert notification.status == NotificationStatus.PENDING
    notification.mark_sent()
    assert notification.status == NotificationStatus.SENT
    assert notification.sent_at is not None
    assert len(notification.events) == 1


def test_notification_mark_delivered() -> None:
    notification = Notification.create(
        tenant_id=uuid4(),
        user_id=uuid4(),
        channel=NotificationChannel.IN_APP,
        subject="Alert",
        body="Machine failure detected",
    )
    notification.mark_sent()
    notification.mark_delivered()
    assert notification.status == NotificationStatus.DELIVERED
    assert notification.delivered_at is not None


def test_notification_requires_subject() -> None:
    with pytest.raises(ValidationError):
        Notification.create(
            tenant_id=uuid4(),
            user_id=uuid4(),
            channel=NotificationChannel.EMAIL,
            subject="   ",
            body="Valid body",
        )

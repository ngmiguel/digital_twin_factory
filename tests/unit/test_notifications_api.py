"""Unit tests for notifications API."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.application.dto.notification import NotificationListResponse, NotificationResponse
from src.domain.notification.enums import NotificationChannel, NotificationStatus
from src.presentation.dependencies.auth import CurrentUser, get_current_user
from src.presentation.dependencies.notification import get_notification_service
from src.presentation.main import create_app


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def current_user(tenant_id, user_id):
    return CurrentUser(
        user_id=user_id,
        tenant_id=tenant_id,
        roles=["maintenance_engineer"],
        permissions=["notification:read"],
    )


@pytest.fixture
def mock_notification_service(tenant_id, user_id):
    service = AsyncMock()
    now = datetime.now(UTC)
    notification = NotificationResponse(
        id=uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        alert_id=uuid4(),
        channel=NotificationChannel.IN_APP,
        status=NotificationStatus.DELIVERED,
        subject="[CRITICAL] Alert",
        body="Temperature critical",
        metadata={"type": "ALERT"},
        sent_at=now,
        delivered_at=now,
        created_at=now,
    )
    service.list_notifications.return_value = NotificationListResponse(
        items=[notification], total=1, page=1, size=20
    )
    service.mark_delivered.return_value = notification
    return service


@pytest.fixture
async def notifications_client(current_user, mock_notification_service):
    app = create_app()

    async def override_user():
        return current_user

    async def override_service():
        return mock_notification_service

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_notification_service] = override_service

    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_notifications(
    notifications_client: AsyncClient, mock_notification_service
) -> None:
    response = await notifications_client.get("/api/v1/notifications")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["channel"] == "IN_APP"
    mock_notification_service.list_notifications.assert_awaited_once()


@pytest.mark.asyncio
async def test_mark_notification_read(
    notifications_client: AsyncClient, mock_notification_service
) -> None:
    notification_id = uuid4()
    response = await notifications_client.patch(f"/api/v1/notifications/{notification_id}/read")
    assert response.status_code == 200
    mock_notification_service.mark_delivered.assert_awaited_once()

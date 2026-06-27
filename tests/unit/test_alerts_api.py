"""Unit tests for alerts API with mocked service."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.application.dto.monitoring import AlertListResponse, AlertResponse
from src.domain.monitoring.enums import AlertSeverity, AlertType
from src.presentation.dependencies.auth import CurrentUser, get_current_user
from src.presentation.dependencies.monitoring import get_alert_service
from src.presentation.main import create_app


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def current_user(tenant_id):
    return CurrentUser(
        user_id=uuid4(),
        tenant_id=tenant_id,
        roles=["tenant_admin"],
        permissions=["alert:read", "alert:write"],
    )


@pytest.fixture
def mock_alert_service(tenant_id):
    service = AsyncMock()
    alert_id = uuid4()
    machine_id = uuid4()
    now = datetime.now(UTC)
    alert_response = AlertResponse(
        id=alert_id,
        tenant_id=tenant_id,
        machine_id=machine_id,
        alert_type=AlertType.TEMPERATURE_HIGH,
        severity=AlertSeverity.WARNING,
        message="temperature warning",
        metadata={"value": 88.0},
        is_acknowledged=False,
        acknowledged_by=None,
        acknowledged_at=None,
        is_resolved=False,
        resolved_at=None,
        created_at=now,
        updated_at=now,
    )
    service.list_alerts.return_value = AlertListResponse(
        items=[alert_response], total=1, page=1, size=20
    )
    service.acknowledge_alert.return_value = alert_response
    service.resolve_alert.return_value = alert_response
    return service


@pytest.fixture
async def alerts_client(current_user, mock_alert_service):
    app = create_app()

    async def override_user():
        return current_user

    async def override_service():
        return mock_alert_service

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_alert_service] = override_service

    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_alerts(alerts_client: AsyncClient, mock_alert_service) -> None:
    response = await alerts_client.get("/api/v1/alerts?status=active")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["severity"] == "WARNING"
    mock_alert_service.list_alerts.assert_awaited_once()


@pytest.mark.asyncio
async def test_acknowledge_alert(alerts_client: AsyncClient, mock_alert_service) -> None:
    alert_id = uuid4()
    response = await alerts_client.patch(f"/api/v1/alerts/{alert_id}/acknowledge")
    assert response.status_code == 200
    mock_alert_service.acknowledge_alert.assert_awaited_once()


@pytest.mark.asyncio
async def test_resolve_alert(alerts_client: AsyncClient, mock_alert_service) -> None:
    alert_id = uuid4()
    response = await alerts_client.patch(
        f"/api/v1/alerts/{alert_id}/resolve",
        json={"resolution": "Cooling system repaired"},
    )
    assert response.status_code == 200
    mock_alert_service.resolve_alert.assert_awaited_once()

"""Unit tests for prediction and maintenance API."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.application.dto.prediction import (
    MaintenanceListResponse,
    MaintenanceResponse,
    PredictionListResponse,
    PredictionResponse,
)
from src.domain.prediction.enums import MaintenanceStatus, MaintenanceType, PredictionType
from src.presentation.dependencies.auth import CurrentUser, get_current_user
from src.presentation.dependencies.prediction import get_maintenance_service, get_prediction_service
from src.presentation.main import create_app


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def current_user(tenant_id):
    return CurrentUser(
        user_id=uuid4(),
        tenant_id=tenant_id,
        roles=["maintenance_engineer"],
        permissions=["prediction:read", "maintenance:read", "maintenance:write"],
    )


@pytest.fixture
def mock_prediction_service(tenant_id):
    service = AsyncMock()
    machine_id = uuid4()
    now = datetime.now(UTC)
    prediction = PredictionResponse(
        id=uuid4(),
        tenant_id=tenant_id,
        machine_id=machine_id,
        prediction_type=PredictionType.FAILURE_WITHIN_24H,
        confidence=0.87,
        features={"anomaly_score": 0.82},
        predicted_at=now,
        valid_until=now,
        created_at=now,
    )
    service.list_machine_predictions.return_value = PredictionListResponse(
        predictions=[prediction], total=1, page=1, size=20
    )
    return service


@pytest.fixture
def mock_maintenance_service(tenant_id):
    service = AsyncMock()
    now = datetime.now(UTC)
    maintenance = MaintenanceResponse(
        id=uuid4(),
        tenant_id=tenant_id,
        machine_id=uuid4(),
        prediction_id=None,
        assigned_to=None,
        maintenance_type=MaintenanceType.PREDICTIVE,
        status=MaintenanceStatus.SCHEDULED,
        description="Scheduled bearing replacement",
        scheduled_at=now,
        started_at=None,
        completed_at=None,
        created_at=now,
    )
    service.list_maintenance.return_value = MaintenanceListResponse(
        items=[maintenance], total=1, page=1, size=20
    )
    service.create_maintenance.return_value = maintenance
    service.start_maintenance.return_value = maintenance
    service.complete_maintenance.return_value = maintenance
    return service


@pytest.fixture
async def prediction_client(current_user, mock_prediction_service, mock_maintenance_service):
    app = create_app()

    async def override_user():
        return current_user

    async def override_prediction():
        return mock_prediction_service

    async def override_maintenance():
        return mock_maintenance_service

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_prediction_service] = override_prediction
    app.dependency_overrides[get_maintenance_service] = override_maintenance

    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_machine_predictions(
    prediction_client: AsyncClient, mock_prediction_service
) -> None:
    machine_id = uuid4()
    response = await prediction_client.get(f"/api/v1/machines/{machine_id}/predictions")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["predictions"][0]["confidence"] == 0.87
    mock_prediction_service.list_machine_predictions.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_maintenance(
    prediction_client: AsyncClient, mock_maintenance_service
) -> None:
    response = await prediction_client.get("/api/v1/maintenance?status=SCHEDULED")
    assert response.status_code == 200
    assert response.json()["total"] == 1
    mock_maintenance_service.list_maintenance.assert_awaited_once()


@pytest.mark.asyncio
async def test_complete_maintenance(
    prediction_client: AsyncClient, mock_maintenance_service
) -> None:
    maintenance_id = uuid4()
    response = await prediction_client.patch(f"/api/v1/maintenance/{maintenance_id}/complete")
    assert response.status_code == 200
    mock_maintenance_service.complete_maintenance.assert_awaited_once()

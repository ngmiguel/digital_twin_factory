"""Unit tests for factory API with mocked service."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.application.dto.factory import FactoryListResponse, FactoryResponse
from src.domain.factory.enums import FactoryStatus
from src.presentation.dependencies.auth import CurrentUser, get_current_user
from src.presentation.dependencies.factory import get_factory_service
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
        permissions=["factory:read", "factory:write", "factory:delete", "machine:read", "machine:write"],
    )


@pytest.fixture
def mock_factory_service(tenant_id):
    service = AsyncMock()
    factory_id = uuid4()
    now = datetime.now(UTC)
    factory_response = FactoryResponse(
        id=factory_id,
        name="Usine Nord",
        location="Lyon",
        status=FactoryStatus.ACTIVE,
        config={},
        machine_count=0,
        active_alerts=0,
        created_at=now,
        updated_at=now,
    )
    service.list_factories.return_value = FactoryListResponse(
        items=[factory_response], total=1, page=1, size=20
    )
    service.create_factory.return_value = factory_response
    service.get_factory.return_value = factory_response
    return service


@pytest.fixture
async def factory_client(current_user, mock_factory_service):
    app = create_app()

    async def override_user():
        return current_user

    async def override_service():
        return mock_factory_service

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_factory_service] = override_service

    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_factories(factory_client: AsyncClient, mock_factory_service) -> None:
    response = await factory_client.get("/api/v1/factories")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Usine Nord"
    mock_factory_service.list_factories.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_factory(factory_client: AsyncClient, mock_factory_service) -> None:
    response = await factory_client.post(
        "/api/v1/factories",
        json={"name": "Usine Nord", "location": "Lyon", "config": {}},
    )
    assert response.status_code == 201
    mock_factory_service.create_factory.assert_awaited_once()

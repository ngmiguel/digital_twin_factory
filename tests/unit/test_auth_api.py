"""Unit tests for auth API with mocked service."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.application.dto.auth import TokenResponse, UserResponse
from src.presentation.dependencies.auth import get_auth_service
from src.presentation.main import create_app


@pytest.fixture
def mock_auth_service():
    service = AsyncMock()
    user_id = uuid4()
    tenant_id = uuid4()
    service.register.return_value = TokenResponse(
        access_token="access-token",
        refresh_token="refresh-token",
        expires_in=900,
        user=UserResponse(
            id=user_id,
            email="admin@factory.com",
            tenant_id=tenant_id,
            first_name="Jean",
            last_name="Dupont",
            roles=["tenant_admin"],
        ),
    )
    service.login.return_value = service.register.return_value
    service.refresh.return_value = service.register.return_value
    service.logout.return_value = None
    return service


@pytest.fixture
async def auth_client(mock_auth_service):
    app = create_app()

    async def override_auth_service():
        return mock_auth_service

    app.dependency_overrides[get_auth_service] = override_auth_service
    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_register_endpoint(auth_client: AsyncClient, mock_auth_service) -> None:
    response = await auth_client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@factory.com",
            "password": "SecurePass123",
            "first_name": "Jean",
            "last_name": "Dupont",
            "organization_name": "Usine Dupont",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["access_token"] == "access-token"
    assert data["user"]["roles"] == ["tenant_admin"]
    mock_auth_service.register.assert_awaited_once()


@pytest.mark.asyncio
async def test_login_endpoint(auth_client: AsyncClient, mock_auth_service) -> None:
    response = await auth_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@factory.com", "password": "SecurePass123"},
    )
    assert response.status_code == 200
    mock_auth_service.login.assert_awaited_once()


@pytest.mark.asyncio
async def test_logout_endpoint(auth_client: AsyncClient, mock_auth_service) -> None:
    response = await auth_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": "refresh-token"},
    )
    assert response.status_code == 204
    mock_auth_service.logout.assert_awaited_once()

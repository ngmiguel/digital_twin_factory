"""Integration tests for authentication API."""

import pytest
from httpx import AsyncClient

from tests.helpers.auth import TEST_PASSWORD, auth_header, register_user


@pytest.mark.integration
@pytest.mark.asyncio
async def test_register_login_refresh_logout_flow(integration_client: AsyncClient) -> None:
    data = await register_user(integration_client)
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]
    email = data["user"]["email"]

    login_response = await integration_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": TEST_PASSWORD},
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert login_data["access_token"]

    refresh_response = await integration_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login_data["refresh_token"]},
    )
    assert refresh_response.status_code == 200
    refreshed = refresh_response.json()

    logout_response = await integration_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refreshed["refresh_token"]},
    )
    assert logout_response.status_code == 204


@pytest.mark.integration
@pytest.mark.asyncio
async def test_duplicate_register_returns_conflict(integration_client: AsyncClient) -> None:
    data = await register_user(integration_client)
    email = data["user"]["email"]

    duplicate = await integration_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": TEST_PASSWORD,
            "first_name": "Dup",
            "last_name": "User",
            "organization_name": "Another Org",
        },
    )
    assert duplicate.status_code == 409


@pytest.mark.integration
@pytest.mark.asyncio
async def test_protected_endpoint_requires_auth(integration_client: AsyncClient) -> None:
    response = await integration_client.get("/api/v1/factories")
    assert response.status_code == 401

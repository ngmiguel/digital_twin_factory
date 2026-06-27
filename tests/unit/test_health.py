"""Unit tests for health endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_liveness(client: AsyncClient) -> None:
    response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


@pytest.mark.asyncio
async def test_health_returns_version(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "services" in data
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_health_includes_correlation_id(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert "X-Correlation-ID" in response.headers


@pytest.mark.asyncio
async def test_openapi_docs_available(client: AsyncClient) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Digital Twin Factory"

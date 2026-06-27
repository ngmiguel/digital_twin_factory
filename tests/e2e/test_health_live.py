"""E2E health check against live API."""

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_live_health_endpoint(e2e_client: AsyncClient) -> None:
    response = await e2e_client.get("/health/live")
    assert response.status_code == 200
    assert response.json().get("status") == "alive"

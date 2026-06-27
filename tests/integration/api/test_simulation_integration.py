"""Integration tests for simulation tick with real database."""

from uuid import UUID

import pytest
from httpx import AsyncClient

from src.infrastructure.simulation.tick_runner import run_machine_tick
from tests.helpers.auth import auth_header, register_user


@pytest.mark.integration
@pytest.mark.asyncio
async def test_simulation_tick_persists_metrics(integration_client: AsyncClient) -> None:
    token_data = await register_user(integration_client)
    headers = auth_header(token_data["access_token"])

    factory = await integration_client.post(
        "/api/v1/factories",
        json={"name": "Sim Factory", "location": "Marseille", "config": {}},
        headers=headers,
    )
    factory_id = factory.json()["id"]

    line = await integration_client.post(
        f"/api/v1/factories/{factory_id}/lines",
        json={"name": "Sim Line", "capacity": 5},
        headers=headers,
    )
    line_id = line.json()["id"]

    machine = await integration_client.post(
        "/api/v1/machines",
        json={
            "production_line_id": line_id,
            "name": "Sim-Machine",
            "machine_type": "PRESS",
            "nominal_production_rate": 80.0,
        },
        headers=headers,
    )
    machine_id = machine.json()["id"]
    tenant_id = token_data["user"]["tenant_id"]

    await integration_client.post(f"/api/v1/machines/{machine_id}/start", headers=headers)

    result = await run_machine_tick(UUID(machine_id), UUID(tenant_id))
    assert result["status"] == "ok"
    assert "temperature" in result

"""E2E onboarding flow — register through machine start."""

import pytest
from httpx import AsyncClient

from tests.helpers.auth import auth_header, register_user


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_full_onboarding_flow(e2e_client: AsyncClient) -> None:
    token_data = await register_user(e2e_client)
    headers = auth_header(token_data["access_token"])

    factory_response = await e2e_client.post(
        "/api/v1/factories",
        json={"name": "E2E Factory", "location": "Toulouse", "config": {}},
        headers=headers,
    )
    assert factory_response.status_code == 201
    factory_id = factory_response.json()["id"]

    line_response = await e2e_client.post(
        f"/api/v1/factories/{factory_id}/lines",
        json={"name": "E2E Line", "capacity": 8},
        headers=headers,
    )
    assert line_response.status_code == 201
    line_id = line_response.json()["id"]

    machine_response = await e2e_client.post(
        "/api/v1/machines",
        json={
            "production_line_id": line_id,
            "name": "E2E-CNC",
            "machine_type": "CNC_MILL",
        },
        headers=headers,
    )
    assert machine_response.status_code == 201
    machine_id = machine_response.json()["id"]

    start_response = await e2e_client.post(
        f"/api/v1/machines/{machine_id}/start",
        headers=headers,
    )
    assert start_response.status_code == 200
    assert start_response.json()["status"] == "RUNNING"

    list_response = await e2e_client.get("/api/v1/machines", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["total"] >= 1

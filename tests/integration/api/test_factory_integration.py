"""Integration tests for factory and machine management."""

import pytest
from httpx import AsyncClient

from tests.helpers.auth import auth_header, register_user


@pytest.mark.integration
@pytest.mark.asyncio
async def test_factory_crud_flow(integration_client: AsyncClient) -> None:
    token_data = await register_user(integration_client)
    headers = auth_header(token_data["access_token"])

    create_response = await integration_client.post(
        "/api/v1/factories",
        json={"name": "Usine Integration", "location": "Paris", "config": {}},
        headers=headers,
    )
    assert create_response.status_code == 201
    factory = create_response.json()
    factory_id = factory["id"]
    assert factory["name"] == "Usine Integration"

    list_response = await integration_client.get("/api/v1/factories", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["total"] >= 1

    line_response = await integration_client.post(
        f"/api/v1/factories/{factory_id}/lines",
        json={"name": "Line A", "capacity": 10},
        headers=headers,
    )
    assert line_response.status_code == 201
    line_id = line_response.json()["id"]

    machine_response = await integration_client.post(
        "/api/v1/machines",
        json={
            "production_line_id": line_id,
            "name": "CNC-INT-001",
            "machine_type": "CNC_MILL",
            "nominal_production_rate": 100.0,
        },
        headers=headers,
    )
    assert machine_response.status_code == 201
    machine_id = machine_response.json()["id"]

    start_response = await integration_client.post(
        f"/api/v1/machines/{machine_id}/start",
        headers=headers,
    )
    assert start_response.status_code == 200
    assert start_response.json()["status"] == "RUNNING"

    get_response = await integration_client.get(f"/api/v1/factories/{factory_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["machine_count"] == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tenant_isolation(integration_client: AsyncClient) -> None:
    user_a = await register_user(integration_client, "tenant-a")
    user_b = await register_user(integration_client, "tenant-b")

    create_a = await integration_client.post(
        "/api/v1/factories",
        json={"name": "Factory A", "location": "Lyon", "config": {}},
        headers=auth_header(user_a["access_token"]),
    )
    factory_a_id = create_a.json()["id"]

    forbidden = await integration_client.get(
        f"/api/v1/factories/{factory_a_id}",
        headers=auth_header(user_b["access_token"]),
    )
    assert forbidden.status_code == 404

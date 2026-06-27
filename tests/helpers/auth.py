"""Shared test helpers."""

from uuid import uuid4

from httpx import AsyncClient

TEST_PASSWORD = "SecurePass123!"


async def register_user(client: AsyncClient, suffix: str | None = None) -> dict:
    """Register a tenant admin and return the token response payload."""
    unique = suffix or str(uuid4())
    payload = {
        "email": f"user-{unique}@test.example.com",
        "password": TEST_PASSWORD,
        "first_name": "Integration",
        "last_name": "Tester",
        "organization_name": f"Test Org {unique}",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def auth_header(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}

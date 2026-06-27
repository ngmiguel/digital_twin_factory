"""E2E test fixtures."""

import os

import httpx
import pytest

E2E_BASE_URL = os.environ.get("E2E_BASE_URL", "http://localhost:8000")


async def _api_reachable() -> bool:
    try:
        async with httpx.AsyncClient(base_url=E2E_BASE_URL, timeout=5.0) as client:
            response = await client.get("/health")
            return response.status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="session")
def e2e_stack():
    if not __import__("asyncio").run(_api_reachable()):
        pytest.skip(f"E2E API not reachable at {E2E_BASE_URL}")
    return E2E_BASE_URL


@pytest.fixture
async def e2e_client(e2e_stack):
    async with httpx.AsyncClient(base_url=e2e_stack, timeout=30.0) as client:
        yield client

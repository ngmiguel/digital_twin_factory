"""Integration test fixtures — real PostgreSQL and Redis."""

import os
import subprocess
import sys

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Integration env before app imports
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://dtf:dtf@localhost:5432/digital_twin_factory_test",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/14")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/13")
os.environ.setdefault("API_RELOAD", "false")


async def _services_available() -> bool:
    database_url = os.environ["DATABASE_URL"]
    redis_url = os.environ["REDIS_URL"]
    try:
        engine = create_async_engine(database_url)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()

        import redis.asyncio as aioredis

        client = aioredis.from_url(redis_url, decode_responses=True)
        await client.ping()
        await client.aclose()
        return True
    except Exception:
        return False


def _run_migrations() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )
    if result.returncode != 0:
        raise RuntimeError(f"Alembic migration failed: {result.stderr}")


@pytest.fixture(scope="session")
def integration_services():
    if not __import__("asyncio").run(_services_available()):
        pytest.skip("PostgreSQL and Redis required for integration tests")
    _run_migrations()
    return True


@pytest.fixture
async def integration_client(integration_services):
    from src.infrastructure.cache.redis_client import close_redis, init_redis
    from src.infrastructure.config.settings import get_settings
    from src.infrastructure.logging.setup import setup_logging
    from src.infrastructure.persistence.database import close_db, init_db
    from src.presentation.main import create_app

    get_settings.cache_clear()
    settings = get_settings()
    setup_logging(settings)
    init_db(settings)
    await init_redis(settings)

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    await close_redis()
    await close_db()

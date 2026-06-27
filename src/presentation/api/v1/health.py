"""Health check endpoints."""

import time
from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from src.infrastructure.cache.redis_client import _redis_client
from src.infrastructure.config.settings import get_settings
from src.infrastructure.persistence.database import _engine

router = APIRouter(tags=["Health"])

_start_time = time.time()


@router.get("/health")
async def health() -> dict[str, Any]:
    settings = get_settings()
    services: dict[str, Any] = {}

    # Database check
    if _engine is not None:
        try:
            async with _engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            services["database"] = {"status": "ok"}
        except Exception as e:
            services["database"] = {"status": "error", "message": str(e)}
    else:
        services["database"] = {"status": "not_initialized"}

    # Redis check
    if _redis_client is not None:
        try:
            pong = await _redis_client.ping()
            services["redis"] = {"status": "ok" if pong else "error"}
        except Exception as e:
            services["redis"] = {"status": "error", "message": str(e)}
    else:
        services["redis"] = {"status": "not_initialized"}

    all_ok = all(s.get("status") == "ok" for s in services.values())
    overall = "healthy" if all_ok else "degraded"

    return {
        "status": overall,
        "version": settings.app_version,
        "environment": settings.environment,
        "uptime_seconds": int(time.time() - _start_time),
        "services": services,
    }


@router.get("/health/live")
async def liveness() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness() -> dict[str, str]:
    if _engine is None or _redis_client is None:
        return {"status": "not_ready"}
    try:
        async with _engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await _redis_client.ping()
        return {"status": "ready"}
    except Exception:
        return {"status": "not_ready"}

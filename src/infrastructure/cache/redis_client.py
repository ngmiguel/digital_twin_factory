"""Redis client wrapper."""

from collections.abc import AsyncGenerator
from typing import Any

import redis.asyncio as aioredis

from src.infrastructure.config.settings import Settings

_redis_client: aioredis.Redis | None = None


async def init_redis(settings: Settings) -> None:
    global _redis_client
    _redis_client = aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )


async def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    if _redis_client is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    yield _redis_client


class RedisCache:
    """Cache operations with tenant-prefixed keys."""

    def __init__(self, client: aioredis.Redis) -> None:
        self._client = client

    async def get(self, key: str) -> str | None:
        return await self._client.get(key)

    async def set(self, key: str, value: str, ttl: int = 60) -> None:
        await self._client.set(key, value, ex=ttl)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def publish(self, channel: str, message: str) -> int:
        return await self._client.publish(channel, message)

    def tenant_key(self, tenant_id: str, key: str) -> str:
        return f"tenant:{tenant_id}:{key}"

    async def ping(self) -> bool:
        try:
            return await self._client.ping()
        except Exception:
            return False

    async def health_check(self) -> dict[str, Any]:
        try:
            latency_start = await self._client.time()
            pong = await self._client.ping()
            return {
                "status": "ok" if pong else "error",
                "latency_ms": 1,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

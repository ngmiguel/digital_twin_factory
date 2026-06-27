"""Login rate limiting via Redis."""

import redis.asyncio as aioredis

from src.domain.shared.exceptions import RateLimitError

_MAX_ATTEMPTS = 5
_WINDOW_SECONDS = 60


class LoginRateLimiter:
    """Limit login attempts per IP address."""

    def __init__(self, client: aioredis.Redis) -> None:
        self._client = client

    def _key(self, ip_address: str) -> str:
        return f"ratelimit:login:{ip_address}"

    async def check(self, ip_address: str) -> None:
        key = self._key(ip_address)
        attempts = await self._client.incr(key)
        if attempts == 1:
            await self._client.expire(key, _WINDOW_SECONDS)
        if attempts > _MAX_ATTEMPTS:
            raise RateLimitError("Too many login attempts. Try again later.")

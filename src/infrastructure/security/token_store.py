"""Redis-backed refresh token storage."""

from uuid import UUID

import redis.asyncio as aioredis

from src.domain.shared.exceptions import AuthenticationError


class RefreshTokenStore:
    """Store and rotate refresh tokens in Redis."""

    def __init__(self, client: aioredis.Redis) -> None:
        self._client = client

    def _key(self, jti: str) -> str:
        return f"refresh:{jti}"

    def _user_sessions_key(self, user_id: UUID) -> str:
        return f"user:{user_id}:sessions"

    async def store(self, jti: str, user_id: UUID, ttl_seconds: int) -> None:
        await self._client.set(self._key(jti), str(user_id), ex=ttl_seconds)
        await self._client.sadd(self._user_sessions_key(user_id), jti)
        await self._client.expire(self._user_sessions_key(user_id), ttl_seconds)

    async def validate(self, jti: str, user_id: UUID) -> None:
        stored_user_id = await self._client.get(self._key(jti))
        if stored_user_id is None or stored_user_id != str(user_id):
            raise AuthenticationError("Invalid refresh token")

    async def revoke(self, jti: str, user_id: UUID) -> None:
        await self._client.delete(self._key(jti))
        await self._client.srem(self._user_sessions_key(user_id), jti)

    async def revoke_all(self, user_id: UUID) -> None:
        sessions = await self._client.smembers(self._user_sessions_key(user_id))
        if sessions:
            keys = [self._key(jti) for jti in sessions]
            await self._client.delete(*keys)
        await self._client.delete(self._user_sessions_key(user_id))

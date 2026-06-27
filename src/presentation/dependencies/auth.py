"""FastAPI authentication dependencies."""

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.shared.exceptions import PermissionDeniedError
from src.infrastructure.cache.redis_client import _redis_client
from src.infrastructure.config.settings import Settings, get_settings
from src.infrastructure.persistence.database import get_session
from src.infrastructure.persistence.repositories.user_repository import UserRepository
from src.infrastructure.persistence.unit_of_work import SQLAlchemyUnitOfWork
from src.infrastructure.security.jwt_service import JWTService, TokenPayload
from src.infrastructure.security.permissions import has_permission
from src.infrastructure.security.rate_limiter import LoginRateLimiter
from src.infrastructure.security.token_store import RefreshTokenStore
from src.application.handlers.auth.auth_service import AuthService

security = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    user_id: UUID
    tenant_id: UUID
    roles: list[str]
    permissions: list[str]


async def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    if _redis_client is None:
        raise RuntimeError("Redis not initialized")

    uow = SQLAlchemyUnitOfWork(session)
    return AuthService(
        uow=uow,
        tenant_repo=TenantRepository(session),
        user_repo=UserRepository(session),
        jwt_service=JWTService(settings),
        token_store=RefreshTokenStore(_redis_client),
        rate_limiter=LoginRateLimiter(_redis_client),
    )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    jwt_service = JWTService(settings)
    try:
        payload = jwt_service.decode_token(credentials.credentials, expected_type="access")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    if payload.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return CurrentUser(
        user_id=payload.user_id,
        tenant_id=payload.tenant_id,
        roles=payload.roles,
        permissions=payload.permissions,
    )


def require_permission(permission: str):
    """Dependency factory for RBAC permission checks."""

    async def checker(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        if not has_permission(user.permissions, permission):
            raise PermissionDeniedError(permission)
        return user

    return checker


def get_token_payload(token: str, settings: Settings) -> TokenPayload:
    return JWTService(settings).decode_token(token, expected_type="access")

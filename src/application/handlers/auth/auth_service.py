"""Authentication use cases."""

from uuid import UUID

import structlog

from src.application.dto.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from src.domain.identity.events import UserLoggedIn
from src.domain.identity.roles import SystemRole
from src.domain.identity.tenant import Tenant
from src.domain.identity.user import User
from src.domain.identity.value_objects import Email
from src.domain.shared.exceptions import AuthenticationError, ConflictError
from src.infrastructure.persistence.repositories.tenant_repository import TenantRepository
from src.infrastructure.persistence.repositories.user_repository import UserRepository
from src.infrastructure.persistence.unit_of_work import SQLAlchemyUnitOfWork
from src.infrastructure.security.jwt_service import JWTService
from src.infrastructure.security.password_service import PasswordService
from src.infrastructure.security.rate_limiter import LoginRateLimiter
from src.infrastructure.security.token_store import RefreshTokenStore

logger = structlog.get_logger()


class AuthService:
    """Register, login, refresh and logout use cases."""

    def __init__(
        self,
        uow: SQLAlchemyUnitOfWork,
        tenant_repo: TenantRepository,
        user_repo: UserRepository,
        jwt_service: JWTService,
        token_store: RefreshTokenStore,
        rate_limiter: LoginRateLimiter | None = None,
    ) -> None:
        self._uow = uow
        self._tenant_repo = tenant_repo
        self._user_repo = user_repo
        self._jwt_service = jwt_service
        self._token_store = token_store
        self._rate_limiter = rate_limiter

    async def register(self, request: RegisterRequest) -> TokenResponse:
        email = Email.create(str(request.email))

        if await self._user_repo.email_exists(email.value):
            raise ConflictError("Email already registered")

        tenant = Tenant.create(name=request.organization_name)
        existing = await self._tenant_repo.get_by_slug(tenant.slug)
        if existing:
            raise ConflictError("Organization slug already taken")

        password_hash = PasswordService.hash(request.password)
        user = User.register(
            tenant_id=tenant.id,
            email=email,
            password_hash=password_hash,
            first_name=request.first_name,
            last_name=request.last_name,
        )

        await self._tenant_repo.add(tenant)
        await self._user_repo.add(user)
        await self._user_repo.assign_role(user.id, SystemRole.TENANT_ADMIN.value)

        roles, permissions = await self._user_repo.get_roles_and_permissions(user.id)
        token_pair, jti, refresh_ttl = self._jwt_service.create_token_pair(
            user.id, user.tenant_id, roles, permissions
        )
        await self._token_store.store(jti, user.id, refresh_ttl)
        await self._uow.commit()

        logger.info("user.registered", user_id=str(user.id), tenant_id=str(tenant.id))
        return self._build_token_response(user, roles, token_pair)

    async def login(self, request: LoginRequest, ip_address: str | None = None) -> TokenResponse:
        if self._rate_limiter and ip_address:
            await self._rate_limiter.check(ip_address)

        user = await self._user_repo.get_by_email(str(request.email))
        if user is None or not PasswordService.verify(request.password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        user.record_login(ip_address)
        await self._user_repo.update(user)

        roles, permissions = await self._user_repo.get_roles_and_permissions(user.id)
        token_pair, jti, refresh_ttl = self._jwt_service.create_token_pair(
            user.id, user.tenant_id, roles, permissions
        )
        await self._token_store.store(jti, user.id, refresh_ttl)
        await self._uow.commit()

        logger.info(
            "user.logged_in",
            user_id=str(user.id),
            ip_address=ip_address,
            event=UserLoggedIn.__name__,
        )
        return self._build_token_response(user, roles, token_pair)

    async def refresh(self, request: RefreshRequest) -> TokenResponse:
        payload = self._jwt_service.decode_token(request.refresh_token, expected_type="refresh")
        if payload.jti is None:
            raise AuthenticationError("Invalid refresh token")

        await self._token_store.validate(payload.jti, payload.user_id)

        user = await self._user_repo.get_by_id(payload.user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        await self._token_store.revoke(payload.jti, payload.user_id)

        roles, permissions = await self._user_repo.get_roles_and_permissions(user.id)
        token_pair, new_jti, refresh_ttl = self._jwt_service.create_token_pair(
            user.id, user.tenant_id, roles, permissions
        )
        await self._token_store.store(new_jti, user.id, refresh_ttl)
        await self._uow.commit()

        return self._build_token_response(user, roles, token_pair)

    async def logout(self, request: LogoutRequest) -> None:
        payload = self._jwt_service.decode_token(request.refresh_token, expected_type="refresh")
        if payload.jti is None:
            raise AuthenticationError("Invalid refresh token")

        await self._token_store.revoke(payload.jti, payload.user_id)
        await self._uow.commit()
        logger.info("user.logged_out", user_id=str(payload.user_id))

    @staticmethod
    def _build_token_response(user: User, roles: list[str], token_pair) -> TokenResponse:
        return TokenResponse(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            expires_in=token_pair.expires_in,
            user=UserResponse(
                id=user.id,
                email=user.email,
                tenant_id=user.tenant_id,
                first_name=user.first_name,
                last_name=user.last_name,
                roles=roles,
            ),
        )

"""JWT token creation and validation."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from jose import JWTError, jwt

from src.domain.shared.exceptions import AuthenticationError
from src.infrastructure.config.settings import Settings


@dataclass(frozen=True)
class TokenPayload:
    user_id: UUID
    tenant_id: UUID | None
    roles: list[str]
    permissions: list[str]
    token_type: str
    jti: str | None = None


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in: int


class JWTService:
    """Create and decode JWT access and refresh tokens."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def create_access_token(
        self,
        user_id: UUID,
        tenant_id: UUID,
        roles: list[str],
        permissions: list[str],
    ) -> tuple[str, int]:
        expires_delta = timedelta(minutes=self._settings.jwt_access_token_expire_minutes)
        expires_at = datetime.now(UTC) + expires_delta
        payload = {
            "sub": str(user_id),
            "tenant_id": str(tenant_id),
            "roles": roles,
            "permissions": permissions,
            "type": "access",
            "exp": expires_at,
        }
        token = jwt.encode(
            payload,
            self._settings.jwt_secret_key,
            algorithm=self._settings.jwt_algorithm,
        )
        return token, int(expires_delta.total_seconds())

    def create_refresh_token(self, user_id: UUID) -> tuple[str, str, int]:
        jti = str(uuid4())
        expires_delta = timedelta(days=self._settings.jwt_refresh_token_expire_days)
        expires_at = datetime.now(UTC) + expires_delta
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "jti": jti,
            "exp": expires_at,
        }
        token = jwt.encode(
            payload,
            self._settings.jwt_secret_key,
            algorithm=self._settings.jwt_algorithm,
        )
        return token, jti, int(expires_delta.total_seconds())

    def create_token_pair(
        self,
        user_id: UUID,
        tenant_id: UUID,
        roles: list[str],
        permissions: list[str],
    ) -> tuple[TokenPair, str, int]:
        access_token, expires_in = self.create_access_token(
            user_id, tenant_id, roles, permissions
        )
        refresh_token, jti, refresh_ttl = self.create_refresh_token(user_id)
        return (
            TokenPair(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=expires_in,
            ),
            jti,
            refresh_ttl,
        )

    def decode_token(self, token: str, expected_type: str) -> TokenPayload:
        try:
            payload = jwt.decode(
                token,
                self._settings.jwt_secret_key,
                algorithms=[self._settings.jwt_algorithm],
            )
        except JWTError as exc:
            raise AuthenticationError("Invalid or expired token") from exc

        if payload.get("type") != expected_type:
            raise AuthenticationError("Invalid token type")

        if expected_type == "access":
            return TokenPayload(
                user_id=UUID(payload["sub"]),
                tenant_id=UUID(payload["tenant_id"]),
                roles=list(payload.get("roles", [])),
                permissions=list(payload.get("permissions", [])),
                token_type="access",
            )

        return TokenPayload(
            user_id=UUID(payload["sub"]),
            tenant_id=None,
            roles=[],
            permissions=[],
            token_type="refresh",
            jti=payload.get("jti"),
        )

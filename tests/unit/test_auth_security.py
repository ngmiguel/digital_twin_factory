"""Unit tests for security services."""

from uuid import uuid4

import pytest

from src.domain.shared.exceptions import ValidationError
from src.infrastructure.config.settings import Settings
from src.infrastructure.security.jwt_service import JWTService
from src.infrastructure.security.password_service import PasswordService
from src.infrastructure.security.permissions import has_permission


@pytest.fixture
def settings() -> Settings:
    return Settings(
        jwt_secret_key="test-secret-key-for-unit-tests",
        jwt_access_token_expire_minutes=15,
        jwt_refresh_token_expire_days=7,
    )


def test_password_hash_and_verify() -> None:
    hashed = PasswordService.hash("SecurePass123")
    assert PasswordService.verify("SecurePass123", hashed)
    assert not PasswordService.verify("WrongPass123", hashed)


def test_password_strength_validation() -> None:
    with pytest.raises(ValidationError):
        PasswordService.hash("weak")


def test_jwt_access_and_refresh_tokens(settings: Settings) -> None:
    jwt_service = JWTService(settings)
    user_id = uuid4()
    tenant_id = uuid4()
    roles = ["tenant_admin"]
    permissions = ["factory:read", "factory:write"]

    token_pair, jti, refresh_ttl = jwt_service.create_token_pair(
        user_id, tenant_id, roles, permissions
    )
    assert token_pair.access_token
    assert token_pair.refresh_token
    assert jti
    assert refresh_ttl > 0

    access_payload = jwt_service.decode_token(token_pair.access_token, "access")
    assert access_payload.user_id == user_id
    assert access_payload.tenant_id == tenant_id
    assert "factory:read" in access_payload.permissions

    refresh_payload = jwt_service.decode_token(token_pair.refresh_token, "refresh")
    assert refresh_payload.user_id == user_id
    assert refresh_payload.jti == jti


@pytest.mark.parametrize(
    ("permissions", "required", "expected"),
    [
        (["factory:read"], "factory:read", True),
        (["factory:*"], "factory:write", True),
        (["*"], "machine:delete", True),
        (["factory:read"], "factory:write", False),
        (["machine:read"], "factory:read", False),
    ],
)
def test_has_permission(permissions: list[str], required: str, expected: bool) -> None:
    assert has_permission(permissions, required) is expected

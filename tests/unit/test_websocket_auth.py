"""Unit tests for WebSocket authentication."""

from uuid import uuid4

import pytest

from src.domain.shared.exceptions import AuthenticationError, PermissionDeniedError
from src.infrastructure.config.settings import Settings
from src.infrastructure.security.jwt_service import JWTService
from src.presentation.websocket.auth import authenticate_websocket, parse_machine_filter


@pytest.fixture
def jwt_token() -> str:
    settings = Settings(jwt_secret_key="test-secret-key")
    service = JWTService(settings)
    user_id = uuid4()
    tenant_id = uuid4()
    token, _ = service.create_access_token(
        user_id, tenant_id, ["operator"], ["factory:read", "machine:read"]
    )
    return token


def test_authenticate_websocket_valid(jwt_token: str) -> None:
    from src.infrastructure.config.settings import get_settings

    get_settings.cache_clear()
    user = authenticate_websocket(jwt_token, "factory:read")
    assert "factory:read" in user.permissions


def test_authenticate_websocket_missing_token() -> None:
    with pytest.raises(AuthenticationError):
        authenticate_websocket("", "factory:read")


def test_authenticate_websocket_forbidden(jwt_token: str) -> None:
    from src.infrastructure.config.settings import get_settings

    get_settings.cache_clear()
    with pytest.raises(PermissionDeniedError):
        authenticate_websocket(jwt_token, "factory:write")


def test_parse_machine_filter() -> None:
    machine_id = uuid4()
    message = f'{{"machine_id": "{machine_id}", "type": "metric"}}'
    assert parse_machine_filter(message, machine_id) is True
    assert parse_machine_filter(message, uuid4()) is False

"""WebSocket JWT authentication."""

from uuid import UUID

from src.domain.shared.exceptions import AuthenticationError, PermissionDeniedError
from src.infrastructure.config.settings import get_settings
from src.infrastructure.security.jwt_service import JWTService
from src.infrastructure.security.permissions import has_permission
from src.presentation.dependencies.auth import CurrentUser


def authenticate_websocket(token: str, required_permission: str) -> CurrentUser:
    if not token:
        raise AuthenticationError("Missing authentication token")

    settings = get_settings()
    jwt_service = JWTService(settings)
    payload = jwt_service.decode_token(token, expected_type="access")

    if payload.tenant_id is None:
        raise AuthenticationError("Invalid token payload")

    if not has_permission(payload.permissions, required_permission):
        raise PermissionDeniedError(required_permission)

    return CurrentUser(
        user_id=payload.user_id,
        tenant_id=payload.tenant_id,
        roles=payload.roles,
        permissions=payload.permissions,
    )


def parse_machine_filter(message: str, machine_id: UUID) -> bool:
    """Return True if message belongs to the given machine."""
    import json

    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        return False
    return data.get("machine_id") == str(machine_id)

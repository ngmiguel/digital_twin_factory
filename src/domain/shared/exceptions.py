"""Domain exceptions — mapped to HTTP responses in presentation layer."""

from uuid import UUID


class DomainException(Exception):
    """Base domain exception."""

    def __init__(self, message: str, code: str = "DOMAIN_ERROR") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class EntityNotFoundError(DomainException):
    def __init__(self, entity_type: str, entity_id: UUID) -> None:
        super().__init__(
            message=f"{entity_type} with id '{entity_id}' not found",
            code="NOT_FOUND",
        )
        self.entity_type = entity_type
        self.entity_id = entity_id


class ValidationError(DomainException):
    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message=message, code="VALIDATION_ERROR")
        self.field = field


class PermissionDeniedError(DomainException):
    def __init__(self, required_permission: str) -> None:
        super().__init__(
            message=f"Permission denied: {required_permission} required",
            code="FORBIDDEN",
        )
        self.required_permission = required_permission


class TenantIsolationError(DomainException):
    def __init__(self, tenant_id: UUID) -> None:
        super().__init__(
            message="Access denied: resource belongs to another tenant",
            code="FORBIDDEN",
        )
        self.tenant_id = tenant_id


class AuthenticationError(DomainException):
    def __init__(self, reason: str = "Invalid credentials") -> None:
        super().__init__(message=reason, code="UNAUTHORIZED")
        self.reason = reason


class ConflictError(DomainException):
    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="CONFLICT")


class RateLimitError(DomainException):
    def __init__(self, message: str = "Rate limit exceeded") -> None:
        super().__init__(message=message, code="RATE_LIMITED")


class SimulationError(DomainException):
    def __init__(self, machine_id: UUID, reason: str) -> None:
        super().__init__(
            message=f"Simulation error for machine {machine_id}: {reason}",
            code="SIMULATION_ERROR",
        )
        self.machine_id = machine_id

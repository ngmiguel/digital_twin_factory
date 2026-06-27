"""Shared domain primitives."""

from src.domain.shared.aggregate_root import AggregateRoot
from src.domain.shared.domain_event import DomainEvent
from src.domain.shared.entity import Entity
from src.domain.shared.exceptions import (
    AuthenticationError,
    ConflictError,
    DomainException,
    EntityNotFoundError,
    PermissionDeniedError,
    RateLimitError,
    SimulationError,
    TenantIsolationError,
    ValidationError,
)
from src.domain.shared.value_object import ValueObject

__all__ = [
    "AggregateRoot",
    "DomainEvent",
    "Entity",
    "ValueObject",
    "DomainException",
    "EntityNotFoundError",
    "ValidationError",
    "PermissionDeniedError",
    "TenantIsolationError",
    "AuthenticationError",
    "ConflictError",
    "RateLimitError",
    "SimulationError",
]

"""Identity domain events."""

from uuid import UUID

from src.domain.shared.domain_event import DomainEvent


class TenantCreated(DomainEvent):
    name: str
    slug: str


class UserRegistered(DomainEvent):
    user_id: UUID
    email: str


class UserLoggedIn(DomainEvent):
    user_id: UUID
    ip_address: str | None = None

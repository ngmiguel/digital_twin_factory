"""User aggregate root."""

from datetime import datetime
from uuid import UUID

from src.domain.identity.events import UserRegistered
from src.domain.identity.value_objects import Email
from src.domain.shared.aggregate_root import AggregateRoot
from src.domain.shared.entity import Entity
from src.domain.shared.exceptions import AuthenticationError


class User(AggregateRoot):
    tenant_id: UUID
    email: str
    password_hash: str
    first_name: str
    last_name: str
    is_active: bool
    last_login: datetime | None = None

    @classmethod
    def register(
        cls,
        tenant_id: UUID,
        email: Email,
        password_hash: str,
        first_name: str,
        last_name: str,
    ) -> "User":
        now = Entity.now()
        user = cls(
            id=Entity.new_id(),
            tenant_id=tenant_id,
            email=email.value,
            password_hash=password_hash,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        user.add_event(
            UserRegistered.create(
                tenant_id=tenant_id,
                aggregate_id=user.id,
                user_id=user.id,
                email=user.email,
            )
        )
        return user

    def record_login(self, ip_address: str | None = None) -> None:
        if not self.is_active:
            raise AuthenticationError("Account is deactivated")
        self.last_login = Entity.now()
        self.updated_at = Entity.now()

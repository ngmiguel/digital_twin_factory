"""Factory aggregate root."""

from uuid import UUID

from src.domain.factory.enums import FactoryStatus
from src.domain.factory.events import FactoryCreated, FactoryDeleted, FactoryUpdated
from src.domain.shared.aggregate_root import AggregateRoot
from src.domain.shared.entity import Entity
from src.domain.shared.exceptions import ValidationError


class Factory(AggregateRoot):
    tenant_id: UUID
    name: str
    location: str | None
    status: FactoryStatus
    config: dict[str, object]

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        name: str,
        location: str | None = None,
        config: dict[str, object] | None = None,
    ) -> "Factory":
        if not name.strip():
            raise ValidationError("Factory name is required", field="name")

        now = Entity.now()
        factory = cls(
            id=Entity.new_id(),
            tenant_id=tenant_id,
            name=name.strip(),
            location=location.strip() if location else None,
            status=FactoryStatus.ACTIVE,
            config=config or {},
            created_at=now,
            updated_at=now,
        )
        factory.add_event(
            FactoryCreated.create(
                tenant_id=tenant_id,
                aggregate_id=factory.id,
                name=factory.name,
                location=factory.location,
            )
        )
        return factory

    def update(
        self,
        name: str | None = None,
        location: str | None = None,
        status: FactoryStatus | None = None,
        config: dict[str, object] | None = None,
    ) -> None:
        if name is not None:
            if not name.strip():
                raise ValidationError("Factory name is required", field="name")
            self.name = name.strip()
        if location is not None:
            self.location = location.strip() if location else None
        if status is not None:
            self.status = status
        if config is not None:
            self.config = config
        self.updated_at = Entity.now()
        self.add_event(
            FactoryUpdated.create(
                tenant_id=self.tenant_id,
                aggregate_id=self.id,
                factory_id=self.id,
            )
        )

    def mark_deleted(self) -> None:
        self.add_event(
            FactoryDeleted.create(
                tenant_id=self.tenant_id,
                aggregate_id=self.id,
                factory_id=self.id,
            )
        )

"""Production line entity."""

from uuid import UUID

from src.domain.factory.enums import ProductionLineStatus
from src.domain.factory.events import ProductionLineAdded
from src.domain.shared.aggregate_root import AggregateRoot
from src.domain.shared.entity import Entity
from src.domain.shared.exceptions import ValidationError


class ProductionLine(AggregateRoot):
    factory_id: UUID
    tenant_id: UUID
    name: str
    capacity: int
    status: ProductionLineStatus

    @classmethod
    def create(
        cls,
        factory_id: UUID,
        tenant_id: UUID,
        name: str,
        capacity: int,
    ) -> "ProductionLine":
        if not name.strip():
            raise ValidationError("Production line name is required", field="name")
        if capacity <= 0:
            raise ValidationError("Capacity must be positive", field="capacity")

        now = Entity.now()
        line = cls(
            id=Entity.new_id(),
            factory_id=factory_id,
            tenant_id=tenant_id,
            name=name.strip(),
            capacity=capacity,
            status=ProductionLineStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        line.add_event(
            ProductionLineAdded.create(
                tenant_id=tenant_id,
                aggregate_id=line.id,
                factory_id=factory_id,
                line_id=line.id,
                name=line.name,
            )
        )
        return line

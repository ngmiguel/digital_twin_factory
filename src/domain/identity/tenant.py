"""Tenant aggregate root."""

from src.domain.identity.events import TenantCreated
from src.domain.identity.value_objects import TenantSlug
from src.domain.shared.aggregate_root import AggregateRoot
from src.domain.shared.entity import Entity


class Tenant(AggregateRoot):
    name: str
    slug: str
    settings: dict[str, object]
    is_active: bool

    @classmethod
    def create(cls, name: str, slug: TenantSlug | None = None) -> "Tenant":
        resolved_slug = slug or TenantSlug.from_name(name)
        now = Entity.now()
        tenant = cls(
            id=Entity.new_id(),
            name=name.strip(),
            slug=resolved_slug.value,
            settings={},
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        tenant.add_event(
            TenantCreated.create(
                tenant_id=tenant.id,
                aggregate_id=tenant.id,
                name=tenant.name,
                slug=tenant.slug,
            )
        )
        return tenant

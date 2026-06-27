"""Tenant repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.identity.tenant import Tenant
from src.infrastructure.persistence.models.identity import TenantModel


class TenantRepository:
    """Persistence adapter for Tenant aggregate."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_slug(self, slug: str) -> Tenant | None:
        result = await self._session.execute(
            select(TenantModel).where(TenantModel.slug == slug)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def add(self, tenant: Tenant) -> Tenant:
        model = TenantModel(
            id=tenant.id,
            name=tenant.name,
            slug=tenant.slug,
            settings=tenant.settings,
            is_active=tenant.is_active,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return tenant

    @staticmethod
    def _to_domain(model: TenantModel) -> Tenant:
        return Tenant(
            id=model.id,
            name=model.name,
            slug=model.slug,
            settings=model.settings,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

"""Production line repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.factory.enums import ProductionLineStatus
from src.domain.factory.production_line import ProductionLine
from src.infrastructure.persistence.models.factory import ProductionLineModel


class ProductionLineRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, line_id: UUID, tenant_id: UUID) -> ProductionLine | None:
        result = await self._session.execute(
            select(ProductionLineModel).where(
                ProductionLineModel.id == line_id,
                ProductionLineModel.tenant_id == tenant_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_factory(self, factory_id: UUID, tenant_id: UUID) -> list[ProductionLine]:
        result = await self._session.execute(
            select(ProductionLineModel)
            .where(
                ProductionLineModel.factory_id == factory_id,
                ProductionLineModel.tenant_id == tenant_id,
            )
            .order_by(ProductionLineModel.created_at.desc())
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def add(self, line: ProductionLine) -> ProductionLine:
        model = ProductionLineModel(
            id=line.id,
            factory_id=line.factory_id,
            tenant_id=line.tenant_id,
            name=line.name,
            capacity=line.capacity,
            status=line.status.value,
            created_at=line.created_at,
            updated_at=line.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return line

    @staticmethod
    def _to_domain(model: ProductionLineModel) -> ProductionLine:
        return ProductionLine(
            id=model.id,
            factory_id=model.factory_id,
            tenant_id=model.tenant_id,
            name=model.name,
            capacity=model.capacity,
            status=ProductionLineStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

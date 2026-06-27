"""Factory repository."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.factory.enums import FactoryStatus
from src.domain.factory.factory import Factory
from src.infrastructure.persistence.repositories.alert_repository import AlertRepository
from src.infrastructure.persistence.models.factory import FactoryModel, MachineModel, ProductionLineModel


class FactoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._alert_repo = AlertRepository(session)

    async def get_by_id(self, factory_id: UUID, tenant_id: UUID) -> Factory | None:
        result = await self._session.execute(
            select(FactoryModel).where(
                FactoryModel.id == factory_id,
                FactoryModel.tenant_id == tenant_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        status: FactoryStatus | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[tuple[Factory, int, int]], int]:
        base_query = select(FactoryModel).where(FactoryModel.tenant_id == tenant_id)
        if status is not None:
            base_query = base_query.where(FactoryModel.status == status.value)

        count_result = await self._session.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            base_query.order_by(FactoryModel.created_at.desc()).offset((page - 1) * size).limit(size)
        )
        factories = result.scalars().all()

        items: list[tuple[Factory, int, int]] = []
        for model in factories:
            machine_count = await self.count_machines(model.id, tenant_id)
            active_alerts = await self._alert_repo.count_active_by_factory(model.id, tenant_id)
            items.append((self._to_domain(model), machine_count, active_alerts))

        return items, total

    async def add(self, factory: Factory) -> Factory:
        model = FactoryModel(
            id=factory.id,
            tenant_id=factory.tenant_id,
            name=factory.name,
            location=factory.location,
            status=factory.status.value,
            config=factory.config,
            created_at=factory.created_at,
            updated_at=factory.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return factory

    async def update(self, factory: Factory) -> Factory:
        result = await self._session.execute(
            select(FactoryModel).where(
                FactoryModel.id == factory.id,
                FactoryModel.tenant_id == factory.tenant_id,
            )
        )
        model = result.scalar_one()
        model.name = factory.name
        model.location = factory.location
        model.status = factory.status.value
        model.config = factory.config
        model.updated_at = factory.updated_at
        await self._session.flush()
        return factory

    async def delete(self, factory_id: UUID, tenant_id: UUID) -> None:
        result = await self._session.execute(
            select(FactoryModel).where(
                FactoryModel.id == factory_id,
                FactoryModel.tenant_id == tenant_id,
            )
        )
        model = result.scalar_one()
        await self._session.delete(model)
        await self._session.flush()

    async def count_machines(self, factory_id: UUID, tenant_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count(MachineModel.id))
            .select_from(MachineModel)
            .join(ProductionLineModel, MachineModel.production_line_id == ProductionLineModel.id)
            .where(
                ProductionLineModel.factory_id == factory_id,
                MachineModel.tenant_id == tenant_id,
            )
        )
        return result.scalar_one()

    async def count_active_alerts(self, factory_id: UUID, tenant_id: UUID) -> int:
        return await self._alert_repo.count_active_by_factory(factory_id, tenant_id)

    @staticmethod
    def _to_domain(model: FactoryModel) -> Factory:
        return Factory(
            id=model.id,
            tenant_id=model.tenant_id,
            name=model.name,
            location=model.location,
            status=FactoryStatus(model.status),
            config=model.config,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

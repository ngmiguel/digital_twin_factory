"""Machine repository."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.factory.enums import MachineStatus, MachineType
from src.domain.factory.machine import Machine
from src.infrastructure.persistence.models.factory import MachineModel, ProductionLineModel


class MachineRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, machine_id: UUID, tenant_id: UUID) -> Machine | None:
        result = await self._session.execute(
            select(MachineModel).where(
                MachineModel.id == machine_id,
                MachineModel.tenant_id == tenant_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        factory_id: UUID | None = None,
        status: MachineStatus | None = None,
        machine_type: MachineType | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[Machine], int]:
        query = select(MachineModel).where(MachineModel.tenant_id == tenant_id)

        if factory_id is not None:
            query = query.join(
                ProductionLineModel,
                MachineModel.production_line_id == ProductionLineModel.id,
            ).where(ProductionLineModel.factory_id == factory_id)

        if status is not None:
            query = query.where(MachineModel.status == status.value)
        if machine_type is not None:
            query = query.where(MachineModel.machine_type == machine_type.value)

        count_result = await self._session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            query.order_by(MachineModel.created_at.desc()).offset((page - 1) * size).limit(size)
        )
        machines = [self._to_domain(m) for m in result.scalars().all()]
        return machines, total

    async def add(self, machine: Machine) -> Machine:
        model = MachineModel(
            id=machine.id,
            tenant_id=machine.tenant_id,
            production_line_id=machine.production_line_id,
            name=machine.name,
            machine_type=machine.machine_type.value,
            status=machine.status.value,
            simulation_config=machine.simulation_config,
            failure_rate=machine.failure_rate,
            nominal_production_rate=machine.nominal_production_rate,
            created_at=machine.created_at,
            updated_at=machine.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return machine

    async def update(self, machine: Machine) -> Machine:
        result = await self._session.execute(
            select(MachineModel).where(
                MachineModel.id == machine.id,
                MachineModel.tenant_id == machine.tenant_id,
            )
        )
        model = result.scalar_one()
        model.name = machine.name
        model.status = machine.status.value
        model.simulation_config = machine.simulation_config
        model.failure_rate = machine.failure_rate
        model.nominal_production_rate = machine.nominal_production_rate
        model.updated_at = machine.updated_at
        await self._session.flush()
        return machine

    async def delete(self, machine_id: UUID, tenant_id: UUID) -> None:
        result = await self._session.execute(
            select(MachineModel).where(
                MachineModel.id == machine_id,
                MachineModel.tenant_id == tenant_id,
            )
        )
        model = result.scalar_one()
        await self._session.delete(model)
        await self._session.flush()

    @staticmethod
    def _to_domain(model: MachineModel) -> Machine:
        return Machine(
            id=model.id,
            tenant_id=model.tenant_id,
            production_line_id=model.production_line_id,
            name=model.name,
            machine_type=MachineType(model.machine_type),
            status=MachineStatus(model.status),
            simulation_config=model.simulation_config,
            failure_rate=model.failure_rate,
            nominal_production_rate=model.nominal_production_rate,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

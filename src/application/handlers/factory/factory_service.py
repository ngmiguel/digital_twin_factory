"""Factory management use cases."""

from uuid import UUID

import structlog

from src.application.dto.factory import (
    CreateFactoryRequest,
    CreateMachineRequest,
    CreateProductionLineRequest,
    FactoryListResponse,
    FactoryResponse,
    MachineListResponse,
    MachineResponse,
    ProductionLineResponse,
    UpdateFactoryRequest,
    UpdateMachineRequest,
)
from src.domain.factory.factory import Factory
from src.domain.factory.machine import Machine
from src.domain.factory.production_line import ProductionLine
from src.domain.shared.exceptions import EntityNotFoundError
from src.application.handlers.simulation.simulation_coordinator import SimulationCoordinator
from src.infrastructure.persistence.repositories.factory_repository import FactoryRepository
from src.infrastructure.persistence.repositories.machine_repository import MachineRepository
from src.infrastructure.persistence.repositories.production_line_repository import (
    ProductionLineRepository,
)
from src.infrastructure.persistence.unit_of_work import SQLAlchemyUnitOfWork

logger = structlog.get_logger()


class FactoryService:
    def __init__(
        self,
        uow: SQLAlchemyUnitOfWork,
        factory_repo: FactoryRepository,
        line_repo: ProductionLineRepository,
        machine_repo: MachineRepository,
        simulation_coordinator: SimulationCoordinator | None = None,
    ) -> None:
        self._uow = uow
        self._factory_repo = factory_repo
        self._line_repo = line_repo
        self._machine_repo = machine_repo
        self._simulation_coordinator = simulation_coordinator

    async def create_factory(self, tenant_id: UUID, request: CreateFactoryRequest) -> FactoryResponse:
        factory = Factory.create(
            tenant_id=tenant_id,
            name=request.name,
            location=request.location,
            config=request.config,
        )
        await self._factory_repo.add(factory)
        await self._uow.commit()
        logger.info("factory.created", factory_id=str(factory.id), tenant_id=str(tenant_id))
        return self._factory_to_response(factory, machine_count=0, active_alerts=0)

    async def list_factories(
        self,
        tenant_id: UUID,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> FactoryListResponse:
        from src.domain.factory.enums import FactoryStatus

        status_enum = FactoryStatus(status) if status else None
        size = min(size, 100)
        items, total = await self._factory_repo.list_by_tenant(tenant_id, status_enum, page, size)
        return FactoryListResponse(
            items=[
                self._factory_to_response(f, machine_count=mc, active_alerts=aa)
                for f, mc, aa in items
            ],
            total=total,
            page=page,
            size=size,
        )

    async def get_factory(self, tenant_id: UUID, factory_id: UUID) -> FactoryResponse:
        factory = await self._require_factory(factory_id, tenant_id)
        machine_count = await self._factory_repo.count_machines(factory_id, tenant_id)
        active_alerts = await self._factory_repo.count_active_alerts(factory_id, tenant_id)
        return self._factory_to_response(
            factory, machine_count=machine_count, active_alerts=active_alerts
        )

    async def update_factory(
        self, tenant_id: UUID, factory_id: UUID, request: UpdateFactoryRequest
    ) -> FactoryResponse:
        factory = await self._require_factory(factory_id, tenant_id)
        factory.update(
            name=request.name,
            location=request.location,
            status=request.status,
            config=request.config,
        )
        await self._factory_repo.update(factory)
        await self._uow.commit()
        return await self.get_factory(tenant_id, factory_id)

    async def delete_factory(self, tenant_id: UUID, factory_id: UUID) -> None:
        factory = await self._require_factory(factory_id, tenant_id)
        factory.mark_deleted()
        await self._factory_repo.delete(factory_id, tenant_id)
        await self._uow.commit()
        logger.info("factory.deleted", factory_id=str(factory_id), tenant_id=str(tenant_id))

    async def create_production_line(
        self, tenant_id: UUID, factory_id: UUID, request: CreateProductionLineRequest
    ) -> ProductionLineResponse:
        await self._require_factory(factory_id, tenant_id)
        line = ProductionLine.create(
            factory_id=factory_id,
            tenant_id=tenant_id,
            name=request.name,
            capacity=request.capacity,
        )
        await self._line_repo.add(line)
        await self._uow.commit()
        return self._line_to_response(line)

    async def list_production_lines(
        self, tenant_id: UUID, factory_id: UUID
    ) -> list[ProductionLineResponse]:
        await self._require_factory(factory_id, tenant_id)
        lines = await self._line_repo.list_by_factory(factory_id, tenant_id)
        return [self._line_to_response(line) for line in lines]

    async def create_machine(self, tenant_id: UUID, request: CreateMachineRequest) -> MachineResponse:
        line = await self._line_repo.get_by_id(request.production_line_id, tenant_id)
        if line is None:
            raise EntityNotFoundError("ProductionLine", request.production_line_id)

        machine = Machine.provision(
            tenant_id=tenant_id,
            production_line_id=request.production_line_id,
            name=request.name,
            machine_type=request.machine_type,
            failure_rate=request.failure_rate,
            nominal_production_rate=request.nominal_production_rate,
            simulation_config=request.simulation_config,
        )
        await self._machine_repo.add(machine)
        await self._uow.commit()
        logger.info("machine.provisioned", machine_id=str(machine.id), tenant_id=str(tenant_id))
        return self._machine_to_response(machine)

    async def list_machines(
        self,
        tenant_id: UUID,
        factory_id: UUID | None = None,
        status: str | None = None,
        machine_type: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> MachineListResponse:
        from src.domain.factory.enums import MachineStatus, MachineType

        status_enum = MachineStatus(status) if status else None
        type_enum = MachineType(machine_type) if machine_type else None
        size = min(size, 100)
        machines, total = await self._machine_repo.list_by_tenant(
            tenant_id, factory_id, status_enum, type_enum, page, size
        )
        return MachineListResponse(
            items=[self._machine_to_response(m) for m in machines],
            total=total,
            page=page,
            size=size,
        )

    async def get_machine(self, tenant_id: UUID, machine_id: UUID) -> MachineResponse:
        machine = await self._require_machine(machine_id, tenant_id)
        return self._machine_to_response(machine)

    async def update_machine(
        self, tenant_id: UUID, machine_id: UUID, request: UpdateMachineRequest
    ) -> MachineResponse:
        machine = await self._require_machine(machine_id, tenant_id)
        machine.update(
            name=request.name,
            failure_rate=request.failure_rate,
            nominal_production_rate=request.nominal_production_rate,
            simulation_config=request.simulation_config,
        )
        await self._machine_repo.update(machine)
        await self._uow.commit()
        return self._machine_to_response(machine)

    async def delete_machine(self, tenant_id: UUID, machine_id: UUID) -> None:
        await self._require_machine(machine_id, tenant_id)
        await self._machine_repo.delete(machine_id, tenant_id)
        await self._uow.commit()

    async def start_machine(self, tenant_id: UUID, machine_id: UUID) -> MachineResponse:
        machine = await self._require_machine(machine_id, tenant_id)
        machine.start()
        await self._machine_repo.update(machine)
        await self._uow.commit()
        if self._simulation_coordinator is not None:
            self._simulation_coordinator.start_simulation(tenant_id, machine_id)
        return self._machine_to_response(machine)

    async def stop_machine(self, tenant_id: UUID, machine_id: UUID) -> MachineResponse:
        machine = await self._require_machine(machine_id, tenant_id)
        machine.stop()
        await self._machine_repo.update(machine)
        await self._uow.commit()
        if self._simulation_coordinator is not None:
            self._simulation_coordinator.stop_simulation(tenant_id, machine_id)
        return self._machine_to_response(machine)

    async def _require_factory(self, factory_id: UUID, tenant_id: UUID) -> Factory:
        factory = await self._factory_repo.get_by_id(factory_id, tenant_id)
        if factory is None:
            raise EntityNotFoundError("Factory", factory_id)
        return factory

    async def _require_machine(self, machine_id: UUID, tenant_id: UUID) -> Machine:
        machine = await self._machine_repo.get_by_id(machine_id, tenant_id)
        if machine is None:
            raise EntityNotFoundError("Machine", machine_id)
        return machine

    @staticmethod
    def _factory_to_response(
        factory: Factory, machine_count: int = 0, active_alerts: int = 0
    ) -> FactoryResponse:
        return FactoryResponse(
            id=factory.id,
            name=factory.name,
            location=factory.location,
            status=factory.status,
            config=factory.config,
            machine_count=machine_count,
            active_alerts=active_alerts,
            created_at=factory.created_at,
            updated_at=factory.updated_at,
        )

    @staticmethod
    def _line_to_response(line: ProductionLine) -> ProductionLineResponse:
        return ProductionLineResponse(
            id=line.id,
            factory_id=line.factory_id,
            name=line.name,
            capacity=line.capacity,
            status=line.status,
            created_at=line.created_at,
            updated_at=line.updated_at,
        )

    @staticmethod
    def _machine_to_response(machine: Machine) -> MachineResponse:
        return MachineResponse(
            id=machine.id,
            tenant_id=machine.tenant_id,
            production_line_id=machine.production_line_id,
            name=machine.name,
            machine_type=machine.machine_type,
            status=machine.status,
            simulation_config=machine.simulation_config,
            failure_rate=machine.failure_rate,
            nominal_production_rate=machine.nominal_production_rate,
            created_at=machine.created_at,
            updated_at=machine.updated_at,
        )

"""Factory management API dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.handlers.factory.factory_service import FactoryService
from src.application.handlers.simulation.simulation_coordinator import SimulationCoordinator
from src.infrastructure.persistence.database import get_session
from src.infrastructure.persistence.repositories.factory_repository import FactoryRepository
from src.infrastructure.persistence.repositories.machine_repository import MachineRepository
from src.infrastructure.persistence.repositories.production_line_repository import (
    ProductionLineRepository,
)
from src.infrastructure.persistence.unit_of_work import SQLAlchemyUnitOfWork
from src.infrastructure.simulation.registry import SimulationRegistry


async def get_factory_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FactoryService:
    uow = SQLAlchemyUnitOfWork(session)
    simulation_coordinator = SimulationCoordinator(SimulationRegistry.from_settings())
    return FactoryService(
        uow=uow,
        factory_repo=FactoryRepository(session),
        line_repo=ProductionLineRepository(session),
        machine_repo=MachineRepository(session),
        simulation_coordinator=simulation_coordinator,
    )

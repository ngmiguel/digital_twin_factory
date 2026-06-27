"""Prediction API dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.handlers.prediction.maintenance_service import MaintenanceService
from src.application.handlers.prediction.prediction_service import PredictionService
from src.infrastructure.persistence.database import get_session
from src.infrastructure.persistence.repositories.machine_repository import MachineRepository
from src.infrastructure.persistence.repositories.maintenance_repository import MaintenanceRepository
from src.infrastructure.persistence.repositories.metric_repository import MetricRepository
from src.infrastructure.persistence.repositories.prediction_repository import PredictionRepository
from src.infrastructure.persistence.unit_of_work import SQLAlchemyUnitOfWork


async def get_prediction_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PredictionService:
    uow = SQLAlchemyUnitOfWork(session)
    return PredictionService(
        uow=uow,
        machine_repo=MachineRepository(session),
        metric_repo=MetricRepository(session),
        prediction_repo=PredictionRepository(session),
        maintenance_repo=MaintenanceRepository(session),
    )


async def get_maintenance_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MaintenanceService:
    uow = SQLAlchemyUnitOfWork(session)
    return MaintenanceService(
        uow=uow,
        machine_repo=MachineRepository(session),
        maintenance_repo=MaintenanceRepository(session),
    )

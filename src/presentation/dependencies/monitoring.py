"""Monitoring API dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.handlers.monitoring.alert_service import AlertService
from src.infrastructure.persistence.database import get_session
from src.infrastructure.persistence.repositories.alert_repository import AlertRepository
from src.infrastructure.persistence.unit_of_work import SQLAlchemyUnitOfWork


async def get_alert_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AlertService:
    uow = SQLAlchemyUnitOfWork(session)
    return AlertService(uow=uow, alert_repo=AlertRepository(session))

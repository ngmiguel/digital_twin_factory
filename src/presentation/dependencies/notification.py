"""Notification API dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.handlers.notification.notification_service import NotificationService
from src.infrastructure.cache.redis_client import _redis_client
from src.infrastructure.persistence.database import get_session
from src.infrastructure.persistence.repositories.notification_repository import NotificationRepository
from src.infrastructure.persistence.repositories.user_repository import UserRepository
from src.infrastructure.persistence.unit_of_work import SQLAlchemyUnitOfWork


async def get_notification_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> NotificationService:
    uow = SQLAlchemyUnitOfWork(session)
    return NotificationService(
        uow=uow,
        notification_repo=NotificationRepository(session),
        user_repo=UserRepository(session),
        redis=_redis_client,
    )

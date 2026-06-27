"""Unit of Work implementation."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces import UnitOfWork


class SQLAlchemyUnitOfWork(UnitOfWork):
    """SQLAlchemy-backed Unit of Work."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            await self.rollback()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    @property
    def session(self) -> AsyncSession:
        return self._session

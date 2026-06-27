"""Application interfaces — repository and unit of work contracts."""

from abc import ABC, abstractmethod
from typing import TypeVar
from uuid import UUID

T = TypeVar("T")


class Repository(ABC):
    """Generic repository interface."""

    @abstractmethod
    async def get_by_id(self, entity_id: UUID) -> T | None:
        ...

    @abstractmethod
    async def add(self, entity: T) -> T:
        ...

    @abstractmethod
    async def update(self, entity: T) -> T:
        ...

    @abstractmethod
    async def delete(self, entity_id: UUID) -> None:
        ...


class UnitOfWork(ABC):
    """Unit of Work pattern — atomic transaction boundary."""

    @abstractmethod
    async def __aenter__(self) -> "UnitOfWork":
        ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        ...

    @abstractmethod
    async def commit(self) -> None:
        ...

    @abstractmethod
    async def rollback(self) -> None:
        ...

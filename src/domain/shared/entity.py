"""Base entity."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict


class Entity(BaseModel):
    """Base class for domain entities identified by UUID."""

    model_config = ConfigDict(frozen=False)

    id: UUID
    created_at: datetime
    updated_at: datetime

    @classmethod
    def new_id(cls) -> UUID:
        return uuid4()

    @classmethod
    def now(cls) -> datetime:
        return datetime.now(UTC)

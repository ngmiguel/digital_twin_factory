"""Base value object."""

from pydantic import BaseModel, ConfigDict


class ValueObject(BaseModel):
    """Immutable value object base."""

    model_config = ConfigDict(frozen=True)

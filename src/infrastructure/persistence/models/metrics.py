"""Machine metrics ORM model."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.persistence.base import Base


class MachineMetricModel(Base):
    __tablename__ = "machine_metrics"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    machine_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
    vibration: Mapped[float] = mapped_column(Float, nullable=False)
    power_consumption: Mapped[float] = mapped_column(Float, nullable=False)
    production_rate: Mapped[float] = mapped_column(Float, nullable=False)
    machine_status: Mapped[str] = mapped_column(String(50), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )

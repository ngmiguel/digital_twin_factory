"""Machine metrics repository."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.simulation.metric_snapshot import MetricSnapshot
from src.infrastructure.persistence.models.metrics import MachineMetricModel


class MetricRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_snapshot(
        self,
        machine_id: UUID,
        tenant_id: UUID,
        snapshot: MetricSnapshot,
        recorded_at: datetime | None = None,
    ) -> None:
        model = MachineMetricModel(
            id=uuid4(),
            machine_id=machine_id,
            tenant_id=tenant_id,
            temperature=snapshot.temperature,
            vibration=snapshot.vibration,
            power_consumption=snapshot.power_consumption,
            production_rate=snapshot.production_rate,
            machine_status=snapshot.machine_status.value,
            recorded_at=recorded_at or datetime.now(UTC),
        )
        self._session.add(model)
        await self._session.flush()

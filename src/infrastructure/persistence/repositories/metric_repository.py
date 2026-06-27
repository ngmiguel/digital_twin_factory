"""Machine metrics repository."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.factory.enums import MachineStatus
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

    async def list_recent(
        self,
        machine_id: UUID,
        tenant_id: UUID,
        hours: int = 24,
        limit: int = 500,
    ) -> list[MetricSnapshot]:
        since = datetime.now(UTC) - timedelta(hours=hours)
        result = await self._session.execute(
            select(MachineMetricModel)
            .where(
                MachineMetricModel.machine_id == machine_id,
                MachineMetricModel.tenant_id == tenant_id,
                MachineMetricModel.recorded_at >= since,
            )
            .order_by(MachineMetricModel.recorded_at.asc())
            .limit(limit)
        )
        return [self._to_snapshot(m) for m in result.scalars().all()]

    @staticmethod
    def _to_snapshot(model: MachineMetricModel) -> MetricSnapshot:
        return MetricSnapshot(
            temperature=model.temperature,
            vibration=model.vibration,
            power_consumption=model.power_consumption,
            production_rate=model.production_rate,
            machine_status=MachineStatus(model.machine_status),
        )

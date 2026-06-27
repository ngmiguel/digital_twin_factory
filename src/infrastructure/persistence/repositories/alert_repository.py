"""Alert repository."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.monitoring.alert import Alert
from src.domain.monitoring.enums import AlertSeverity, AlertType
from src.infrastructure.persistence.models.factory import MachineModel, ProductionLineModel
from src.infrastructure.persistence.models.monitoring import AlertModel


class AlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, alert_id: UUID, tenant_id: UUID) -> Alert | None:
        result = await self._session.execute(
            select(AlertModel).where(
                AlertModel.id == alert_id,
                AlertModel.tenant_id == tenant_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        severity: AlertSeverity | None = None,
        machine_id: UUID | None = None,
        is_resolved: bool | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[Alert], int]:
        query = select(AlertModel).where(AlertModel.tenant_id == tenant_id)

        if severity is not None:
            query = query.where(AlertModel.severity == severity.value)
        if machine_id is not None:
            query = query.where(AlertModel.machine_id == machine_id)
        if is_resolved is not None:
            query = query.where(AlertModel.is_resolved == is_resolved)

        count_result = await self._session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            query.order_by(AlertModel.created_at.desc()).offset((page - 1) * size).limit(size)
        )
        alerts = [self._to_domain(m) for m in result.scalars().all()]
        return alerts, total

    async def add(self, alert: Alert) -> Alert:
        model = AlertModel(
            id=alert.id,
            tenant_id=alert.tenant_id,
            machine_id=alert.machine_id,
            alert_type=alert.alert_type.value,
            severity=alert.severity.value,
            message=alert.message,
            alert_metadata=alert.metadata,
            is_acknowledged=alert.is_acknowledged,
            acknowledged_by=alert.acknowledged_by,
            acknowledged_at=alert.acknowledged_at,
            is_resolved=alert.is_resolved,
            resolved_at=alert.resolved_at,
            created_at=alert.created_at,
            updated_at=alert.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return alert

    async def update(self, alert: Alert) -> Alert:
        result = await self._session.execute(
            select(AlertModel).where(
                AlertModel.id == alert.id,
                AlertModel.tenant_id == alert.tenant_id,
            )
        )
        model = result.scalar_one()
        model.is_acknowledged = alert.is_acknowledged
        model.acknowledged_by = alert.acknowledged_by
        model.acknowledged_at = alert.acknowledged_at
        model.is_resolved = alert.is_resolved
        model.resolved_at = alert.resolved_at
        model.updated_at = alert.updated_at
        await self._session.flush()
        return alert

    async def has_active_alert(
        self, machine_id: UUID, tenant_id: UUID, alert_type: AlertType
    ) -> bool:
        result = await self._session.execute(
            select(func.count())
            .select_from(AlertModel)
            .where(
                AlertModel.machine_id == machine_id,
                AlertModel.tenant_id == tenant_id,
                AlertModel.alert_type == alert_type.value,
                AlertModel.is_resolved.is_(False),
            )
        )
        return result.scalar_one() > 0

    async def count_active_by_factory(self, factory_id: UUID, tenant_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(AlertModel)
            .join(MachineModel, AlertModel.machine_id == MachineModel.id)
            .join(ProductionLineModel, MachineModel.production_line_id == ProductionLineModel.id)
            .where(
                ProductionLineModel.factory_id == factory_id,
                AlertModel.tenant_id == tenant_id,
                AlertModel.is_resolved.is_(False),
            )
        )
        return result.scalar_one()

    @staticmethod
    def _to_domain(model: AlertModel) -> Alert:
        return Alert(
            id=model.id,
            tenant_id=model.tenant_id,
            machine_id=model.machine_id,
            alert_type=AlertType(model.alert_type),
            severity=AlertSeverity(model.severity),
            message=model.message,
            metadata=model.alert_metadata,
            is_acknowledged=model.is_acknowledged,
            acknowledged_by=model.acknowledged_by,
            acknowledged_at=model.acknowledged_at,
            is_resolved=model.is_resolved,
            resolved_at=model.resolved_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

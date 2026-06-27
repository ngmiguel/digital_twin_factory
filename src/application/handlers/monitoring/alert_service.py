"""Alert management use cases."""

import json
from datetime import UTC, datetime
from uuid import UUID

import structlog
from redis.asyncio import Redis

from src.application.dto.monitoring import AlertListResponse, AlertResponse, ResolveAlertRequest
from src.domain.factory.machine import Machine
from src.domain.monitoring.alert import Alert
from src.domain.monitoring.enums import AlertSeverity, AlertType
from src.domain.monitoring.threshold_evaluator import ThresholdEvaluator
from src.domain.shared.exceptions import EntityNotFoundError
from src.domain.simulation.metric_snapshot import MetricSnapshot
from src.infrastructure.messaging.redis_channels import factory_alerts_channel
from src.infrastructure.persistence.repositories.alert_repository import AlertRepository
from src.infrastructure.persistence.unit_of_work import SQLAlchemyUnitOfWork

logger = structlog.get_logger()


class AlertService:
    def __init__(
        self,
        uow: SQLAlchemyUnitOfWork,
        alert_repo: AlertRepository,
        evaluator: ThresholdEvaluator | None = None,
    ) -> None:
        self._uow = uow
        self._alert_repo = alert_repo
        self._evaluator = evaluator or ThresholdEvaluator()

    async def list_alerts(
        self,
        tenant_id: UUID,
        severity: str | None = None,
        machine_id: UUID | None = None,
        is_resolved: bool | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> AlertListResponse:
        severity_enum = AlertSeverity(severity) if severity else None
        if status == "active":
            is_resolved = False

        size = min(size, 100)
        alerts, total = await self._alert_repo.list_by_tenant(
            tenant_id,
            severity=severity_enum,
            machine_id=machine_id,
            is_resolved=is_resolved,
            page=page,
            size=size,
        )
        return AlertListResponse(
            items=[self._to_response(a) for a in alerts],
            total=total,
            page=page,
            size=size,
        )

    async def acknowledge_alert(
        self, tenant_id: UUID, alert_id: UUID, user_id: UUID
    ) -> AlertResponse:
        alert = await self._require_alert(alert_id, tenant_id)
        alert.acknowledge(user_id)
        await self._alert_repo.update(alert)
        await self._uow.commit()
        logger.info("alert.acknowledged", alert_id=str(alert_id), user_id=str(user_id))
        return self._to_response(alert)

    async def resolve_alert(
        self, tenant_id: UUID, alert_id: UUID, request: ResolveAlertRequest
    ) -> AlertResponse:
        alert = await self._require_alert(alert_id, tenant_id)
        alert.resolve(request.resolution)
        await self._alert_repo.update(alert)
        await self._uow.commit()
        logger.info("alert.resolved", alert_id=str(alert_id))
        return self._to_response(alert)

    async def process_simulation_tick(
        self,
        machine: Machine,
        metrics: MetricSnapshot,
        factory_id: UUID,
        redis: Redis,
        machine_failed: bool = False,
    ) -> list[Alert]:
        raised: list[Alert] = []

        if machine_failed:
            alert = await self._raise_if_new(
                machine,
                AlertType.MACHINE_FAILURE,
                AlertSeverity.EMERGENCY,
                f"Machine {machine.name} has failed",
                {"machine_id": str(machine.id)},
            )
            if alert:
                raised.append(alert)
                await self._publish_alert(redis, machine.tenant_id, factory_id, machine.id, alert)

        for violation in self._evaluator.evaluate(machine, metrics):
            alert = await self._raise_if_new(
                machine,
                violation.alert_type,
                violation.severity,
                violation.message,
                {
                    "metric_name": violation.metric_name,
                    "value": violation.value,
                    "threshold": violation.threshold,
                },
            )
            if alert:
                raised.append(alert)
                await self._publish_alert(redis, machine.tenant_id, factory_id, machine.id, alert)

        if raised:
            logger.info(
                "alert.raised",
                machine_id=str(machine.id),
                count=len(raised),
            )

        return raised

    async def _raise_if_new(
        self,
        machine: Machine,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        metadata: dict[str, object],
    ) -> Alert | None:
        if await self._alert_repo.has_active_alert(machine.id, machine.tenant_id, alert_type):
            return None

        alert = Alert.raise_alert(
            tenant_id=machine.tenant_id,
            machine_id=machine.id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            metadata=metadata,
        )
        await self._alert_repo.add(alert)
        return alert

    async def _require_alert(self, alert_id: UUID, tenant_id: UUID) -> Alert:
        alert = await self._alert_repo.get_by_id(alert_id, tenant_id)
        if alert is None:
            raise EntityNotFoundError("Alert", alert_id)
        return alert

    async def _publish_alert(
        self,
        redis: Redis,
        tenant_id: UUID,
        factory_id: UUID,
        machine_id: UUID,
        alert: Alert,
    ) -> None:
        channel = factory_alerts_channel(tenant_id, factory_id)
        payload = json.dumps(
            {
                "type": "alert",
                "alert_id": str(alert.id),
                "factory_id": str(factory_id),
                "machine_id": str(machine_id),
                "alert_type": alert.alert_type.value,
                "severity": alert.severity.value,
                "message": alert.message,
                "metadata": alert.metadata,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        await redis.publish(channel, payload)

        if alert.severity in (AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY):
            from src.infrastructure.tasks.notification import notify_alert

            notify_alert.delay(
                str(tenant_id),
                str(alert.id),
                alert.severity.value,
                alert.message,
                str(machine_id),
                alert.alert_type.value,
            )

    @staticmethod
    def _to_response(alert: Alert) -> AlertResponse:
        return AlertResponse(
            id=alert.id,
            tenant_id=alert.tenant_id,
            machine_id=alert.machine_id,
            alert_type=alert.alert_type,
            severity=alert.severity,
            message=alert.message,
            metadata=alert.metadata,
            is_acknowledged=alert.is_acknowledged,
            acknowledged_by=alert.acknowledged_by,
            acknowledged_at=alert.acknowledged_at,
            is_resolved=alert.is_resolved,
            resolved_at=alert.resolved_at,
            created_at=alert.created_at,
            updated_at=alert.updated_at,
        )

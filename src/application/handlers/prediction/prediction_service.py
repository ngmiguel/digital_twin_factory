"""Predictive maintenance use cases."""

from uuid import UUID

import structlog

from src.application.dto.prediction import (
    CreateMaintenanceRequest,
    MaintenanceListResponse,
    MaintenanceResponse,
    PredictionListResponse,
    PredictionResponse,
)
from src.domain.prediction.enums import MaintenanceStatus, MaintenanceType, PredictionType
from src.domain.prediction.failure_predictor import FailurePredictor
from src.domain.prediction.maintenance_record import MaintenanceRecord
from src.domain.prediction.prediction import Prediction
from src.domain.shared.exceptions import EntityNotFoundError
from src.infrastructure.persistence.repositories.machine_repository import MachineRepository
from src.infrastructure.persistence.repositories.maintenance_repository import MaintenanceRepository
from src.infrastructure.persistence.repositories.metric_repository import MetricRepository
from src.infrastructure.persistence.repositories.prediction_repository import PredictionRepository
from src.infrastructure.persistence.unit_of_work import SQLAlchemyUnitOfWork

logger = structlog.get_logger()


class PredictionService:
    def __init__(
        self,
        uow: SQLAlchemyUnitOfWork,
        machine_repo: MachineRepository,
        metric_repo: MetricRepository,
        prediction_repo: PredictionRepository,
        maintenance_repo: MaintenanceRepository,
        predictor: FailurePredictor | None = None,
    ) -> None:
        self._uow = uow
        self._machine_repo = machine_repo
        self._metric_repo = metric_repo
        self._prediction_repo = prediction_repo
        self._maintenance_repo = maintenance_repo
        self._predictor = predictor or FailurePredictor()

    async def list_machine_predictions(
        self,
        tenant_id: UUID,
        machine_id: UUID,
        valid_only: bool = True,
        page: int = 1,
        size: int = 20,
    ) -> PredictionListResponse:
        await self._require_machine(machine_id, tenant_id)
        size = min(size, 100)
        predictions, total = await self._prediction_repo.list_by_machine(
            machine_id, tenant_id, valid_only=valid_only, page=page, size=size
        )
        return PredictionListResponse(
            predictions=[self._prediction_to_response(p) for p in predictions],
            total=total,
            page=page,
            size=size,
        )

    async def run_failure_prediction(self, tenant_id: UUID, machine_id: UUID) -> Prediction | None:
        machine = await self._require_machine(machine_id, tenant_id)
        history = await self._metric_repo.list_recent(machine_id, tenant_id, hours=24)

        result = self._predictor.predict(machine, history)
        if result is None:
            return None

        if await self._prediction_repo.has_valid_prediction(
            machine_id, tenant_id, result.prediction_type
        ):
            return None

        prediction = Prediction.create(
            tenant_id=tenant_id,
            machine_id=machine_id,
            prediction_type=result.prediction_type,
            confidence=result.confidence,
            features=result.features,
        )
        await self._prediction_repo.add(prediction)
        await self._schedule_maintenance_if_needed(tenant_id, machine_id, prediction)
        await self._uow.commit()

        logger.info(
            "prediction.created",
            machine_id=str(machine_id),
            confidence=result.confidence,
            prediction_type=result.prediction_type.value,
        )
        return prediction

    async def _schedule_maintenance_if_needed(
        self, tenant_id: UUID, machine_id: UUID, prediction: Prediction
    ) -> MaintenanceRecord | None:
        if await self._maintenance_repo.has_scheduled_for_machine(machine_id, tenant_id):
            return None

        if prediction.prediction_type != PredictionType.FAILURE_WITHIN_24H:
            return None

        record = MaintenanceRecord.schedule(
            tenant_id=tenant_id,
            machine_id=machine_id,
            maintenance_type=MaintenanceType.PREDICTIVE,
            description=f"Predictive maintenance scheduled (confidence {prediction.confidence:.0%})",
            prediction_id=prediction.id,
        )
        await self._maintenance_repo.add(record)
        logger.info("maintenance.scheduled", machine_id=str(machine_id), maintenance_id=str(record.id))

        from src.infrastructure.tasks.notification import notify_maintenance

        notify_maintenance.delay(
            str(tenant_id),
            str(record.id),
            str(machine_id),
            record.description,
        )
        return record

    async def _require_machine(self, machine_id: UUID, tenant_id: UUID) -> object:
        machine = await self._machine_repo.get_by_id(machine_id, tenant_id)
        if machine is None:
            raise EntityNotFoundError("Machine", machine_id)
        return machine

    @staticmethod
    def _prediction_to_response(prediction: Prediction) -> PredictionResponse:
        return PredictionResponse(
            id=prediction.id,
            tenant_id=prediction.tenant_id,
            machine_id=prediction.machine_id,
            prediction_type=prediction.prediction_type,
            confidence=prediction.confidence,
            features=prediction.features,
            predicted_at=prediction.predicted_at,
            valid_until=prediction.valid_until,
            created_at=prediction.created_at,
        )

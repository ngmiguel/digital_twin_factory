"""Prediction repository."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.prediction.enums import PredictionType
from src.domain.prediction.prediction import Prediction
from src.infrastructure.persistence.models.prediction import PredictionModel


class PredictionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, prediction_id: UUID, tenant_id: UUID) -> Prediction | None:
        result = await self._session.execute(
            select(PredictionModel).where(
                PredictionModel.id == prediction_id,
                PredictionModel.tenant_id == tenant_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_machine(
        self,
        machine_id: UUID,
        tenant_id: UUID,
        valid_only: bool = True,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[Prediction], int]:
        query = select(PredictionModel).where(
            PredictionModel.machine_id == machine_id,
            PredictionModel.tenant_id == tenant_id,
        )
        if valid_only:
            query = query.where(PredictionModel.valid_until >= func.now())

        count_result = await self._session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            query.order_by(PredictionModel.predicted_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        return [self._to_domain(m) for m in result.scalars().all()], total

    async def add(self, prediction: Prediction) -> Prediction:
        model = PredictionModel(
            id=prediction.id,
            tenant_id=prediction.tenant_id,
            machine_id=prediction.machine_id,
            prediction_type=prediction.prediction_type.value,
            confidence=prediction.confidence,
            feature_data=prediction.features,
            predicted_at=prediction.predicted_at,
            valid_until=prediction.valid_until,
            created_at=prediction.created_at,
            updated_at=prediction.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return prediction

    async def has_valid_prediction(
        self, machine_id: UUID, tenant_id: UUID, prediction_type: PredictionType
    ) -> bool:
        result = await self._session.execute(
            select(func.count())
            .select_from(PredictionModel)
            .where(
                PredictionModel.machine_id == machine_id,
                PredictionModel.tenant_id == tenant_id,
                PredictionModel.prediction_type == prediction_type.value,
                PredictionModel.valid_until >= func.now(),
            )
        )
        return result.scalar_one() > 0

    @staticmethod
    def _to_domain(model: PredictionModel) -> Prediction:
        return Prediction(
            id=model.id,
            tenant_id=model.tenant_id,
            machine_id=model.machine_id,
            prediction_type=PredictionType(model.prediction_type),
            confidence=model.confidence,
            features=model.feature_data,
            predicted_at=model.predicted_at,
            valid_until=model.valid_until,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

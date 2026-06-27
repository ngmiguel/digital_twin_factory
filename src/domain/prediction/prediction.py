"""Prediction aggregate root."""

from datetime import datetime, timedelta
from uuid import UUID

from src.domain.prediction.enums import PredictionType
from src.domain.prediction.events import FailurePredicted
from src.domain.shared.aggregate_root import AggregateRoot
from src.domain.shared.entity import Entity
from src.domain.shared.exceptions import ValidationError


class Prediction(AggregateRoot):
    tenant_id: UUID
    machine_id: UUID
    prediction_type: PredictionType
    confidence: float
    features: dict[str, object]
    predicted_at: datetime
    valid_until: datetime

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        machine_id: UUID,
        prediction_type: PredictionType,
        confidence: float,
        features: dict[str, object],
        valid_hours: int = 24,
    ) -> "Prediction":
        if confidence <= 0 or confidence > 1:
            raise ValidationError("Confidence must be between 0 and 1", field="confidence")

        now = Entity.now()
        prediction = cls(
            id=Entity.new_id(),
            tenant_id=tenant_id,
            machine_id=machine_id,
            prediction_type=prediction_type,
            confidence=confidence,
            features=features,
            predicted_at=now,
            valid_until=now + timedelta(hours=valid_hours),
            created_at=now,
            updated_at=now,
        )
        prediction.add_event(
            FailurePredicted.create(
                tenant_id=tenant_id,
                aggregate_id=prediction.id,
                prediction_id=prediction.id,
                machine_id=machine_id,
                confidence=confidence,
                prediction_type=prediction_type.value,
            )
        )
        return prediction

    def is_valid(self, at: datetime | None = None) -> bool:
        reference = at or Entity.now()
        return reference <= self.valid_until

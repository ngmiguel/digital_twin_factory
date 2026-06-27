"""Unit tests for prediction domain."""

from uuid import uuid4

import pytest

from src.domain.factory.enums import MachineStatus, MachineType
from src.domain.factory.machine import Machine
from src.domain.prediction.enums import MaintenanceStatus, MaintenanceType, PredictionType
from src.domain.prediction.failure_predictor import FailurePredictor
from src.domain.prediction.maintenance_record import MaintenanceRecord
from src.domain.prediction.prediction import Prediction
from src.domain.shared.exceptions import ValidationError
from src.domain.simulation.metric_snapshot import MetricSnapshot


def _make_machine(failure_rate: float = 0.05) -> Machine:
    return Machine.provision(
        tenant_id=uuid4(),
        production_line_id=uuid4(),
        name="Press-001",
        machine_type=MachineType.PRESS,
        nominal_production_rate=100.0,
        failure_rate=failure_rate,
    )


def _degraded_history(count: int = 10) -> list[MetricSnapshot]:
    snapshots: list[MetricSnapshot] = []
    for i in range(count):
        snapshots.append(
            MetricSnapshot(
                temperature=70.0 + i * 8.0,
                vibration=5.0 + i * 2.0,
                power_consumption=50.0 + i * 5.0,
                production_rate=90.0 - i * 8.0,
                machine_status=MachineStatus.RUNNING,
            )
        )
    return snapshots


def test_failure_predictor_detects_high_risk() -> None:
    machine = _make_machine(failure_rate=0.1)
    predictor = FailurePredictor()
    result = predictor.predict(machine, _degraded_history())
    assert result is not None
    assert result.confidence >= FailurePredictor.CONFIDENCE_THRESHOLD
    assert result.prediction_type in (
        PredictionType.FAILURE_WITHIN_24H,
        PredictionType.DEGRADATION_TREND,
    )


def test_failure_predictor_skips_insufficient_data() -> None:
    machine = _make_machine()
    predictor = FailurePredictor()
    result = predictor.predict(machine, _degraded_history(count=2))
    assert result is None


def test_prediction_create_emits_event() -> None:
    prediction = Prediction.create(
        tenant_id=uuid4(),
        machine_id=uuid4(),
        prediction_type=PredictionType.FAILURE_WITHIN_24H,
        confidence=0.87,
        features={"anomaly_score": 0.82},
    )
    assert prediction.is_valid()
    assert len(prediction.events) == 1


def test_maintenance_lifecycle() -> None:
    record = MaintenanceRecord.schedule(
        tenant_id=uuid4(),
        machine_id=uuid4(),
        maintenance_type=MaintenanceType.PREDICTIVE,
        description="Replace worn bearing",
    )
    assert record.status == MaintenanceStatus.SCHEDULED

    record.start()
    assert record.status == MaintenanceStatus.IN_PROGRESS

    record.complete()
    assert record.status == MaintenanceStatus.COMPLETED


def test_machine_complete_maintenance_from_failure() -> None:
    machine = _make_machine()
    machine.status = MachineStatus.FAILURE
    machine.complete_maintenance()
    assert machine.status == MachineStatus.OFFLINE


def test_machine_cannot_complete_maintenance_from_running() -> None:
    machine = _make_machine()
    machine.start()
    with pytest.raises(ValidationError):
        machine.complete_maintenance()

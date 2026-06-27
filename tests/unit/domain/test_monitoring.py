"""Unit tests for monitoring domain."""

from uuid import uuid4

from src.domain.factory.enums import MachineStatus, MachineType
from src.domain.factory.machine import Machine
from src.domain.monitoring.alert import Alert
from src.domain.monitoring.enums import AlertSeverity, AlertType
from src.domain.monitoring.threshold_evaluator import ThresholdEvaluator
from src.domain.shared.exceptions import ValidationError
from src.domain.simulation.metric_snapshot import MetricSnapshot


def _make_machine() -> Machine:
    return Machine.provision(
        tenant_id=uuid4(),
        production_line_id=uuid4(),
        name="CNC-001",
        machine_type=MachineType.CNC_MILL,
        nominal_production_rate=100.0,
    )


def _make_metrics(
    temperature: float = 50.0,
    vibration: float = 2.0,
    power: float = 30.0,
    production_rate: float = 95.0,
) -> MetricSnapshot:
    return MetricSnapshot(
        temperature=temperature,
        vibration=vibration,
        power_consumption=power,
        production_rate=production_rate,
        machine_status=MachineStatus.RUNNING,
    )


def test_temperature_critical_threshold_violation() -> None:
    machine = _make_machine()
    evaluator = ThresholdEvaluator()
    violations = evaluator.evaluate(machine, _make_metrics(temperature=96.0))
    assert len(violations) == 1
    assert violations[0].severity == AlertSeverity.CRITICAL
    assert violations[0].alert_type == AlertType.TEMPERATURE_HIGH


def test_temperature_warning_threshold_violation() -> None:
    machine = _make_machine()
    evaluator = ThresholdEvaluator()
    violations = evaluator.evaluate(machine, _make_metrics(temperature=88.0))
    assert len(violations) == 1
    assert violations[0].severity == AlertSeverity.WARNING


def test_production_drop_critical_below_nominal() -> None:
    machine = _make_machine()
    evaluator = ThresholdEvaluator()
    violations = evaluator.evaluate(machine, _make_metrics(production_rate=40.0))
    assert len(violations) == 1
    assert violations[0].severity == AlertSeverity.CRITICAL
    assert violations[0].alert_type == AlertType.PRODUCTION_DROP


def test_no_violation_when_metrics_normal() -> None:
    machine = _make_machine()
    evaluator = ThresholdEvaluator()
    violations = evaluator.evaluate(machine, _make_metrics())
    assert violations == []


def test_alert_raise_and_acknowledge() -> None:
    tenant_id = uuid4()
    machine_id = uuid4()
    user_id = uuid4()

    alert = Alert.raise_alert(
        tenant_id=tenant_id,
        machine_id=machine_id,
        alert_type=AlertType.TEMPERATURE_HIGH,
        severity=AlertSeverity.WARNING,
        message="High temperature",
    )
    assert alert.is_acknowledged is False
    assert len(alert.events) == 1

    alert.acknowledge(user_id)
    assert alert.is_acknowledged is True
    assert alert.acknowledged_by == user_id


def test_alert_resolve_requires_message() -> None:
    alert = Alert.raise_alert(
        tenant_id=uuid4(),
        machine_id=uuid4(),
        alert_type=AlertType.VIBRATION_CRITICAL,
        severity=AlertSeverity.CRITICAL,
        message="Vibration spike",
    )
    try:
        alert.resolve("   ")
        assert False, "expected ValidationError"
    except ValidationError:
        pass

    alert.resolve("Replaced bearing")
    assert alert.is_resolved is True

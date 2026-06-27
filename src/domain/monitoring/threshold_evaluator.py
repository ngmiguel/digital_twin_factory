"""Threshold evaluation — pure domain logic."""

from dataclasses import dataclass

from src.domain.factory.machine import Machine
from src.domain.monitoring.enums import AlertSeverity, AlertType, ComparisonOperator
from src.domain.simulation.metric_snapshot import MetricSnapshot


@dataclass(frozen=True)
class ThresholdRule:
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    comparison_operator: ComparisonOperator = ComparisonOperator.GREATER_THAN
    alert_type_warning: AlertType = AlertType.TEMPERATURE_HIGH
    alert_type_critical: AlertType = AlertType.TEMPERATURE_HIGH


@dataclass(frozen=True)
class ThresholdViolation:
    metric_name: str
    value: float
    threshold: float
    severity: AlertSeverity
    alert_type: AlertType
    message: str


class ThresholdEvaluator:
    """Evaluate metrics against threshold rules."""

    def evaluate(self, machine: Machine, metrics: MetricSnapshot) -> list[ThresholdViolation]:
        violations: list[ThresholdViolation] = []
        metric_values = {
            "temperature": metrics.temperature,
            "vibration": metrics.vibration,
            "power_consumption": metrics.power_consumption,
            "production_rate": metrics.production_rate,
        }

        for rule in self._rules_for_machine(machine):
            value = metric_values.get(rule.metric_name)
            if value is None:
                continue
            violation = self._check_rule(rule, value, machine)
            if violation:
                violations.append(violation)

        return violations

    def _rules_for_machine(self, machine: Machine) -> list[ThresholdRule]:
        nominal = machine.nominal_production_rate
        return [
            ThresholdRule(
                metric_name="temperature",
                warning_threshold=85.0,
                critical_threshold=95.0,
                comparison_operator=ComparisonOperator.GREATER_THAN,
                alert_type_warning=AlertType.TEMPERATURE_HIGH,
                alert_type_critical=AlertType.TEMPERATURE_HIGH,
            ),
            ThresholdRule(
                metric_name="vibration",
                warning_threshold=7.0,
                critical_threshold=12.0,
                comparison_operator=ComparisonOperator.GREATER_THAN,
                alert_type_warning=AlertType.VIBRATION_CRITICAL,
                alert_type_critical=AlertType.VIBRATION_CRITICAL,
            ),
            ThresholdRule(
                metric_name="power_consumption",
                warning_threshold=60.0,
                critical_threshold=80.0,
                comparison_operator=ComparisonOperator.GREATER_THAN,
                alert_type_warning=AlertType.POWER_SPIKE,
                alert_type_critical=AlertType.POWER_SPIKE,
            ),
            ThresholdRule(
                metric_name="production_rate",
                warning_threshold=nominal * 0.7,
                critical_threshold=nominal * 0.5,
                comparison_operator=ComparisonOperator.LESS_THAN,
                alert_type_warning=AlertType.PRODUCTION_DROP,
                alert_type_critical=AlertType.PRODUCTION_DROP,
            ),
        ]

    def _check_rule(
        self, rule: ThresholdRule, value: float, machine: Machine
    ) -> ThresholdViolation | None:
        if rule.comparison_operator == ComparisonOperator.GREATER_THAN:
            if value >= rule.critical_threshold:
                return ThresholdViolation(
                    metric_name=rule.metric_name,
                    value=value,
                    threshold=rule.critical_threshold,
                    severity=AlertSeverity.CRITICAL,
                    alert_type=rule.alert_type_critical,
                    message=(
                        f"{rule.metric_name} critical on {machine.name}: "
                        f"{value:.2f} >= {rule.critical_threshold:.2f}"
                    ),
                )
            if value >= rule.warning_threshold:
                return ThresholdViolation(
                    metric_name=rule.metric_name,
                    value=value,
                    threshold=rule.warning_threshold,
                    severity=AlertSeverity.WARNING,
                    alert_type=rule.alert_type_warning,
                    message=(
                        f"{rule.metric_name} warning on {machine.name}: "
                        f"{value:.2f} >= {rule.warning_threshold:.2f}"
                    ),
                )
        elif rule.comparison_operator == ComparisonOperator.LESS_THAN:
            if value <= rule.critical_threshold:
                return ThresholdViolation(
                    metric_name=rule.metric_name,
                    value=value,
                    threshold=rule.critical_threshold,
                    severity=AlertSeverity.CRITICAL,
                    alert_type=rule.alert_type_critical,
                    message=(
                        f"{rule.metric_name} critical on {machine.name}: "
                        f"{value:.2f} <= {rule.critical_threshold:.2f}"
                    ),
                )
            if value <= rule.warning_threshold:
                return ThresholdViolation(
                    metric_name=rule.metric_name,
                    value=value,
                    threshold=rule.warning_threshold,
                    severity=AlertSeverity.WARNING,
                    alert_type=rule.alert_type_warning,
                    message=(
                        f"{rule.metric_name} warning on {machine.name}: "
                        f"{value:.2f} <= {rule.warning_threshold:.2f}"
                    ),
                )
        return None

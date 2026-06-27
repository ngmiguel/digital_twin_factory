"""Monitoring bounded context enums."""

from enum import StrEnum


class AlertSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class AlertType(StrEnum):
    TEMPERATURE_HIGH = "TEMPERATURE_HIGH"
    VIBRATION_CRITICAL = "VIBRATION_CRITICAL"
    POWER_SPIKE = "POWER_SPIKE"
    PRODUCTION_DROP = "PRODUCTION_DROP"
    MACHINE_FAILURE = "MACHINE_FAILURE"
    PREDICTIVE_WARNING = "PREDICTIVE_WARNING"


class ComparisonOperator(StrEnum):
    GREATER_THAN = "GT"
    LESS_THAN = "LT"

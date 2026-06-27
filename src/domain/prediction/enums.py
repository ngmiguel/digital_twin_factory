"""Prediction bounded context enums."""

from enum import StrEnum


class PredictionType(StrEnum):
    FAILURE_WITHIN_24H = "FAILURE_WITHIN_24H"
    FAILURE_WITHIN_7D = "FAILURE_WITHIN_7D"
    DEGRADATION_TREND = "DEGRADATION_TREND"


class MaintenanceType(StrEnum):
    PREVENTIVE = "PREVENTIVE"
    CORRECTIVE = "CORRECTIVE"
    PREDICTIVE = "PREDICTIVE"
    EMERGENCY = "EMERGENCY"


class MaintenanceStatus(StrEnum):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

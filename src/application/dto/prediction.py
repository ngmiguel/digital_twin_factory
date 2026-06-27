"""Prediction and maintenance DTOs."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.domain.prediction.enums import MaintenanceStatus, MaintenanceType, PredictionType


class PredictionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    machine_id: UUID
    prediction_type: PredictionType
    confidence: float
    features: dict[str, Any]
    predicted_at: datetime
    valid_until: datetime
    created_at: datetime


class PredictionListResponse(BaseModel):
    predictions: list[PredictionResponse]
    total: int
    page: int
    size: int


class MaintenanceResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    machine_id: UUID
    prediction_id: UUID | None
    assigned_to: UUID | None
    maintenance_type: MaintenanceType
    status: MaintenanceStatus
    description: str
    scheduled_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class MaintenanceListResponse(BaseModel):
    items: list[MaintenanceResponse]
    total: int
    page: int
    size: int


class CreateMaintenanceRequest(BaseModel):
    machine_id: UUID
    maintenance_type: MaintenanceType = MaintenanceType.PREDICTIVE
    description: str = Field(min_length=1, max_length=500)
    assigned_to: UUID | None = None
    scheduled_at: datetime | None = None
    prediction_id: UUID | None = None

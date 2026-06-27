"""Monitoring DTOs."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.domain.monitoring.enums import AlertSeverity, AlertType


class AlertResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    machine_id: UUID
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    metadata: dict[str, Any]
    is_acknowledged: bool
    acknowledged_by: UUID | None
    acknowledged_at: datetime | None
    is_resolved: bool
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AlertListResponse(BaseModel):
    items: list[AlertResponse]
    total: int
    page: int
    size: int


class ResolveAlertRequest(BaseModel):
    resolution: str = Field(min_length=1, max_length=500)

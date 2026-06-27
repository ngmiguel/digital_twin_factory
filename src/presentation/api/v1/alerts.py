"""Alert API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.application.dto.monitoring import AlertListResponse, AlertResponse, ResolveAlertRequest
from src.application.handlers.monitoring.alert_service import AlertService
from src.presentation.dependencies.auth import CurrentUser, require_permission
from src.presentation.dependencies.monitoring import get_alert_service

router = APIRouter()


@router.get("/alerts", response_model=AlertListResponse)
async def list_alerts(
    user: Annotated[CurrentUser, Depends(require_permission("alert:read"))],
    service: Annotated[AlertService, Depends(get_alert_service)],
    severity: str | None = Query(default=None),
    machine_id: UUID | None = Query(default=None),
    is_resolved: bool | None = Query(default=None),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> AlertListResponse:
    return await service.list_alerts(
        user.tenant_id,
        severity=severity,
        machine_id=machine_id,
        is_resolved=is_resolved,
        status=status,
        page=page,
        size=size,
    )


@router.patch("/alerts/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: UUID,
    user: Annotated[CurrentUser, Depends(require_permission("alert:write"))],
    service: Annotated[AlertService, Depends(get_alert_service)],
) -> AlertResponse:
    return await service.acknowledge_alert(user.tenant_id, alert_id, user.user_id)


@router.patch("/alerts/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: UUID,
    request: ResolveAlertRequest,
    user: Annotated[CurrentUser, Depends(require_permission("alert:write"))],
    service: Annotated[AlertService, Depends(get_alert_service)],
) -> AlertResponse:
    return await service.resolve_alert(user.tenant_id, alert_id, request)

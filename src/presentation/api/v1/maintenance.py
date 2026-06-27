"""Maintenance API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.application.dto.prediction import (
    CreateMaintenanceRequest,
    MaintenanceListResponse,
    MaintenanceResponse,
)
from src.application.handlers.prediction.maintenance_service import MaintenanceService
from src.presentation.dependencies.auth import CurrentUser, require_permission
from src.presentation.dependencies.prediction import get_maintenance_service

router = APIRouter()


@router.get("/maintenance", response_model=MaintenanceListResponse)
async def list_maintenance(
    user: Annotated[CurrentUser, Depends(require_permission("maintenance:read"))],
    service: Annotated[MaintenanceService, Depends(get_maintenance_service)],
    status: str | None = Query(default=None),
    machine_id: UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> MaintenanceListResponse:
    return await service.list_maintenance(
        user.tenant_id,
        status=status,
        machine_id=machine_id,
        page=page,
        size=size,
    )


@router.post("/maintenance", response_model=MaintenanceResponse, status_code=status.HTTP_201_CREATED)
async def create_maintenance(
    request: CreateMaintenanceRequest,
    user: Annotated[CurrentUser, Depends(require_permission("maintenance:write"))],
    service: Annotated[MaintenanceService, Depends(get_maintenance_service)],
) -> MaintenanceResponse:
    return await service.create_maintenance(user.tenant_id, request)


@router.patch("/maintenance/{maintenance_id}/start", response_model=MaintenanceResponse)
async def start_maintenance(
    maintenance_id: UUID,
    user: Annotated[CurrentUser, Depends(require_permission("maintenance:write"))],
    service: Annotated[MaintenanceService, Depends(get_maintenance_service)],
) -> MaintenanceResponse:
    return await service.start_maintenance(user.tenant_id, maintenance_id)


@router.patch("/maintenance/{maintenance_id}/complete", response_model=MaintenanceResponse)
async def complete_maintenance(
    maintenance_id: UUID,
    user: Annotated[CurrentUser, Depends(require_permission("maintenance:write"))],
    service: Annotated[MaintenanceService, Depends(get_maintenance_service)],
) -> MaintenanceResponse:
    return await service.complete_maintenance(user.tenant_id, maintenance_id)

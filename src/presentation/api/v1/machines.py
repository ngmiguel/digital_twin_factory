"""Machine API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.application.dto.factory import (
    CreateMachineRequest,
    MachineListResponse,
    MachineResponse,
    UpdateMachineRequest,
)
from src.application.handlers.factory.factory_service import FactoryService
from src.presentation.dependencies.auth import CurrentUser, require_permission
from src.presentation.dependencies.factory import get_factory_service

router = APIRouter()


@router.get("/machines", response_model=MachineListResponse)
async def list_machines(
    user: Annotated[CurrentUser, Depends(require_permission("machine:read"))],
    service: Annotated[FactoryService, Depends(get_factory_service)],
    factory_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    machine_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> MachineListResponse:
    return await service.list_machines(
        user.tenant_id,
        factory_id=factory_id,
        status=status,
        machine_type=machine_type,
        page=page,
        size=size,
    )


@router.post("/machines", response_model=MachineResponse, status_code=status.HTTP_201_CREATED)
async def create_machine(
    request: CreateMachineRequest,
    user: Annotated[CurrentUser, Depends(require_permission("machine:write"))],
    service: Annotated[FactoryService, Depends(get_factory_service)],
) -> MachineResponse:
    return await service.create_machine(user.tenant_id, request)


@router.get("/machines/{machine_id}", response_model=MachineResponse)
async def get_machine(
    machine_id: UUID,
    user: Annotated[CurrentUser, Depends(require_permission("machine:read"))],
    service: Annotated[FactoryService, Depends(get_factory_service)],
) -> MachineResponse:
    return await service.get_machine(user.tenant_id, machine_id)


@router.put("/machines/{machine_id}", response_model=MachineResponse)
async def update_machine(
    machine_id: UUID,
    request: UpdateMachineRequest,
    user: Annotated[CurrentUser, Depends(require_permission("machine:write"))],
    service: Annotated[FactoryService, Depends(get_factory_service)],
) -> MachineResponse:
    return await service.update_machine(user.tenant_id, machine_id, request)


@router.delete("/machines/{machine_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_machine(
    machine_id: UUID,
    user: Annotated[CurrentUser, Depends(require_permission("machine:delete"))],
    service: Annotated[FactoryService, Depends(get_factory_service)],
) -> None:
    await service.delete_machine(user.tenant_id, machine_id)


@router.post("/machines/{machine_id}/start", response_model=MachineResponse)
async def start_machine(
    machine_id: UUID,
    user: Annotated[CurrentUser, Depends(require_permission("machine:start"))],
    service: Annotated[FactoryService, Depends(get_factory_service)],
) -> MachineResponse:
    return await service.start_machine(user.tenant_id, machine_id)


@router.post("/machines/{machine_id}/stop", response_model=MachineResponse)
async def stop_machine(
    machine_id: UUID,
    user: Annotated[CurrentUser, Depends(require_permission("machine:stop"))],
    service: Annotated[FactoryService, Depends(get_factory_service)],
) -> MachineResponse:
    return await service.stop_machine(user.tenant_id, machine_id)

"""Factory and production line API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.application.dto.factory import (
    CreateFactoryRequest,
    CreateProductionLineRequest,
    FactoryListResponse,
    FactoryResponse,
    ProductionLineResponse,
    UpdateFactoryRequest,
)
from src.application.handlers.factory.factory_service import FactoryService
from src.presentation.dependencies.auth import CurrentUser, require_permission
from src.presentation.dependencies.factory import get_factory_service

router = APIRouter()


@router.get("/factories", response_model=FactoryListResponse)
async def list_factories(
    user: Annotated[CurrentUser, Depends(require_permission("factory:read"))],
    service: Annotated[FactoryService, Depends(get_factory_service)],
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> FactoryListResponse:
    return await service.list_factories(user.tenant_id, status=status, page=page, size=size)


@router.post("/factories", response_model=FactoryResponse, status_code=status.HTTP_201_CREATED)
async def create_factory(
    request: CreateFactoryRequest,
    user: Annotated[CurrentUser, Depends(require_permission("factory:write"))],
    service: Annotated[FactoryService, Depends(get_factory_service)],
) -> FactoryResponse:
    return await service.create_factory(user.tenant_id, request)


@router.get("/factories/{factory_id}", response_model=FactoryResponse)
async def get_factory(
    factory_id: UUID,
    user: Annotated[CurrentUser, Depends(require_permission("factory:read"))],
    service: Annotated[FactoryService, Depends(get_factory_service)],
) -> FactoryResponse:
    return await service.get_factory(user.tenant_id, factory_id)


@router.put("/factories/{factory_id}", response_model=FactoryResponse)
async def update_factory(
    factory_id: UUID,
    request: UpdateFactoryRequest,
    user: Annotated[CurrentUser, Depends(require_permission("factory:write"))],
    service: Annotated[FactoryService, Depends(get_factory_service)],
) -> FactoryResponse:
    return await service.update_factory(user.tenant_id, factory_id, request)


@router.delete("/factories/{factory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_factory(
    factory_id: UUID,
    user: Annotated[CurrentUser, Depends(require_permission("factory:delete"))],
    service: Annotated[FactoryService, Depends(get_factory_service)],
) -> None:
    await service.delete_factory(user.tenant_id, factory_id)


@router.get("/factories/{factory_id}/lines", response_model=list[ProductionLineResponse])
async def list_production_lines(
    factory_id: UUID,
    user: Annotated[CurrentUser, Depends(require_permission("factory:read"))],
    service: Annotated[FactoryService, Depends(get_factory_service)],
) -> list[ProductionLineResponse]:
    return await service.list_production_lines(user.tenant_id, factory_id)


@router.post(
    "/factories/{factory_id}/lines",
    response_model=ProductionLineResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_production_line(
    factory_id: UUID,
    request: CreateProductionLineRequest,
    user: Annotated[CurrentUser, Depends(require_permission("factory:write"))],
    service: Annotated[FactoryService, Depends(get_factory_service)],
) -> ProductionLineResponse:
    return await service.create_production_line(user.tenant_id, factory_id, request)

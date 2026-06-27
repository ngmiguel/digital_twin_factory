"""Factory management DTOs."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.domain.factory.enums import FactoryStatus, MachineStatus, MachineType, ProductionLineStatus


class CreateFactoryRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    config: dict[str, Any] = Field(default_factory=dict)


class UpdateFactoryRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    status: FactoryStatus | None = None
    config: dict[str, Any] | None = None


class FactoryResponse(BaseModel):
    id: UUID
    name: str
    location: str | None
    status: FactoryStatus
    config: dict[str, Any]
    machine_count: int = 0
    active_alerts: int = 0
    created_at: datetime
    updated_at: datetime


class FactoryListResponse(BaseModel):
    items: list[FactoryResponse]
    total: int
    page: int
    size: int


class CreateProductionLineRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    capacity: int = Field(gt=0)


class ProductionLineResponse(BaseModel):
    id: UUID
    factory_id: UUID
    name: str
    capacity: int
    status: ProductionLineStatus
    created_at: datetime
    updated_at: datetime


class CreateMachineRequest(BaseModel):
    production_line_id: UUID
    name: str = Field(min_length=1, max_length=255)
    machine_type: MachineType
    failure_rate: float = Field(default=0.001, ge=0, le=1)
    nominal_production_rate: float = Field(default=100.0, gt=0)
    simulation_config: dict[str, Any] | None = None


class UpdateMachineRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    failure_rate: float | None = Field(default=None, ge=0, le=1)
    nominal_production_rate: float | None = Field(default=None, gt=0)
    simulation_config: dict[str, Any] | None = None


class MachineResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    production_line_id: UUID
    name: str
    machine_type: MachineType
    status: MachineStatus
    simulation_config: dict[str, Any]
    failure_rate: float
    nominal_production_rate: float
    created_at: datetime
    updated_at: datetime


class MachineListResponse(BaseModel):
    items: list[MachineResponse]
    total: int
    page: int
    size: int

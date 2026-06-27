"""API v1 router aggregation."""

from fastapi import APIRouter

from src.presentation.api.v1.alerts import router as alerts_router
from src.presentation.api.v1.auth import router as auth_router
from src.presentation.api.v1.factories import router as factories_router
from src.presentation.api.v1.health import router as health_router
from src.presentation.api.v1.maintenance import router as maintenance_router
from src.presentation.api.v1.machines import router as machines_router
from src.presentation.api.v1.notifications import router as notifications_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(factories_router, tags=["Factories"])
api_v1_router.include_router(machines_router, tags=["Machines"])
api_v1_router.include_router(alerts_router, tags=["Alerts"])
api_v1_router.include_router(maintenance_router, tags=["Maintenance"])
api_v1_router.include_router(notifications_router, tags=["Notifications"])

# Health endpoints remain at root level (see main.py)
health_router_root = health_router

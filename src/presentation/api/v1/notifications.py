"""Notification API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.application.dto.notification import NotificationListResponse, NotificationResponse
from src.application.handlers.notification.notification_service import NotificationService
from src.presentation.dependencies.auth import CurrentUser, require_permission
from src.presentation.dependencies.notification import get_notification_service

router = APIRouter()


@router.get("/notifications", response_model=NotificationListResponse)
async def list_notifications(
    user: Annotated[CurrentUser, Depends(require_permission("notification:read"))],
    service: Annotated[NotificationService, Depends(get_notification_service)],
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> NotificationListResponse:
    return await service.list_notifications(
        user.tenant_id,
        user.user_id,
        status=status,
        page=page,
        size=size,
    )


@router.patch("/notifications/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: UUID,
    user: Annotated[CurrentUser, Depends(require_permission("notification:read"))],
    service: Annotated[NotificationService, Depends(get_notification_service)],
) -> NotificationResponse:
    return await service.mark_delivered(user.tenant_id, user.user_id, notification_id)

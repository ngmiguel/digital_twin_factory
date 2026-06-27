"""WebSocket route definitions."""

from uuid import UUID

from fastapi import APIRouter, Query, WebSocket

from src.presentation.websocket.handlers import (
    handle_factory_websocket,
    handle_machine_websocket,
    handle_notifications_websocket,
)

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/factory/{factory_id}")
async def factory_metrics_stream(
    websocket: WebSocket,
    factory_id: UUID,
    token: str = Query(..., description="JWT access token"),
) -> None:
    await handle_factory_websocket(websocket, factory_id, token)


@router.websocket("/ws/machine/{machine_id}")
async def machine_metrics_stream(
    websocket: WebSocket,
    machine_id: UUID,
    token: str = Query(..., description="JWT access token"),
) -> None:
    await handle_machine_websocket(websocket, machine_id, token)


@router.websocket("/ws/notifications")
async def notifications_stream(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
) -> None:
    await handle_notifications_websocket(websocket, token)

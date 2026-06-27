"""Redis Pub/Sub bridge for WebSocket real-time streaming."""

import asyncio
import json
from datetime import UTC, datetime
from uuid import UUID

import structlog
from fastapi import WebSocket, WebSocketDisconnect
from redis.asyncio import Redis

from src.domain.shared.exceptions import AuthenticationError, EntityNotFoundError, PermissionDeniedError
from src.infrastructure.cache.redis_client import _redis_client
from src.infrastructure.messaging.redis_channels import factory_alerts_channel, factory_metrics_channel
from src.infrastructure.persistence.repositories.factory_repository import FactoryRepository
from src.infrastructure.persistence.repositories.machine_repository import MachineRepository
from src.infrastructure.persistence.database import _session_factory
from src.presentation.websocket.auth import authenticate_websocket, parse_machine_filter
from src.presentation.websocket.connection_manager import factory_connection_manager

logger = structlog.get_logger()
_HEARTBEAT_INTERVAL = 30


async def _verify_factory_access(tenant_id: UUID, factory_id: UUID) -> None:
    if _session_factory is None:
        raise RuntimeError("Database not initialized")
    async with _session_factory() as session:
        repo = FactoryRepository(session)
        factory = await repo.get_by_id(factory_id, tenant_id)
        if factory is None:
            raise EntityNotFoundError("Factory", factory_id)


async def _verify_machine_access(tenant_id: UUID, machine_id: UUID) -> UUID:
    if _session_factory is None:
        raise RuntimeError("Database not initialized")
    async with _session_factory() as session:
        machine_repo = MachineRepository(session)
        machine = await machine_repo.get_by_id(machine_id, tenant_id)
        if machine is None:
            raise EntityNotFoundError("Machine", machine_id)
        factory_id = await machine_repo.get_factory_id(machine_id, tenant_id)
        if factory_id is None:
            raise EntityNotFoundError("Machine", machine_id)
        return factory_id


async def _stream_redis_channel(
    websocket: WebSocket,
    redis: Redis,
    channel: str,
    machine_filter: UUID | None = None,
    include_alerts: bool = False,
    tenant_id: UUID | None = None,
    factory_id: UUID | None = None,
) -> None:
    pubsub = redis.pubsub()
    channels = [channel]
    if include_alerts and tenant_id and factory_id:
        channels.append(factory_alerts_channel(tenant_id, factory_id))

    await pubsub.subscribe(*channels)

    async def heartbeat() -> None:
        while True:
            await asyncio.sleep(_HEARTBEAT_INTERVAL)
            await websocket.send_text(
                json.dumps({"type": "ping", "timestamp": datetime.now(UTC).isoformat()})
            )

    heartbeat_task = asyncio.create_task(heartbeat())

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message.get("type") == "message":
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode()
                if machine_filter is not None and not parse_machine_filter(data, machine_filter):
                    continue
                await websocket.send_text(data)

            try:
                client_msg = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                parsed = json.loads(client_msg)
                if parsed.get("type") == "pong":
                    continue
            except asyncio.TimeoutError:
                pass
            except json.JSONDecodeError:
                pass
    finally:
        heartbeat_task.cancel()
        await pubsub.unsubscribe(*channels)
        await pubsub.close()


async def handle_factory_websocket(websocket: WebSocket, factory_id: UUID, token: str) -> None:
    if _redis_client is None:
        await websocket.close(code=1011, reason="Redis not available")
        return

    try:
        user = authenticate_websocket(token, "factory:read")
        await _verify_factory_access(user.tenant_id, factory_id)
    except (AuthenticationError, PermissionDeniedError):
        await websocket.close(code=1008, reason="Unauthorized")
        return
    except EntityNotFoundError:
        await websocket.close(code=1008, reason="Factory not found")
        return

    await factory_connection_manager.connect(user.tenant_id, factory_id, websocket)
    channel = factory_metrics_channel(user.tenant_id, factory_id)

    logger.info(
        "websocket.connected",
        factory_id=str(factory_id),
        tenant_id=str(user.tenant_id),
        connections=factory_connection_manager.count(user.tenant_id, factory_id),
    )

    try:
        await _stream_redis_channel(
            websocket,
            _redis_client,
            channel,
            include_alerts=True,
            tenant_id=user.tenant_id,
            factory_id=factory_id,
        )
    except WebSocketDisconnect:
        pass
    finally:
        factory_connection_manager.disconnect(user.tenant_id, factory_id, websocket)
        logger.info("websocket.disconnected", factory_id=str(factory_id))


async def handle_machine_websocket(websocket: WebSocket, machine_id: UUID, token: str) -> None:
    if _redis_client is None:
        await websocket.close(code=1011, reason="Redis not available")
        return

    try:
        user = authenticate_websocket(token, "machine:read")
        factory_id = await _verify_machine_access(user.tenant_id, machine_id)
    except (AuthenticationError, PermissionDeniedError):
        await websocket.close(code=1008, reason="Unauthorized")
        return
    except EntityNotFoundError:
        await websocket.close(code=1008, reason="Machine not found")
        return

    await factory_connection_manager.connect(user.tenant_id, factory_id, websocket)
    channel = factory_metrics_channel(user.tenant_id, factory_id)

    logger.info(
        "websocket.connected",
        machine_id=str(machine_id),
        factory_id=str(factory_id),
        tenant_id=str(user.tenant_id),
    )

    try:
        await _stream_redis_channel(
            websocket,
            _redis_client,
            channel,
            machine_filter=machine_id,
        )
    except WebSocketDisconnect:
        pass
    finally:
        factory_connection_manager.disconnect(user.tenant_id, factory_id, websocket)
        logger.info("websocket.disconnected", machine_id=str(machine_id))

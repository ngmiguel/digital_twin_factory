"""Unit tests for Redis channel naming."""

from uuid import uuid4

from src.infrastructure.messaging.redis_channels import (
    factory_alerts_channel,
    factory_metrics_channel,
    machine_status_channel,
    user_notifications_channel,
)


def test_factory_metrics_channel_format() -> None:
    tenant_id = uuid4()
    factory_id = uuid4()
    channel = factory_metrics_channel(tenant_id, factory_id)
    assert channel == f"tenant:{tenant_id}:factory:{factory_id}:metrics"


def test_factory_alerts_channel_format() -> None:
    tenant_id = uuid4()
    factory_id = uuid4()
    channel = factory_alerts_channel(tenant_id, factory_id)
    assert "alerts" in channel


def test_machine_status_channel_format() -> None:
    tenant_id = uuid4()
    machine_id = uuid4()
    channel = machine_status_channel(tenant_id, machine_id)
    assert str(machine_id) in channel


def test_user_notifications_channel_format() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    channel = user_notifications_channel(tenant_id, user_id)
    assert channel == f"tenant:{tenant_id}:user:{user_id}:notifications"

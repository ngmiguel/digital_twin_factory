"""Redis Pub/Sub channel naming conventions."""

from uuid import UUID


def factory_metrics_channel(tenant_id: UUID, factory_id: UUID) -> str:
    return f"tenant:{tenant_id}:factory:{factory_id}:metrics"


def factory_alerts_channel(tenant_id: UUID, factory_id: UUID) -> str:
    return f"tenant:{tenant_id}:factory:{factory_id}:alerts"


def machine_status_channel(tenant_id: UUID, machine_id: UUID) -> str:
    return f"tenant:{tenant_id}:machine:{machine_id}:status"

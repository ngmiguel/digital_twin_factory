# ADR-002 — Event-Driven Architecture avec Redis

**Statut :** Accepté  
**Date :** 2025-06-27

## Contexte

Le dashboard temps réel nécessite une latence < 100ms entre la génération d'une métrique et son affichage. La simulation tourne en background (Celery) tandis que les clients WebSocket doivent recevoir les updates en push.

## Décision

Utiliser **Redis Pub/Sub** comme bus d'événements temps réel, avec persistance PostgreSQL en parallèle (write-through).

### Channels Redis

| Channel | Publisher | Subscriber |
|---------|-----------|------------|
| `factory:{factory_id}:metrics` | Simulation Service | WebSocket API |
| `factory:{factory_id}:alerts` | Monitoring Service | WebSocket API, Notification |
| `machine:{machine_id}:status` | Simulation Service | Monitoring Service |
| `tenant:{tenant_id}:events` | Tous services | Audit Service (futur) |

### Domain Events (in-process)

Pour les opérations synchrones (CRUD), les domain events sont dispatchés in-process via un event bus léger avant évolution vers un message broker dédié (RabbitMQ/Kafka en phase 3).

```python
# Exemple conceptuel — pas de code implémenté encore
class DomainEvent:
    occurred_at: datetime
    aggregate_id: UUID
    tenant_id: UUID

class AlertRaised(DomainEvent):
    machine_id: UUID
    severity: AlertSeverity
    alert_type: AlertType
    message: str
```

## Conséquences

- Redis est single point pour le temps réel — mitigé par Redis Sentinel en production
- Pub/Sub ne garantit pas la persistence — les events critiques sont aussi persistés en DB
- Celery utilise le même Redis comme broker (séparation par DB index)

## Alternatives rejetées

| Alternative | Raison |
|-------------|--------|
| Polling REST | Latence inacceptable |
| Kafka | Over-engineering pour phase 1 |
| WebSocket direct Celery→Client | Pas de fan-out multi-clients |

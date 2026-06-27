# ADR-004 — CQRS Strategy (Partiel)

**Statut :** Accepté  
**Date :** 2025-06-27

## Contexte

Les lectures (dashboard métriques, historique) et les écritures (création machine, alertes) ont des patterns de charge différents. Le dashboard peut lire des milliers de métriques/seconde via WebSocket tandis que les écritures CRUD sont rares.

## Décision

Adopter **CQRS partiel** — pas de stores séparés, mais séparation explicite Commands/Queries dans `application/`.

### Commands (Write)

| Command | Handler | Aggregate |
|---------|---------|-----------|
| `CreateFactoryCommand` | `CreateFactoryHandler` | Factory |
| `ProvisionMachineCommand` | `ProvisionMachineHandler` | Machine |
| `AcknowledgeAlertCommand` | `AcknowledgeAlertHandler` | Alert |
| `ScheduleMaintenanceCommand` | `ScheduleMaintenanceHandler` | MaintenanceRecord |

### Queries (Read)

| Query | Handler | Source |
|-------|---------|--------|
| `GetFactoryByIdQuery` | `GetFactoryHandler` | PostgreSQL |
| `ListMachinesQuery` | `ListMachinesHandler` | PostgreSQL |
| `GetMachineMetricsQuery` | `GetMetricsHandler` | PostgreSQL + Redis cache |
| `GetActiveAlertsQuery` | `GetAlertsHandler` | PostgreSQL |
| `GetLatestMetricQuery` | `GetLatestMetricHandler` | Redis cache |

### Temps réel (hors CQRS)

Les métriques live passent par Redis Pub/Sub → WebSocket, pas par des Query handlers.

## Conséquences

- Code application clair : `commands/` vs `queries/`
- Pas de complexité d'un event store complet
- Évolution possible vers read models dédiés (TimescaleDB pour métriques)

## Alternatives rejetées

| Alternative | Raison |
|-------------|--------|
| CQRS complet + Event Sourcing | Over-engineering phase 1 |
| Pas de CQRS | Mélange read/write dans les services |

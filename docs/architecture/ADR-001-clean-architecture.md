# ADR-001 — Clean Architecture + DDD

**Statut :** Accepté  
**Date :** 2025-06-27  
**Décideurs :** Architecture Team

## Contexte

Digital Twin Factory est un système complexe avec simulation temps réel, multi-tenancy, RBAC et maintenance prédictive. Une architecture en couches est nécessaire pour maintenir la testabilité et permettre l'évolution vers des microservices.

## Décision

Adopter **Clean Architecture** avec 4 couches et **Domain-Driven Design** pour modéliser le métier industriel.

### Couches

```
src/
├── domain/
│   ├── identity/       # User, Role, Tenant aggregates
│   ├── factory/        # Factory, Machine, ProductionLine aggregates
│   ├── simulation/     # VirtualMachine, Metric, FailureModel
│   ├── monitoring/     # Alert, MetricSnapshot
│   └── prediction/     # Prediction, MaintenanceRecord
├── application/
│   ├── commands/       # Write operations (CQRS)
│   ├── queries/        # Read operations (CQRS)
│   ├── handlers/       # Command/Query handlers
│   └── dto/            # Data Transfer Objects
├── infrastructure/
│   ├── persistence/    # SQLAlchemy repositories, UoW
│   ├── messaging/      # Redis pub/sub, event bus
│   ├── cache/          # Redis cache layer
│   └── tasks/          # Celery task definitions
└── presentation/
    ├── api/v1/         # REST routers
    ├── websocket/      # WebSocket handlers
    └── middleware/     # Auth, tenant, logging
```

### Patterns appliqués

| Pattern | Usage |
|---------|-------|
| Repository | Abstraction accès données |
| Unit of Work | Transactions atomiques |
| Aggregate Root | Factory, Machine, User |
| Domain Event | FactoryCreated, AlertRaised |
| Value Object | Temperature, Vibration, Email |
| Factory Method | Création machines virtuelles |

## Conséquences

**Positives :**
- Domaine testable sans infrastructure
- Évolution microservices facilitée (extraire un bounded context = extraire un service)
- Recruteurs reconnaissent immédiatement la structure

**Négatives :**
- Plus de fichiers qu'une architecture MVC simple
- Courbe d'apprentissage pour les nouveaux contributeurs

## Alternatives rejetées

| Alternative | Raison du rejet |
|-------------|-----------------|
| MVC simple | Pas scalable pour multi-tenancy + events |
| Hexagonal seul | DDD ajoute la modélisation métier explicite |
| Microservices dès le départ | Complexité opérationnelle prématurée |

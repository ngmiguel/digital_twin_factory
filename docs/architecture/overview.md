# Architecture Overview — Digital Twin Factory

## Contexte système

Digital Twin Factory est une plateforme SaaS multi-tenant qui simule des usines industrielles en temps réel. Chaque tenant peut créer des usines, provisionner des machines virtuelles et observer leur comportement via des métriques live, des alertes et des prédictions de maintenance.

## Architecture globale

```mermaid
flowchart TB
    subgraph Clients["Clients (futur)"]
        Dashboard["React Dashboard"]
        WinApp["Windows Supervision App"]
    end

    subgraph Gateway["API Gateway"]
        Traefik["Traefik / Nginx"]
    end

    subgraph Backend["Backend Python — Monorepo Phase 1"]
        direction TB
        Presentation["presentation/<br/>FastAPI + WebSocket"]
        Application["application/<br/>Use Cases + CQRS"]
        Domain["domain/<br/>Entities + Events"]
        Infrastructure["infrastructure/<br/>ORM + Redis + Celery"]
    end

    subgraph Data["Infrastructure Data"]
        PG[("PostgreSQL 16")]
        Redis[("Redis 7")]
        Celery["Celery Workers"]
    end

    Dashboard --> Traefik
    WinApp --> Traefik
    Traefik --> Presentation
    Presentation --> Application
    Application --> Domain
    Application --> Infrastructure
    Infrastructure --> PG
    Infrastructure --> Redis
    Infrastructure --> Celery
    Celery --> Redis
```

## Évolution microservices (Phase 2)

Le monorepo initial évolue vers des services déployables indépendamment :

| Service | Responsabilité | Port |
|---------|----------------|------|
| `auth-service` | JWT, RBAC, Multi-tenancy | 8001 |
| `factory-service` | Usines, lignes, machines | 8002 |
| `simulation-service` | Moteur de simulation virtuelle | 8003 |
| `monitoring-service` | Métriques, alertes, dashboard WS | 8004 |
| `prediction-service` | ML, maintenance prédictive | 8005 |
| `notification-service` | Email, webhook, in-app | 8006 |

## Clean Architecture — Règles de dépendance

```mermaid
flowchart LR
    Presentation --> Application
    Application --> Domain
    Infrastructure --> Domain
    Infrastructure --> Application
    Presentation -.-> Infrastructure
```

**Règles :**
1. `domain/` ne dépend de rien (pure Python)
2. `application/` dépend uniquement de `domain/`
3. `infrastructure/` implémente les interfaces définies dans `domain/` et `application/`
4. `presentation/` orchestre les use cases via `application/`

## Flux de données temps réel

```mermaid
sequenceDiagram
    participant Celery as Celery Worker
    participant Sim as Simulation Engine
    participant Redis as Redis Pub/Sub
    participant API as FastAPI WebSocket
    participant PG as PostgreSQL
    participant Client as Client WS

    loop Every 1s per machine
        Celery->>Sim: simulate_machine_tick(machine_id)
        Sim->>Sim: Generate temperature, vibration, power, rate
        Sim->>Redis: PUBLISH factory:{id}:metrics
        Sim->>PG: Batch insert metrics (async)
        Sim->>Sim: Check thresholds → AlertRaised?
    end

    Client->>API: WS /ws/factory/{id}?token=jwt
    API->>Redis: SUBSCRIBE factory:{id}:metrics
    Redis-->>API: metric payload
    API-->>Client: JSON metric event
```

## ADRs (Architecture Decision Records)

| ADR | Décision |
|-----|----------|
| [ADR-001](ADR-001-clean-architecture.md) | Clean Architecture + DDD |
| [ADR-002](ADR-002-event-driven-architecture.md) | Event-Driven avec Redis |
| [ADR-003](ADR-003-multi-tenancy.md) | Multi-tenancy par tenant_id + RLS |
| [ADR-004](ADR-004-cqrs-strategy.md) | CQRS partiel |
| [ADR-005](ADR-005-authentication-strategy.md) | JWT access + refresh |

## Qualité et observabilité

| Aspect | Solution |
|--------|----------|
| Logging | structlog (JSON) + correlation_id |
| Monitoring | Prometheus metrics + health checks |
| Tracing | OpenTelemetry (futur) |
| Error handling | Domain exceptions → HTTP mapping |
| API docs | OpenAPI 3.1 auto-généré FastAPI |

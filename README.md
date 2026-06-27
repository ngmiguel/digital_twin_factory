# Digital Twin Factory

> Plateforme de simulation d'usine industrielle en temps réel — Digital Twin de niveau entreprise.

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## Vision

Digital Twin Factory simule une usine intelligente complète où chaque machine est virtuelle mais se comporte comme une machine industrielle réelle. La plateforme génère des métriques en temps réel (température, vibration, consommation électrique, cadence), détecte les anomalies, prédit les pannes et notifie les opérateurs via un dashboard temps réel.

Ce projet reproduit les architectures utilisées par Siemens, Bosch et General Electric — rarement implémentées en portfolio étudiant.

## Stack technique

| Couche | Technologie |
|--------|-------------|
| Runtime | Python 3.12 |
| API | FastAPI |
| Base de données | PostgreSQL 16 |
| ORM | SQLAlchemy 2.x |
| Migrations | Alembic |
| Cache / Pub/Sub | Redis 7 |
| Tâches async | Celery |
| Temps réel | WebSockets |
| Auth | JWT (access + refresh) |
| Tests | Pytest |
| Conteneurisation | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| Déploiement futur | Kubernetes |

## Principes architecturaux

- **Clean Architecture** — séparation domain / application / infrastructure / presentation
- **DDD** — Bounded Contexts, Aggregates, Domain Events
- **SOLID** — dépendances orientées vers le domaine
- **Repository Pattern** — abstraction de la persistance
- **Unit of Work** — transactions cohérentes
- **CQRS** — séparation commandes / requêtes où pertinent
- **Event-Driven** — Redis Pub/Sub pour le temps réel
- **Multi-tenancy** — isolation par tenant (Row Level Security)

## Structure cible du code

```
src/
├── domain/           # Entités, Value Objects, Domain Events, Interfaces
├── application/      # Use Cases, Commands, Queries, Handlers (CQRS)
├── infrastructure/   # Repositories, ORM, Redis, Celery, External APIs
└── presentation/     # FastAPI routers, WebSocket, Middleware
```

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture Overview](docs/architecture/overview.md) | Vue d'ensemble système |
| [Bounded Contexts](docs/architecture/bounded-contexts.md) | Contextes DDD |
| [Event Storming](docs/architecture/event-storming.md) | Domain Events |
| [Database Schema](docs/database/schema.md) | Modèle relationnel |
| [Use Cases](docs/api/use-cases.md) | Cas d'utilisation |
| [REST API](docs/api/rest-api-spec.md) | Spécification API |
| [WebSocket](docs/infrastructure/websocket-architecture.md) | Temps réel |
| [Redis Strategy](docs/infrastructure/redis-strategy.md) | Cache & Pub/Sub |
| [Celery Tasks](docs/infrastructure/celery-tasks.md) | Tâches background |
| [Security](docs/security/security-strategy.md) | Stratégie sécurité |
| [RBAC](docs/security/rbac.md) | Contrôle d'accès |
| [Testing](docs/testing/testing-strategy.md) | Stratégie de tests |
| [CI/CD](docs/deployment/github-actions.md) | Pipeline GitHub Actions |

## Roadmap des commits

| # | Commit | Statut |
|---|--------|--------|
| 1 | `docs: add project vision and enterprise architecture` | En cours |
| 2 | `docs: define bounded contexts and domain model` | Planifié |
| 3 | `docs: add database schema and use cases` | Planifié |
| 4 | `chore: initialize project structure and dependencies` | Planifié |
| 5 | `feat(auth): implement JWT authentication service` | Planifié |
| 6 | `feat(factory): implement factory and machine management` | Planifié |
| 7 | `feat(simulation): implement virtual machine engine` | Planifié |
| 8 | `feat(realtime): add WebSocket and Redis pub/sub` | Planifié |
| 9 | `feat(monitoring): add metrics, alerts and logging` | Planifié |
| 10 | `feat(prediction): add Celery tasks for predictive maintenance` | Planifié |
| 11 | `feat(notification): add alert notification service` | Planifié |
| 12 | `test: add unit, integration and e2e tests` | Planifié |
| 13 | `ci: add GitHub Actions pipeline` | Planifié |

## Auteur

Miguel — Portfolio professionnel

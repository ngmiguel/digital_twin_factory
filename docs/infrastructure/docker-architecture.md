# Docker Architecture — Digital Twin Factory

## Services Docker Compose

```mermaid
flowchart TB
    subgraph App["Application Layer"]
        API["api<br/>FastAPI<br/>:8000"]
        WS["websocket<br/>FastAPI WS<br/>:8001"]
    end

    subgraph Workers["Celery Workers"]
        SimW["simulation-worker"]
        MonW["monitoring-worker"]
        PredW["prediction-worker"]
        NotifW["notification-worker"]
        Beat["celery-beat"]
    end

    subgraph Data["Data Layer"]
        PG[("postgres<br/>:5432")]
        Redis[("redis<br/>:6379")]
    end

    subgraph Tools["Dev Tools"]
        Flower["flower<br/>:5555"]
        Adminer["adminer<br/>:8080"]
    end

    API --> PG
    API --> Redis
    WS --> Redis
    SimW --> PG
    SimW --> Redis
    MonW --> PG
    PredW --> PG
    NotifW --> Redis
    Beat --> Redis
    Flower --> Redis
    Adminer --> PG
```

## Structure docker/

```
docker/
├── api/
│   └── Dockerfile
├── worker/
│   └── Dockerfile          # Shared worker image
├── postgres/
│   └── init.sql            # Extensions, RLS setup
└── redis/
    └── redis.conf
```

## docker-compose.yml (aperçu)

```yaml
services:
  api:
    build: { context: ., dockerfile: docker/api/Dockerfile }
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql+asyncpg://dtf:dtf@postgres:5432/digital_twin_factory
      - REDIS_URL=redis://redis:6379/0
    depends_on: [postgres, redis]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s

  simulation-worker:
    build: { context: ., dockerfile: docker/worker/Dockerfile }
    command: celery -A src.infrastructure.tasks worker -Q simulation -c 4
    depends_on: [postgres, redis]

  celery-beat:
    build: { context: ., dockerfile: docker/worker/Dockerfile }
    command: celery -A src.infrastructure.tasks beat

  postgres:
    image: postgres:16-alpine
    volumes: [postgres_data:/var/lib/postgresql/data]
    environment:
      POSTGRES_DB: digital_twin_factory
      POSTGRES_USER: dtf
      POSTGRES_PASSWORD: dtf

  redis:
    image: redis:7-alpine
    command: redis-server /usr/local/etc/redis/redis.conf
    volumes: [./docker/redis/redis.conf:/usr/local/etc/redis/redis.conf]

volumes:
  postgres_data:
```

## Multi-stage Dockerfile (API)

```dockerfile
# Stage 1: Builder
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir build && pip wheel --no-cache-dir -w /wheels -e .

# Stage 2: Runtime
FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels
COPY src/ src/
COPY alembic/ alembic/
USER nobody
EXPOSE 8000
CMD ["uvicorn", "src.presentation.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Environnements

| Env | Compose file | Services |
|-----|--------------|----------|
| Development | `docker-compose.yml` | All + Flower + Adminer |
| CI | `docker-compose.ci.yml` | postgres + redis only |
| Production | `docker-compose.prod.yml` | All sans dev tools |

## Variables d'environnement

```bash
# .env.example
DATABASE_URL=postgresql+asyncpg://dtf:dtf@localhost:5432/digital_twin_factory
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=change-me-in-production
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
CELERY_BROKER_URL=redis://localhost:6379/2
CELERY_RESULT_BACKEND=redis://localhost:6379/3
LOG_LEVEL=INFO
ENVIRONMENT=development
```

## Health checks

| Service | Endpoint / Command | Interval |
|---------|-------------------|----------|
| API | `GET /health` | 30s |
| PostgreSQL | `pg_isready` | 10s |
| Redis | `redis-cli ping` | 10s |
| Celery | Flower `/api/workers` | 60s |

## Sécurité containers

- Non-root user (`nobody`) dans tous les images
- Pas de secrets dans les images (env vars uniquement)
- Network isolation : workers n'exposent pas de ports
- Read-only root filesystem (production)

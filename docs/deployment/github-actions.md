# GitHub Actions CI/CD Pipeline

## Workflow overview

```mermaid
flowchart LR
    Push[Push / PR] --> Lint
    Push --> TestUnit
    Push --> Security

    Lint --> TestIntegration
    TestUnit --> TestIntegration
    Security --> TestIntegration

    TestIntegration --> TestE2E
    TestE2E --> Build
    Build --> Deploy

    Deploy -->|main branch only| Staging
```

## Fichier `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: "3.12"

jobs:
  lint:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: pip
      - run: pip install ruff mypy
      - run: ruff check src/ tests/
      - run: ruff format --check src/ tests/
      - run: mypy src/

  test-unit:
    name: Unit Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: pip
      - run: pip install -e ".[test]"
      - run: pytest tests/unit/ -v --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v4
        with:
          file: coverage.xml

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - run: pip install bandit pip-audit
      - run: bandit -r src/ -ll
      - run: pip-audit

  test-integration:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: [lint, test-unit, security]
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: digital_twin_factory_test
          POSTGRES_USER: dtf
          POSTGRES_PASSWORD: dtf
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports: ["6379:6379"]
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: pip
      - run: pip install -e ".[test]"
      - run: alembic upgrade head
        env:
          DATABASE_URL: postgresql+asyncpg://dtf:dtf@localhost:5432/digital_twin_factory_test
      - run: pytest tests/integration/ -v
        env:
          DATABASE_URL: postgresql+asyncpg://dtf:dtf@localhost:5432/digital_twin_factory_test
          REDIS_URL: redis://localhost:6379/0
          JWT_SECRET_KEY: test-secret-key

  test-e2e:
    name: E2E Tests
    runs-on: ubuntu-latest
    needs: test-integration
    steps:
      - uses: actions/checkout@v4
      - run: docker compose -f docker-compose.ci.yml up -d --wait
      - run: pip install -e ".[test]"
      - run: pytest tests/e2e/ -v --timeout=120
      - run: docker compose -f docker-compose.ci.yml down

  build:
    name: Build Docker Images
    runs-on: ubuntu-latest
    needs: test-e2e
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/build-push-action@v5
        with:
          context: .
          file: docker/api/Dockerfile
          push: false
          tags: digital-twin-factory-api:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

## Branch protection rules (GitHub)

Configurer sur `main` :
- Require PR before merging
- Require status checks : lint, test-unit, security, test-integration
- Require branches to be up to date
- No force push

## Commit message convention

Enforced via commitlint (optionnel) :

```
feat(auth): implement JWT login endpoint
fix(simulation): correct temperature degradation curve
docs(architecture): add event storming diagram
test(factory): add integration tests for CRUD
ci: add e2e test job to pipeline
```

## Release strategy

| Branch | Déploiement | Tag |
|--------|-------------|-----|
| `main` | Staging auto | — |
| Release PR | Production | `v1.x.x` semver |

## Secrets GitHub requis (futur deploy)

| Secret | Usage |
|--------|-------|
| `DOCKER_REGISTRY_TOKEN` | Push images |
| `KUBE_CONFIG` | Deploy Kubernetes |
| `JWT_SECRET_KEY` | Production secret |
| `DATABASE_URL` | Production DB |

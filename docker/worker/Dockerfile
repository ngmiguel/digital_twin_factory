FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir hatchling && \
    pip wheel --no-cache-dir --wheel-dir /wheels -e .

FROM python:3.12-slim AS runtime

WORKDIR /app

RUN groupadd -r dtf && useradd -r -g dtf dtf

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels

COPY alembic.ini ./
COPY alembic ./alembic
COPY src ./src

USER dtf

CMD ["celery", "-A", "src.infrastructure.tasks.celery_app", "worker", "--loglevel=info"]

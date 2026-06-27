"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure.cache.redis_client import close_redis, init_redis
from src.infrastructure.config.settings import get_settings
from src.infrastructure.logging.setup import setup_logging
from src.infrastructure.persistence.database import close_db, init_db
from src.presentation.api.v1.router import api_v1_router
from src.presentation.middleware.correlation_id import CorrelationIdMiddleware
from src.presentation.middleware.error_handler import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    setup_logging(settings)
    init_db(settings)
    await init_redis(settings)

    import structlog

    structlog.get_logger().info(
        "application_started",
        environment=settings.environment,
        version=settings.app_version,
    )

    yield

    await close_redis()
    await close_db()
    structlog.get_logger().info("application_stopped")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Real-time industrial Digital Twin platform",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.is_development else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(CorrelationIdMiddleware)

    register_exception_handlers(app)

    app.include_router(api_v1_router)

    return app


app = create_app()


def run() -> None:
    settings = get_settings()
    uvicorn.run(
        "src.presentation.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload and settings.is_development,
    )


if __name__ == "__main__":
    run()

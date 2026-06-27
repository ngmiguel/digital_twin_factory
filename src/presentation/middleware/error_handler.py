"""Global exception handlers — domain exceptions to HTTP responses."""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from src.domain.shared.exceptions import (
    AuthenticationError,
    ConflictError,
    DomainException,
    EntityNotFoundError,
    PermissionDeniedError,
    RateLimitError,
    TenantIsolationError,
    ValidationError,
)
from src.presentation.middleware.correlation_id import get_correlation_id

STATUS_MAP: dict[type[DomainException], int] = {
    EntityNotFoundError: 404,
    ValidationError: 400,
    PermissionDeniedError: 403,
    TenantIsolationError: 403,
    AuthenticationError: 401,
    ConflictError: 409,
    RateLimitError: 429,
}


def _error_body(
    code: str,
    message: str,
    details: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
            "correlation_id": get_correlation_id(),
        }
    }


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainException)
    async def domain_exception_handler(
        request: Request, exc: DomainException
    ) -> JSONResponse:
        status_code = STATUS_MAP.get(type(exc), 500)
        details = []
        if isinstance(exc, ValidationError) and exc.field:
            details.append({"field": exc.field, "message": exc.message})
        return JSONResponse(
            status_code=status_code,
            content=_error_body(exc.code, exc.message, details),
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            {
                "field": ".".join(str(loc) for loc in err["loc"]),
                "message": err["msg"],
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=400,
            content=_error_body("VALIDATION_ERROR", "Request validation failed", details),
        )

    @app.exception_handler(PydanticValidationError)
    async def pydantic_validation_handler(
        request: Request, exc: PydanticValidationError
    ) -> JSONResponse:
        details = [
            {
                "field": ".".join(str(loc) for loc in err["loc"]),
                "message": err["msg"],
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=400,
            content=_error_body("VALIDATION_ERROR", "Validation failed", details),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        import structlog

        structlog.get_logger().error("unhandled_exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content=_error_body("INTERNAL_ERROR", "An internal error occurred"),
        )

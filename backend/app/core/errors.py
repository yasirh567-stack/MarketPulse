"""App-wide exception types and handlers.

Goal: never leak internals (stack traces, secrets, provider error bodies) to
the client, while still logging the full detail server-side for debugging.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger("app.errors")


class ProviderUnavailableError(Exception):
    """Raised when a data provider (and all its fallbacks) fail. Callers
    translate this into a friendly, non-technical API error message."""

    def __init__(self, provider: str, detail: str = ""):
        self.provider = provider
        self.detail = detail
        super().__init__(f"{provider} unavailable: {detail}")


class InsufficientDataError(Exception):
    """Raised by ML/backtesting code when there isn't enough history to
    produce a trustworthy result — the API returns this as a clear 422
    instead of a misleadingly confident number."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ProviderUnavailableError)
    async def provider_unavailable_handler(request: Request, exc: ProviderUnavailableError):
        logger.warning("Provider unavailable: %s (%s)", exc.provider, exc.detail)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "provider_unavailable",
                "message": (
                    f"The {exc.provider} data source is temporarily unavailable. "
                    "Try demo mode or again shortly."
                ),
            },
        )

    @app.exception_handler(InsufficientDataError)
    async def insufficient_data_handler(request: Request, exc: InsufficientDataError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "insufficient_data", "message": exc.reason},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        # pydantic's error dicts can carry a raw exception instance in `ctx`
        # (e.g. from a custom @field_validator raising ValueError), which is
        # not JSON-serializable — stringify it rather than letting json.dumps
        # crash while building the very response meant to report the error.
        safe_errors = []
        for err in exc.errors():
            err = dict(err)
            if "ctx" in err and isinstance(err["ctx"], dict):
                err["ctx"] = {k: str(v) for k, v in err["ctx"].items()}
            safe_errors.append(err)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "validation_error",
                "message": "Invalid request.",
                "detail": safe_errors,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception):
        logger.exception("Unhandled server error")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_error",
                "message": "Something went wrong. Please try again.",
            },
        )

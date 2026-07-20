import logging
import traceback

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.services.capacity import CapacityExhaustedError
from app.services.generation.providers.router import AllProvidersFailedError

logger = logging.getLogger("lumina.errors")

CAPACITY_MESSAGE = (
    "Free-tier capacity for today is used up. It resets at 00:00 UTC — please "
    "try again then, or run Lumina locally with your own API keys."
)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"error": "Validation error", "details": exc.errors()},
        )

    @app.exception_handler(HTTPException)
    async def http_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail},
        )

    @app.exception_handler(CapacityExhaustedError)
    async def capacity_handler(request: Request, exc: CapacityExhaustedError):
        # 429, not 503: the service is healthy, the day's free quota is spent.
        # The `capacity` flag lets the client render the calm banner rather than
        # a generic error toast.
        logger.info("Capacity exhausted: %s", exc)
        return JSONResponse(
            status_code=429,
            content={"error": CAPACITY_MESSAGE, "capacity": True},
        )

    @app.exception_handler(AllProvidersFailedError)
    async def providers_exhausted_handler(request: Request, exc: AllProvidersFailedError):
        logger.warning("All LLM providers failed: %s", exc)
        return JSONResponse(
            status_code=503,
            content={
                "error": "All model providers are currently busy or rate-limited. "
                "Please try again in a minute."
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception):
        # Full detail goes to logs only — never echo internals to clients.
        logger.error("Unhandled exception: %s\n%s", exc, traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"},
        )

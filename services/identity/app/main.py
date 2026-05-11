import logging
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db import engine
from app.routers.auth import router as auth_router

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(sys.stdout),
)

logger: structlog.BoundLogger = structlog.get_logger(service_name=settings.SERVICE_NAME)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("identity.startup", environment=settings.ENVIRONMENT)
    yield
    await engine.dispose()
    logger.info("identity.shutdown")


app = FastAPI(
    title="Stratum Identity",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.include_router(auth_router, prefix="/api/v1")


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "healthy"})

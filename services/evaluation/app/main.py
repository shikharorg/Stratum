from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.db import engine
from app.routers.evaluation import router as evaluation_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("app.starting", service=settings.SERVICE_NAME, environment=settings.ENVIRONMENT)
    logger.info("app.started", service=settings.SERVICE_NAME)

    yield

    await engine.dispose()
    logger.info("app.shutdown", service=settings.SERVICE_NAME)


app = FastAPI(
    title="Stratum Evaluation Service",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app)

app.include_router(evaluation_router, prefix="/api/v1")


@app.get("/health", include_in_schema=False)
async def health() -> JSONResponse:
    return JSONResponse({"status": "healthy"})

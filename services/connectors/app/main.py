from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.routers.connectors import router as connectors_router
from app.routers.webhooks import router as webhooks_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("app.starting", service=settings.SERVICE_NAME, environment=settings.ENVIRONMENT)
    app.state.arq_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    logger.info("app.started", service=settings.SERVICE_NAME)

    yield

    await app.state.arq_pool.aclose()
    logger.info("app.shutdown", service=settings.SERVICE_NAME)


app = FastAPI(
    title="Stratum Connectors Service",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)

app.include_router(connectors_router, prefix="/api/v1")
app.include_router(webhooks_router, prefix="/api/v1")


@app.get("/health", include_in_schema=False)
async def health() -> JSONResponse:
    return JSONResponse({"status": "healthy"})

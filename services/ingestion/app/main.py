from contextlib import asynccontextmanager
from typing import AsyncGenerator

import redis.asyncio as aioredis
import structlog
from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from prometheus_fastapi_instrumentator import Instrumentator
import stratum_libs.pfi_compat  # noqa: F401

from app.core.config import settings
from app.dependencies import get_encoder, get_indexer, get_minio_client
from app.routers.documents import router as documents_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("app.starting", service=settings.SERVICE_NAME, environment=settings.ENVIRONMENT)

    app.state.arq_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    app.state.redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

    minio_client = get_minio_client()
    await minio_client.ensure_bucket()

    encoder = get_encoder()
    indexer = get_indexer()
    await indexer.ensure_collection(encoder)

    logger.info("app.started", service=settings.SERVICE_NAME)

    yield

    await app.state.arq_pool.aclose()
    await app.state.redis.aclose()

    logger.info("app.shutdown", service=settings.SERVICE_NAME)


app = FastAPI(
    title="Stratum Ingestion Service",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app)

app.include_router(documents_router, prefix="/api/v1")


@app.get("/health", include_in_schema=False)
async def health() -> JSONResponse:
    return JSONResponse({"status": "healthy"})

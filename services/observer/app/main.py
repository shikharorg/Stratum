from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from app.consumer import StreamConsumer
from app.core.config import settings
from app.routers.audit_logs import router as audit_logs_router
from app.routers.stream import router as stream_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("app.starting", service=settings.SERVICE_NAME, environment=settings.ENVIRONMENT)

    redis: Redis = await Redis.from_url(settings.REDIS_URL, decode_responses=False)
    app.state.redis = redis

    consumer = StreamConsumer(redis)
    await consumer.setup()

    consumer_task = asyncio.create_task(consumer.consume_forever())
    app.state.consumer_task = consumer_task

    logger.info("app.started", service=settings.SERVICE_NAME)

    yield

    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass

    await redis.aclose()
    logger.info("app.shutdown", service=settings.SERVICE_NAME)


app = FastAPI(
    title="Stratum Observer Service",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)

app.include_router(audit_logs_router, prefix="/api/v1")
app.include_router(stream_router, prefix="/api/v1")


@app.get("/health", include_in_schema=False)
async def health() -> JSONResponse:
    return JSONResponse({"status": "healthy"})

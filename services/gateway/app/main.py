import logging
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
import redis.asyncio as aioredis
import structlog
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.rate_limit import init_redis
from app.middleware.auth import AuthMiddleware
from app.middleware.context import ContextMiddleware
from app.routers.proxy import router as proxy_router

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
    logger.info("gateway.startup", environment=settings.ENVIRONMENT)

    app.state.http_client = httpx.AsyncClient(timeout=120.0)
    redis_client = aioredis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    app.state.redis = redis_client
    init_redis(redis_client)

    yield

    await app.state.http_client.aclose()
    await app.state.redis.aclose()
    logger.info("gateway.shutdown")


app = FastAPI(
    title="Stratum Gateway",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.add_middleware(AuthMiddleware)
app.add_middleware(ContextMiddleware)


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "healthy"})


app.include_router(proxy_router)

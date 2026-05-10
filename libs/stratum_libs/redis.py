import json
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

import redis.asyncio as redis
from redis.asyncio import ConnectionPool, Redis

from stratum_libs.config import settings

_pool: ConnectionPool | None = None


def _get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)
    return _pool


async def get_redis() -> AsyncGenerator[Redis, None]:
    r: Redis = redis.Redis(connection_pool=_get_pool())
    try:
        yield r
    finally:
        await r.aclose()


async def publish_event(
    r: Redis,
    stream: str,
    event_type: str,
    tenant_id: str,
    payload: dict[str, Any],
) -> str:
    event: dict[str, str] = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "tenant_id": tenant_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "payload": json.dumps(payload),
    }
    return await r.xadd(stream, event)

import time
import uuid

from fastapi import HTTPException, status
from redis.asyncio import Redis

RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW_SECONDS = 60

_redis: Redis | None = None


def init_redis(client: Redis) -> None:
    global _redis
    _redis = client


async def check_rate_limit(tenant_id: str) -> None:
    if _redis is None:
        return

    key = f"rate_limit:{tenant_id}"
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW_SECONDS

    pipe = _redis.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)
    pipe.zcard(key)
    pipe.zadd(key, {str(uuid.uuid4()): now})
    pipe.expire(key, RATE_LIMIT_WINDOW_SECONDS + 1)
    results = await pipe.execute()

    current_count: int = results[1]

    if current_count >= RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(RATE_LIMIT_WINDOW_SECONDS)},
        )

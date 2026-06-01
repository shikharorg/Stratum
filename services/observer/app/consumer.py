from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

import structlog
from redis.asyncio import Redis

from app.core.config import settings
from app.db import AsyncSessionFactory
from app.models.audit_log import AuditLog
from app.repositories.audit_log import AuditLogRepository
from app.schemas.audit_log import AuditLogCreate

logger = structlog.get_logger()

SSE_SUBSCRIBERS: dict[str, list[asyncio.Queue]] = {}

_STREAMS = ["ingestion", "retrieval", "workflow", "connectors", "identity"]

_STREAM_TO_SERVICE: dict[str, str] = {
    "ingestion": "ingestion",
    "retrieval": "retrieval",
    "workflow": "workflow",
    "connectors": "connectors",
    "identity": "identity",
}


async def add_subscriber(tenant_id: str) -> asyncio.Queue:
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    SSE_SUBSCRIBERS.setdefault(tenant_id, []).append(queue)
    return queue


async def remove_subscriber(tenant_id: str, queue: asyncio.Queue) -> None:
    subscribers = SSE_SUBSCRIBERS.get(tenant_id, [])
    try:
        subscribers.remove(queue)
    except ValueError:
        pass
    if not subscribers:
        SSE_SUBSCRIBERS.pop(tenant_id, None)


class StreamConsumer:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def setup(self) -> None:
        for stream in _STREAMS:
            try:
                await self._redis.xgroup_create(
                    stream,
                    settings.REDIS_CONSUMER_GROUP,
                    id="$",
                    mkstream=True,
                )
            except Exception as exc:
                if "BUSYGROUP" in str(exc):
                    pass
                else:
                    logger.warning(
                        "consumer.group_create_failed",
                        stream=stream,
                        error=str(exc),
                    )

    async def consume_forever(self) -> None:
        streams_arg = {stream: ">" for stream in _STREAMS}
        while True:
            try:
                results: list[Any] = await self._redis.xreadgroup(
                    groupname=settings.REDIS_CONSUMER_GROUP,
                    consumername=settings.REDIS_CONSUMER_NAME,
                    streams=streams_arg,
                    count=100,
                    block=1000,
                )
                if not results:
                    continue
                for stream_name, messages in results:
                    stream = stream_name if isinstance(stream_name, str) else stream_name.decode()
                    for event_id, data in messages:
                        decoded_id = event_id if isinstance(event_id, str) else event_id.decode()
                        decoded_data: dict[str, str] = {
                            (k.decode() if isinstance(k, bytes) else k): (
                                v.decode() if isinstance(v, bytes) else v
                            )
                            for k, v in data.items()
                        }
                        try:
                            await self._process_event(stream, decoded_id, decoded_data)
                            await self._redis.xack(
                                stream,
                                settings.REDIS_CONSUMER_GROUP,
                                decoded_id,
                            )
                        except Exception as exc:
                            logger.error(
                                "consumer.process_event_failed",
                                stream=stream,
                                event_id=decoded_id,
                                error=str(exc),
                            )
            except Exception as exc:
                logger.error("consumer.loop_error", error=str(exc))

    async def _process_event(self, stream: str, event_id: str, data: dict[str, str]) -> None:
        service = _STREAM_TO_SERVICE.get(stream, stream)

        tenant_id_raw = data.get("tenant_id", "")
        try:
            tenant_uuid = uuid.UUID(tenant_id_raw)
        except (ValueError, AttributeError):
            logger.warning("consumer.invalid_tenant_id", stream=stream, event_id=event_id)
            return

        user_id_raw = data.get("user_id")
        user_uuid: uuid.UUID | None = None
        if user_id_raw:
            try:
                user_uuid = uuid.UUID(user_id_raw)
            except (ValueError, AttributeError):
                pass

        payload_raw = data.get("payload", "{}")
        try:
            payload = json.loads(payload_raw) if isinstance(payload_raw, str) else payload_raw
        except (json.JSONDecodeError, TypeError):
            payload = {}

        audit_data = AuditLogCreate(
            tenant_id=tenant_uuid,
            event_type=data.get("event_type", "unknown"),
            service=data.get("service", service),
            severity=data.get("severity", "info"),
            user_id=user_uuid,
            resource_id=data.get("resource_id") or None,
            resource_type=data.get("resource_type") or None,
            correlation_id=data.get("correlation_id") or None,
            payload=payload,
        )

        async with AsyncSessionFactory() as session:
            repo = AuditLogRepository(session)
            audit_log = await repo.create(audit_data)
            await session.commit()

        asyncio.create_task(_push_to_sse(str(tenant_uuid), audit_log))


async def _push_to_sse(tenant_id: str, audit_log: AuditLog) -> None:
    try:
        subscribers = SSE_SUBSCRIBERS.get(tenant_id, [])
        for queue in list(subscribers):
            try:
                queue.put_nowait(audit_log)
            except asyncio.QueueFull:
                logger.warning("consumer.sse_queue_full", tenant_id=tenant_id)
    except Exception as exc:
        logger.error("consumer.sse_push_failed", tenant_id=tenant_id, error=str(exc))

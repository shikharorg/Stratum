from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

import structlog
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from stratum_libs.auth import RequestContext

from app.consumer import add_subscriber, remove_subscriber
from app.dependencies import get_request_context
from app.schemas.audit_log import AuditLogResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/stream", tags=["stream"])

_HEARTBEAT = 'data: {"type": "heartbeat"}\n\n'


@router.get("")
async def stream_events(
    ctx: RequestContext = Depends(get_request_context),
) -> StreamingResponse:
    tenant_id = ctx.tenant_id

    async def event_generator() -> AsyncGenerator[str, None]:
        queue = await add_subscriber(tenant_id)
        try:
            while True:
                try:
                    audit_log = await asyncio.wait_for(queue.get(), timeout=30.0)
                    payload = AuditLogResponse.model_validate(audit_log).model_dump_json()
                    yield f"data: {payload}\n\n"
                except asyncio.TimeoutError:
                    yield _HEARTBEAT
                except Exception as exc:
                    logger.error("stream.event_error", tenant_id=tenant_id, error=str(exc))
        finally:
            await remove_subscriber(tenant_id, queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

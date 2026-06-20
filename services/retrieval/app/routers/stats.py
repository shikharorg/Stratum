import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from stratum_libs.auth import RequestContext

from app.db import get_session
from app.dependencies import get_request_context
from app.models.retrieval_log import RetrievalLog

router = APIRouter(tags=["stats"])


@router.get("/stats")
async def retrieval_stats(
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
) -> dict:
    tenant_uuid = uuid.UUID(ctx.tenant_id)
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    total = await session.scalar(
        select(func.count())
        .select_from(RetrievalLog)
        .where(RetrievalLog.tenant_id == tenant_uuid)
    ) or 0

    this_week = await session.scalar(
        select(func.count())
        .select_from(RetrievalLog)
        .where(
            RetrievalLog.tenant_id == tenant_uuid,
            RetrievalLog.created_at >= week_ago,
        )
    ) or 0

    return {"total": total, "this_week": this_week}

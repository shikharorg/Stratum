import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from stratum_libs.auth import RequestContext

from app.db import get_session
from app.dependencies import get_request_context
from app.models.workflow_run import WorkflowRun

router = APIRouter(prefix="/workflow", tags=["stats"])


@router.get("/stats")
async def workflow_stats(
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
) -> dict:
    tenant_uuid = uuid.UUID(ctx.tenant_id)

    total = await session.scalar(
        select(func.count()).select_from(WorkflowRun).where(
            WorkflowRun.tenant_id == tenant_uuid
        )
    ) or 0

    completed = await session.scalar(
        select(func.count()).select_from(WorkflowRun).where(
            WorkflowRun.tenant_id == tenant_uuid,
            WorkflowRun.status == "completed",
        )
    ) or 0

    failed = await session.scalar(
        select(func.count()).select_from(WorkflowRun).where(
            WorkflowRun.tenant_id == tenant_uuid,
            WorkflowRun.status == "failed",
        )
    ) or 0

    denom = completed + failed
    success_rate = round((completed / denom) * 100, 1) if denom > 0 else 0.0

    return {
        "total_runs": total,
        "completed_runs": completed,
        "failed_runs": failed,
        "success_rate": success_rate,
    }

import uuid

from fastapi import APIRouter, Depends, Header
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.evaluation import EvaluationResult

router = APIRouter()


@router.get("/quality")
async def evaluation_quality(
    x_tenant_id: str = Header(..., alias="x-tenant-id"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    tenant_uuid = uuid.UUID(x_tenant_id)

    row = (
        await session.execute(
            select(
                func.count().label("total"),
                func.avg(EvaluationResult.faithfulness).label("avg_faithfulness"),
                func.avg(EvaluationResult.answer_relevancy).label("avg_answer_relevancy"),
                func.avg(EvaluationResult.context_precision).label("avg_context_precision"),
            )
            .select_from(EvaluationResult)
            .where(
                EvaluationResult.tenant_id == tenant_uuid,
                EvaluationResult.status == "completed",
            )
        )
    ).one()

    def pct(v: float | None) -> float:
        return round((v or 0.0) * 100, 1)

    return {
        "faithfulness": pct(row.avg_faithfulness),
        "answer_relevancy": pct(row.avg_answer_relevancy),
        "context_precision": pct(row.avg_context_precision),
        "total_evaluations": row.total,
    }

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import EvaluationResult


class EvaluationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        tenant_id: uuid.UUID,
        query: str,
        answer: str,
        contexts: list[str],
        retrieval_log_id: uuid.UUID | None = None,
    ) -> EvaluationResult:
        result = EvaluationResult(
            tenant_id=tenant_id,
            query=query,
            answer=answer,
            contexts=contexts,
            retrieval_log_id=retrieval_log_id,
            status="pending",
        )
        self._session.add(result)
        await self._session.flush()
        await self._session.refresh(result)
        return result

    async def get_by_id(
        self, id: uuid.UUID, tenant_id: uuid.UUID
    ) -> EvaluationResult | None:
        result = await self._session.execute(
            select(EvaluationResult).where(
                EvaluationResult.id == id,
                EvaluationResult.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_paginated(
        self, tenant_id: uuid.UUID, page: int, page_size: int
    ) -> tuple[list[EvaluationResult], int]:
        count_result = await self._session.execute(
            select(func.count())
            .select_from(EvaluationResult)
            .where(EvaluationResult.tenant_id == tenant_id)
        )
        total: int = count_result.scalar_one()

        items_result = await self._session.execute(
            select(EvaluationResult)
            .where(EvaluationResult.tenant_id == tenant_id)
            .order_by(EvaluationResult.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(items_result.scalars().all()), total

    async def update_scores(
        self,
        id: uuid.UUID,
        faithfulness: float | None,
        answer_relevancy: float | None,
        context_precision: float | None,
        overall_score: float | None,
        status: str,
        error_message: str | None = None,
    ) -> EvaluationResult:
        result = await self._session.get(EvaluationResult, id)
        result.faithfulness = faithfulness
        result.answer_relevancy = answer_relevancy
        result.context_precision = context_precision
        result.overall_score = overall_score
        result.status = status
        result.error_message = error_message
        await self._session.flush()
        await self._session.refresh(result)
        return result

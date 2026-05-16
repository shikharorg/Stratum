import uuid
from typing import Any

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.retrieval_log import RetrievalLog

logger = structlog.get_logger()


class RetrievalLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        tenant_id: uuid.UUID,
        query: str,
        source_filter: str | None,
        chunks_retrieved: int,
        chunks_after_rerank: int,
        grounding_passed: bool,
        latency_ms: int,
        extra_metadata: dict[str, Any],
    ) -> RetrievalLog:
        log = RetrievalLog(
            tenant_id=tenant_id,
            query=query,
            source_filter=source_filter,
            chunks_retrieved=chunks_retrieved,
            chunks_after_rerank=chunks_after_rerank,
            grounding_passed=grounding_passed,
            latency_ms=latency_ms,
            extra_metadata=extra_metadata,
        )
        self._session.add(log)
        await self._session.flush()
        await self._session.refresh(log)
        logger.info("retrieval_log.created", log_id=str(log.id), tenant_id=str(tenant_id))
        return log

    async def get_by_tenant(
        self,
        tenant_id: uuid.UUID,
        skip: int,
        limit: int,
    ) -> tuple[list[RetrievalLog], int]:
        count_result = await self._session.execute(
            select(func.count())
            .select_from(RetrievalLog)
            .where(RetrievalLog.tenant_id == tenant_id)
        )
        total = count_result.scalar_one()

        rows_result = await self._session.execute(
            select(RetrievalLog)
            .where(RetrievalLog.tenant_id == tenant_id)
            .order_by(RetrievalLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        logs = list(rows_result.scalars().all())

        return logs, total

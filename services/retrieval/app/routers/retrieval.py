import asyncio
import json
import re
import time
import uuid

import httpx
import redis.asyncio as aioredis
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from stratum_libs.auth import RequestContext

from app.core.config import settings
from app.db import get_session
from app.dependencies import get_query_encoder, get_reranker, get_request_context, get_searcher
from app.pipeline import grounding
from app.pipeline.encoder import QueryEncoder
from app.pipeline.reranker import Reranker
from app.pipeline.searcher import HybridSearcher
from app.repositories.retrieval_log import RetrievalLogRepository
from app.schemas.retrieval import ChunkResult, RetrievalRequest, RetrievalResponse, RetrievalResult

logger = structlog.get_logger()

router = APIRouter(prefix="/retrieve", tags=["retrieval"])

_ABBREVIATIONS: dict[str, str] = {
    r"\bPRs?\b": "pull requests",
    r"\bAPI\b": "application programming interface",
    r"\bCI\b": "continuous integration",
    r"\bCD\b": "continuous deployment",
    r"\bCICD\b": "continuous integration continuous deployment",
    r"\bSLA\b": "service level agreement",
    r"\bSEV\b": "severity",
    r"\bADR\b": "architecture decision record",
    r"\bSOX\b": "sarbanes oxley",
}


def _expand_abbreviations(query: str) -> str:
    expanded = query
    for pattern, replacement in _ABBREVIATIONS.items():
        expanded = re.sub(pattern, replacement, expanded, flags=re.IGNORECASE)
    return expanded


async def _trigger_evaluation(
    query: str,
    answer: str,
    contexts: list[str],
    retrieval_log_id: str,
    tenant_id: str,
) -> None:
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            await client.post(
                f"{settings.EVALUATION_SERVICE_URL}/api/v1/evaluate",
                json={
                    "query": query,
                    "answer": answer,
                    "contexts": contexts,
                    "retrieval_log_id": retrieval_log_id,
                    "tenant_id": tenant_id,
                },
            )
    except Exception as e:
        logger.warning("evaluation.trigger_failed", error=str(e))


@router.post("", response_model=RetrievalResponse, status_code=status.HTTP_200_OK)
async def retrieve(
    body: RetrievalRequest,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
    encoder: QueryEncoder = Depends(get_query_encoder),
    reranker: Reranker = Depends(get_reranker),
    searcher: HybridSearcher = Depends(get_searcher),
) -> RetrievalResponse:
    start = time.monotonic()
    tenant_id = ctx.tenant_id

    dense_vector = encoder.encode_query(body.query)
    # Expand abbreviations only for sparse (BM25) encoding so term overlap
    # matches document vocabulary (e.g. "PR" -> "pull requests").
    sparse_vector = encoder.encode_sparse(_expand_abbreviations(body.query))

    candidates = await searcher.search(
        query_vector=dense_vector,
        sparse_vector=sparse_vector,
        tenant_id=tenant_id,
        source_type=body.source_filter,
        top_k=20,
    )

    reranked = reranker.rerank(body.query, candidates, body.top_k)

    answer = ""
    grounding_passed = True

    if body.include_generation and reranked:
        context_chunks = [r.text for r in reranked]
        labeled_chunks = [
            f"Source: {r.source_url or r.source_type}\n{r.text}" for r in reranked
        ]
        answer = await grounding.generate_answer(body.query, labeled_chunks)

        if answer:
            grounding_passed = await grounding.validate(body.query, answer, context_chunks)

            if not grounding_passed:
                logger.warning(
                    "retrieval.grounding_failed_regenerating",
                    tenant_id=tenant_id,
                    query=body.query[:100],
                )
                answer = await grounding.generate_answer(body.query, labeled_chunks, strict=True)
                grounding_passed = await grounding.validate(body.query, answer, context_chunks)

    latency_ms = int((time.monotonic() - start) * 1000)

    log_repo = RetrievalLogRepository(session)
    log_entry = await log_repo.create(
        tenant_id=uuid.UUID(tenant_id),
        query=body.query,
        source_filter=body.source_filter,
        chunks_retrieved=len(candidates),
        chunks_after_rerank=len(reranked),
        grounding_passed=grounding_passed,
        latency_ms=latency_ms,
        extra_metadata={},
    )
    await session.commit()

    try:
        redis_client = await aioredis.from_url(settings.REDIS_URL)
        await redis_client.xadd(
            "retrieval",
            {
                "event_type": "retrieval.completed",
                "tenant_id": tenant_id,
                "resource_id": str(log_entry.id),
                "resource_type": "retrieval_log",
                "payload": json.dumps({
                    "query": body.query[:200],
                    "grounding_passed": grounding_passed,
                    "latency_ms": latency_ms,
                    "chunks_count": len(reranked),
                }),
                "severity": "info",
            }
        )
        await redis_client.aclose()
    except Exception:
        pass

    if answer and body.include_generation:
        task = asyncio.create_task(
            _trigger_evaluation(
                query=body.query,
                answer=answer,
                contexts=[r.text for r in reranked],
                retrieval_log_id=str(log_entry.id),
                tenant_id=tenant_id,
            )
        )
        task.set_name(f"evaluation:{log_entry.id}")

    logger.info(
        "retrieval.completed",
        tenant_id=tenant_id,
        candidates=len(candidates),
        reranked=len(reranked),
        grounding_passed=grounding_passed,
        latency_ms=latency_ms,
    )

    chunk_results = [
        ChunkResult(
            chunk_id=r.chunk_id,
            document_id=r.document_id,
            text=r.text,
            score=r.combined_score,
            source_type=r.source_type,
            source_url=r.source_url,
        )
        for r in reranked
    ]

    return RetrievalResponse(
        id=log_entry.id,
        tenant_id=uuid.UUID(tenant_id),
        query=body.query,
        result=RetrievalResult(
            answer=answer,
            grounding_passed=grounding_passed,
            chunks=chunk_results,
            latency_ms=float(latency_ms),
        ),
        created_at=log_entry.created_at,
    )

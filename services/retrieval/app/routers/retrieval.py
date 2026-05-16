import time
import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from stratum_libs.auth import RequestContext

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
    sparse_vector = encoder.encode_sparse(body.query)

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
        answer = await grounding.generate_answer(body.query, context_chunks)

        if answer:
            grounding_passed = await grounding.validate(body.query, answer, context_chunks)

            if not grounding_passed:
                logger.warning(
                    "retrieval.grounding_failed_regenerating",
                    tenant_id=tenant_id,
                    query=body.query[:100],
                )
                answer = await grounding.generate_answer(body.query, context_chunks, strict=True)
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

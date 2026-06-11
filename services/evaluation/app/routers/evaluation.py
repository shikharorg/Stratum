import uuid

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.evaluator import run_evaluation
from app.db import get_session
from app.repositories.evaluation import EvaluationRepository
from app.schemas.evaluation import EvaluateRequest, EvaluateResponse, EvaluationListResponse

logger = structlog.get_logger()

router = APIRouter()


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate(
    request: EvaluateRequest,
    session: AsyncSession = Depends(get_session),
) -> EvaluateResponse:
    repo = EvaluationRepository(session)

    retrieval_log_id = (
        uuid.UUID(request.retrieval_log_id) if request.retrieval_log_id else None
    )

    record = await repo.create(
        tenant_id=uuid.UUID(request.tenant_id),
        query=request.query,
        answer=request.answer,
        contexts=request.contexts,
        retrieval_log_id=retrieval_log_id,
    )
    await session.commit()

    scores = await run_evaluation(
        query=request.query,
        answer=request.answer,
        contexts=request.contexts,
    )

    if "error" in scores:
        record = await repo.update_scores(
            id=record.id,
            faithfulness=None,
            answer_relevancy=None,
            context_precision=None,
            overall_score=None,
            status="failed",
            error_message=scores["error"],
        )
    else:
        record = await repo.update_scores(
            id=record.id,
            faithfulness=scores["faithfulness"],
            answer_relevancy=scores["answer_relevancy"],
            context_precision=scores["context_precision"],
            overall_score=scores["overall_score"],
            status="completed",
        )

    await session.commit()

    logger.info("evaluate.done", id=str(record.id), status=record.status)

    return EvaluateResponse(
        id=str(record.id),
        status=record.status,
        faithfulness=record.faithfulness,
        answer_relevancy=record.answer_relevancy,
        context_precision=record.context_precision,
        overall_score=record.overall_score,
        error_message=record.error_message,
        created_at=record.created_at,
    )


@router.get("/evaluations", response_model=EvaluationListResponse)
async def list_evaluations(
    page: int = 1,
    page_size: int = 20,
    x_tenant_id: str = Header(..., alias="x-tenant-id"),
    session: AsyncSession = Depends(get_session),
) -> EvaluationListResponse:
    repo = EvaluationRepository(session)
    items, total = await repo.list_paginated(
        tenant_id=uuid.UUID(x_tenant_id),
        page=page,
        page_size=page_size,
    )

    return EvaluationListResponse(
        items=[
            EvaluateResponse(
                id=str(item.id),
                status=item.status,
                faithfulness=item.faithfulness,
                answer_relevancy=item.answer_relevancy,
                context_precision=item.context_precision,
                overall_score=item.overall_score,
                error_message=item.error_message,
                created_at=item.created_at,
            )
            for item in items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/evaluations/{evaluation_id}", response_model=EvaluateResponse)
async def get_evaluation(
    evaluation_id: str,
    x_tenant_id: str = Header(..., alias="x-tenant-id"),
    session: AsyncSession = Depends(get_session),
) -> EvaluateResponse:
    repo = EvaluationRepository(session)
    record = await repo.get_by_id(
        id=uuid.UUID(evaluation_id),
        tenant_id=uuid.UUID(x_tenant_id),
    )

    if record is None:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    return EvaluateResponse(
        id=str(record.id),
        status=record.status,
        faithfulness=record.faithfulness,
        answer_relevancy=record.answer_relevancy,
        context_precision=record.context_precision,
        overall_score=record.overall_score,
        error_message=record.error_message,
        created_at=record.created_at,
    )

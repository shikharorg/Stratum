import uuid

import structlog
from arq.connections import ArqRedis
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from stratum_libs.auth import RequestContext

from app.db import get_session
from app.dependencies import get_arq_pool, get_request_context
from app.repositories.run import WorkflowRunRepository
from app.repositories.workflow import WorkflowRepository
from app.schemas.run import RunList, RunRequest, RunResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/workflows", tags=["runs"])

_TERMINAL_STATUSES = frozenset({"completed", "failed", "cancelled"})


@router.post("/{workflow_id}/runs", response_model=RunResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_run(
    workflow_id: uuid.UUID,
    body: RunRequest,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
    arq_pool: ArqRedis = Depends(get_arq_pool),
) -> RunResponse:
    tenant_uuid = uuid.UUID(ctx.tenant_id)

    workflow = await WorkflowRepository(session).get_by_id(workflow_id, tenant_uuid)
    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "about:blank",
                "title": "Workflow not found",
                "status": 404,
                "detail": f"Workflow {workflow_id} not found",
            },
        )

    run_repo = WorkflowRunRepository(session)
    run = await run_repo.create(
        tenant_id=tenant_uuid,
        workflow_id=workflow_id,
        input_data=body.input_data,
        extra_metadata={},
    )
    await session.commit()

    try:
        await arq_pool.enqueue_job(
            "execute_workflow",
            run_id=str(run.id),
            tenant_id=ctx.tenant_id,
            workflow_id=str(workflow_id),
            input_data=body.input_data,
            _job_id=str(run.id),
        )
    except Exception as exc:
        logger.exception("runs.enqueue_failed", run_id=str(run.id), tenant_id=ctx.tenant_id)
        try:
            await run_repo.update_status(run.id, tenant_uuid, "failed", str(exc))
            await session.commit()
        except Exception:
            logger.exception("runs.failed_status_update_failed", run_id=str(run.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "type": "about:blank",
                "title": "Queue error",
                "status": 500,
                "detail": "Failed to enqueue workflow job",
            },
        )

    logger.info(
        "runs.enqueued",
        run_id=str(run.id),
        workflow_id=str(workflow_id),
        tenant_id=ctx.tenant_id,
    )
    return RunResponse.model_validate(run)


@router.get("/{workflow_id}/runs", response_model=RunList)
async def list_runs(
    workflow_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
) -> RunList:
    tenant_uuid = uuid.UUID(ctx.tenant_id)

    workflow = await WorkflowRepository(session).get_by_id(workflow_id, tenant_uuid)
    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "about:blank",
                "title": "Workflow not found",
                "status": 404,
                "detail": f"Workflow {workflow_id} not found",
            },
        )

    skip = (page - 1) * page_size
    runs, total = await WorkflowRunRepository(session).get_by_workflow(
        workflow_id, tenant_uuid, skip=skip, limit=page_size
    )
    return RunList(
        items=[RunResponse.model_validate(r) for r in runs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{workflow_id}/runs/{run_id}", response_model=RunResponse)
async def get_run(
    workflow_id: uuid.UUID,
    run_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
) -> RunResponse:
    tenant_uuid = uuid.UUID(ctx.tenant_id)

    workflow = await WorkflowRepository(session).get_by_id(workflow_id, tenant_uuid)
    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "about:blank",
                "title": "Workflow not found",
                "status": 404,
                "detail": f"Workflow {workflow_id} not found",
            },
        )

    run = await WorkflowRunRepository(session).get_by_id(run_id, tenant_uuid)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "about:blank",
                "title": "Run not found",
                "status": 404,
                "detail": f"Run {run_id} not found",
            },
        )
    return RunResponse.model_validate(run)


@router.delete("/{workflow_id}/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_run(
    workflow_id: uuid.UUID,
    run_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
    arq_pool: ArqRedis = Depends(get_arq_pool),
) -> Response:
    tenant_uuid = uuid.UUID(ctx.tenant_id)

    run = await WorkflowRunRepository(session).get_by_id(run_id, tenant_uuid)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "about:blank",
                "title": "Run not found",
                "status": 404,
                "detail": f"Run {run_id} not found",
            },
        )

    if run.status in _TERMINAL_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "type": "about:blank",
                "title": "Run cannot be cancelled",
                "status": 400,
                "detail": f"Run {run_id} has status '{run.status}' and cannot be cancelled",
            },
        )

    job_id = str(run_id)
    queued = await arq_pool.queued_jobs()
    queued_ids = {j.job_id for j in queued}

    if job_id in queued_ids:
        await arq_pool.zrem("arq:queue", job_id)
        logger.info("runs.cancelled_from_queue", run_id=job_id, tenant_id=ctx.tenant_id)
    else:
        await arq_pool.set(f"arq:cancel:{job_id}", "1", ex=3600)
        logger.info("runs.cancel_flag_set", run_id=job_id, tenant_id=ctx.tenant_id)

    await WorkflowRunRepository(session).update_status(run_id, tenant_uuid, "cancelled")
    await session.commit()

    logger.info("runs.cancelled", run_id=str(run_id), workflow_id=str(workflow_id), tenant_id=ctx.tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

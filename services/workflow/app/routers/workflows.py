import uuid

import structlog
from arq.connections import ArqRedis
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from stratum_libs.auth import RequestContext

from app.db import get_session
from app.dependencies import get_arq_pool, get_request_context
from app.repositories.workflow import WorkflowRepository
from app.schemas.workflow import WorkflowCreate, WorkflowList, WorkflowResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    body: WorkflowCreate,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
) -> WorkflowResponse:
    tenant_uuid = uuid.UUID(ctx.tenant_id)
    repo = WorkflowRepository(session)
    workflow = await repo.create(
        tenant_id=tenant_uuid,
        name=body.name,
        description=body.description,
        graph_definition=body.graph_definition,
        extra_metadata=body.extra_metadata,
    )
    await session.commit()
    logger.info("workflows.created", workflow_id=str(workflow.id), tenant_id=ctx.tenant_id)
    return WorkflowResponse.model_validate(workflow)


@router.get("", response_model=WorkflowList)
async def list_workflows(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
) -> WorkflowList:
    tenant_uuid = uuid.UUID(ctx.tenant_id)
    skip = (page - 1) * page_size
    repo = WorkflowRepository(session)
    workflows, total = await repo.get_by_tenant(tenant_uuid, skip=skip, limit=page_size)
    return WorkflowList(
        items=[WorkflowResponse.model_validate(w) for w in workflows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
) -> WorkflowResponse:
    tenant_uuid = uuid.UUID(ctx.tenant_id)
    repo = WorkflowRepository(session)
    workflow = await repo.get_by_id(workflow_id, tenant_uuid)
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
    return WorkflowResponse.model_validate(workflow)


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_workflow(
    workflow_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
) -> Response:
    tenant_uuid = uuid.UUID(ctx.tenant_id)
    repo = WorkflowRepository(session)
    workflow = await repo.get_by_id(workflow_id, tenant_uuid)
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
    await repo.deactivate(workflow_id, tenant_uuid)
    await session.commit()
    logger.info("workflows.deactivated", workflow_id=str(workflow_id), tenant_id=ctx.tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

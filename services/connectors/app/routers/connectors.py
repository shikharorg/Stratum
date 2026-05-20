import uuid

import structlog
from arq.connections import ArqRedis
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from stratum_libs.auth import RequestContext

from app.crypto import encrypt_credentials
from app.db import get_session
from app.dependencies import get_arq_pool, get_request_context
from app.repositories.connector import ConnectorRepository
from app.repositories.run import ConnectorRunRepository
from app.schemas.connector import ConnectorCreate, ConnectorList, ConnectorResponse
from app.schemas.run import ConnectorRunList, ConnectorRunResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/connectors", tags=["connectors"])


@router.post("", response_model=ConnectorResponse, status_code=status.HTTP_201_CREATED)
async def create_connector(
    body: ConnectorCreate,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
) -> ConnectorResponse:
    tenant_uuid = uuid.UUID(ctx.tenant_id)
    encrypted = encrypt_credentials(body.credentials)
    repo = ConnectorRepository(session)
    connector = await repo.create(
        tenant_id=tenant_uuid,
        name=body.name,
        connector_type=body.connector_type,
        credentials=encrypted,
        webhook_secret=body.webhook_secret,
        sync_config=body.sync_config,
        extra_metadata=body.extra_metadata,
    )
    await session.commit()
    logger.info("connectors.created", connector_id=str(connector.id), tenant_id=ctx.tenant_id)
    return ConnectorResponse.model_validate(connector)


@router.get("", response_model=ConnectorList)
async def list_connectors(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
) -> ConnectorList:
    tenant_uuid = uuid.UUID(ctx.tenant_id)
    skip = (page - 1) * page_size
    connectors, total = await ConnectorRepository(session).get_by_tenant(
        tenant_uuid, skip=skip, limit=page_size
    )
    return ConnectorList(
        items=[ConnectorResponse.model_validate(c) for c in connectors],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{connector_id}", response_model=ConnectorResponse)
async def get_connector(
    connector_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
) -> ConnectorResponse:
    tenant_uuid = uuid.UUID(ctx.tenant_id)
    connector = await ConnectorRepository(session).get_by_id(connector_id, tenant_uuid)
    if connector is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "about:blank",
                "title": "Connector not found",
                "status": 404,
                "detail": f"Connector {connector_id} not found",
            },
        )
    return ConnectorResponse.model_validate(connector)


@router.delete("/{connector_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_connector(
    connector_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
) -> Response:
    tenant_uuid = uuid.UUID(ctx.tenant_id)
    repo = ConnectorRepository(session)
    connector = await repo.get_by_id(connector_id, tenant_uuid)
    if connector is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "about:blank",
                "title": "Connector not found",
                "status": 404,
                "detail": f"Connector {connector_id} not found",
            },
        )
    await repo.deactivate(connector_id, tenant_uuid)
    await session.commit()
    logger.info("connectors.deactivated", connector_id=str(connector_id), tenant_id=ctx.tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{connector_id}/sync", status_code=status.HTTP_202_ACCEPTED)
async def trigger_sync(
    connector_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
    arq_pool: ArqRedis = Depends(get_arq_pool),
) -> JSONResponse:
    tenant_uuid = uuid.UUID(ctx.tenant_id)
    connector = await ConnectorRepository(session).get_by_id(connector_id, tenant_uuid)
    if connector is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "about:blank",
                "title": "Connector not found",
                "status": 404,
                "detail": f"Connector {connector_id} not found",
            },
        )
    await arq_pool.enqueue_job(
        "sync_connector",
        connector_id=str(connector_id),
        tenant_id=ctx.tenant_id,
    )
    await session.commit()
    logger.info("connectors.sync_enqueued", connector_id=str(connector_id), tenant_id=ctx.tenant_id)
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"status": "queued", "connector_id": str(connector_id)},
    )


@router.get("/{connector_id}/runs", response_model=ConnectorRunList)
async def list_runs(
    connector_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
) -> ConnectorRunList:
    tenant_uuid = uuid.UUID(ctx.tenant_id)
    connector = await ConnectorRepository(session).get_by_id(connector_id, tenant_uuid)
    if connector is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "about:blank",
                "title": "Connector not found",
                "status": 404,
                "detail": f"Connector {connector_id} not found",
            },
        )
    skip = (page - 1) * page_size
    runs, total = await ConnectorRunRepository(session).get_by_connector(
        connector_id, tenant_uuid, skip=skip, limit=page_size
    )
    return ConnectorRunList(
        items=[ConnectorRunResponse.model_validate(r) for r in runs],
        total=total,
        page=page,
        page_size=page_size,
    )

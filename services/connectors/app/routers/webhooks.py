import json
import uuid

import structlog
from arq.connections import ArqRedis
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.dependencies import get_arq_pool
from app.models.connector import Connector

logger = structlog.get_logger()

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


async def _get_connector_or_404(
    connector_id: uuid.UUID, session: AsyncSession
) -> Connector:
    result = await session.execute(
        select(Connector).where(Connector.id == connector_id)
    )
    connector = result.scalar_one_or_none()
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
    return connector


@router.post("/{connector_id}/slack", status_code=status.HTTP_200_OK)
async def slack_webhook(
    connector_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    arq_pool: ArqRedis = Depends(get_arq_pool),
    x_slack_request_timestamp: str | None = Header(default=None),
    x_slack_signature: str | None = Header(default=None),
) -> JSONResponse:
    raw_body = await request.body()
    connector = await _get_connector_or_404(connector_id, session)

    try:
        payload: dict = json.loads(raw_body)
    except Exception:
        payload = {}

    payload["_raw_body"] = raw_body.decode(errors="replace")
    payload["_timestamp"] = x_slack_request_timestamp or ""
    payload["_signature"] = x_slack_signature or ""

    await arq_pool.enqueue_job(
        "process_webhook",
        connector_id=str(connector_id),
        connector_type="slack",
        payload=payload,
    )
    logger.info("webhooks.slack.enqueued", connector_id=str(connector_id))
    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "ok"})


@router.post("/{connector_id}/jira", status_code=status.HTTP_200_OK)
async def jira_webhook(
    connector_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    arq_pool: ArqRedis = Depends(get_arq_pool),
) -> JSONResponse:
    raw_body = await request.body()
    connector = await _get_connector_or_404(connector_id, session)

    try:
        payload: dict = json.loads(raw_body)
    except Exception:
        payload = {}

    await arq_pool.enqueue_job(
        "process_webhook",
        connector_id=str(connector_id),
        connector_type="jira",
        payload=payload,
    )
    logger.info("webhooks.jira.enqueued", connector_id=str(connector_id))
    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "ok"})


@router.post("/{connector_id}/github", status_code=status.HTTP_200_OK)
async def github_webhook(
    connector_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    arq_pool: ArqRedis = Depends(get_arq_pool),
    x_github_event: str | None = Header(default=None),
    x_hub_signature_256: str | None = Header(default=None),
) -> JSONResponse:
    raw_body = await request.body()
    connector = await _get_connector_or_404(connector_id, session)

    try:
        payload: dict = json.loads(raw_body)
    except Exception:
        payload = {}

    payload["_raw_body"] = raw_body.decode(errors="replace")
    payload["_event_type"] = x_github_event or ""
    payload["_signature"] = x_hub_signature_256 or ""

    await arq_pool.enqueue_job(
        "process_webhook",
        connector_id=str(connector_id),
        connector_type="github",
        payload=payload,
    )
    logger.info("webhooks.github.enqueued", connector_id=str(connector_id), event=x_github_event)
    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "ok"})

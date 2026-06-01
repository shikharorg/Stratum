from __future__ import annotations

import uuid
from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from stratum_libs.auth import RequestContext

from app.db import get_session
from app.dependencies import get_request_context
from app.repositories.audit_log import AuditLogRepository
from app.schemas.audit_log import AuditLogFilter, AuditLogList, AuditLogResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get("", response_model=AuditLogList)
async def list_audit_logs(
    event_type: str | None = Query(default=None),
    service: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    resource_id: str | None = Query(default=None),
    from_timestamp: datetime | None = Query(default=None),
    to_timestamp: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
) -> AuditLogList:
    tenant_uuid = uuid.UUID(ctx.tenant_id)
    filters = AuditLogFilter(
        event_type=event_type,
        service=service,
        severity=severity,
        resource_id=resource_id,
        from_timestamp=from_timestamp,
        to_timestamp=to_timestamp,
    )
    skip = (page - 1) * page_size
    repo = AuditLogRepository(session)
    logs, total = await repo.query(tenant_uuid, filters, skip=skip, limit=page_size)
    return AuditLogList(
        items=[AuditLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
) -> AuditLogResponse:
    tenant_uuid = uuid.UUID(ctx.tenant_id)
    repo = AuditLogRepository(session)
    log = await repo.get_by_id(log_id, tenant_uuid)
    if log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "about:blank",
                "title": "Audit log not found",
                "status": 404,
                "detail": f"Audit log {log_id} not found",
            },
        )
    return AuditLogResponse.model_validate(log)

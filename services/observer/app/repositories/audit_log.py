from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogCreate, AuditLogFilter


class AuditLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: AuditLogCreate) -> AuditLog:
        expires_at = datetime.now(UTC) + timedelta(days=settings.EVENT_RETENTION_DAYS)
        audit_log = AuditLog(
            tenant_id=data.tenant_id,
            event_type=data.event_type,
            service=data.service,
            severity=data.severity,
            user_id=data.user_id,
            resource_id=data.resource_id,
            resource_type=data.resource_type,
            correlation_id=data.correlation_id,
            payload=data.payload,
            expires_at=expires_at,
        )
        self._session.add(audit_log)
        await self._session.flush()
        await self._session.refresh(audit_log)
        return audit_log

    async def get_by_id(self, log_id: uuid.UUID, tenant_id: uuid.UUID) -> AuditLog | None:
        result = await self._session.execute(
            select(AuditLog).where(
                AuditLog.id == log_id,
                AuditLog.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def query(
        self,
        tenant_id: uuid.UUID,
        filters: AuditLogFilter,
        skip: int,
        limit: int,
    ) -> tuple[list[AuditLog], int]:
        base = select(AuditLog).where(AuditLog.tenant_id == tenant_id)

        if filters.event_type is not None:
            base = base.where(AuditLog.event_type == filters.event_type)
        if filters.service is not None:
            base = base.where(AuditLog.service == filters.service)
        if filters.severity is not None:
            base = base.where(AuditLog.severity == filters.severity)
        if filters.resource_id is not None:
            base = base.where(AuditLog.resource_id == filters.resource_id)
        if filters.from_timestamp is not None:
            base = base.where(AuditLog.created_at >= filters.from_timestamp)
        if filters.to_timestamp is not None:
            base = base.where(AuditLog.created_at <= filters.to_timestamp)

        count_result = await self._session.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = count_result.scalar_one()

        rows_result = await self._session.execute(
            base.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
        )
        rows = list(rows_result.scalars().all())

        return rows, total

    async def delete_expired(self) -> int:
        result = await self._session.execute(
            delete(AuditLog)
            .where(AuditLog.expires_at <= datetime.now(UTC))
            .execution_options(synchronize_session=False)
        )
        return result.rowcount

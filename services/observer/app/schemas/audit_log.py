from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class AuditLogCreate(BaseModel):
    tenant_id: uuid.UUID
    event_type: str
    service: str
    severity: str = "info"
    user_id: uuid.UUID | None = None
    resource_id: str | None = None
    resource_type: str | None = None
    correlation_id: str | None = None
    payload: dict


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    event_type: str
    service: str
    severity: str
    user_id: uuid.UUID | None
    resource_id: str | None
    resource_type: str | None
    correlation_id: str | None
    payload: dict
    expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogList(BaseModel):
    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int


class AuditLogFilter(BaseModel):
    event_type: str | None = None
    service: str | None = None
    severity: str | None = None
    resource_id: str | None = None
    from_timestamp: datetime | None = None
    to_timestamp: datetime | None = None

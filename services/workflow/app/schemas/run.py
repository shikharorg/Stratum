import uuid
from datetime import datetime

from pydantic import BaseModel


class RunRequest(BaseModel):
    workflow_id: uuid.UUID
    input_data: dict


class RunResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    workflow_id: uuid.UUID
    status: str
    input_data: dict
    output_data: dict | None
    error_message: str | None
    checkpoint_id: str | None
    started_at: datetime | None
    completed_at: datetime | None
    latency_ms: int | None
    extra_metadata: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class RunList(BaseModel):
    items: list[RunResponse]
    total: int
    page: int
    page_size: int

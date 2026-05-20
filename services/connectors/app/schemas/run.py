import uuid
from datetime import datetime

from pydantic import BaseModel


class ConnectorRunResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    connector_id: uuid.UUID
    run_type: str
    status: str
    items_processed: int
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    extra_metadata: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class ConnectorRunList(BaseModel):
    items: list[ConnectorRunResponse]
    total: int
    page: int
    page_size: int

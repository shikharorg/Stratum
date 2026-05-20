import uuid
from datetime import datetime

from pydantic import BaseModel


class ConnectorCreate(BaseModel):
    name: str
    connector_type: str
    credentials: dict
    webhook_secret: str | None = None
    sync_config: dict = {}
    extra_metadata: dict = {}


class ConnectorResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    connector_type: str
    is_active: bool
    webhook_secret: str | None
    sync_config: dict
    extra_metadata: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConnectorList(BaseModel):
    items: list[ConnectorResponse]
    total: int
    page: int
    page_size: int

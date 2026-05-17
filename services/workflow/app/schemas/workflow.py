import uuid
from datetime import datetime

from pydantic import BaseModel


class WorkflowCreate(BaseModel):
    name: str
    description: str | None = None
    graph_definition: dict
    extra_metadata: dict = {}


class WorkflowResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    description: str | None
    graph_definition: dict
    is_active: bool
    version: int
    extra_metadata: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkflowList(BaseModel):
    items: list[WorkflowResponse]
    total: int
    page: int
    page_size: int

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DocumentCreate(BaseModel):
    tenant_id: uuid.UUID
    name: str
    source_type: str
    source_url: str | None = None
    extra_metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    source_type: str
    source_url: str | None
    status: str
    error_message: str | None
    file_size: int | None
    page_count: int | None
    chunk_count: int | None
    extra_metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class DocumentList(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int

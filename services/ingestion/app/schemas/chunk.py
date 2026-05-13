import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    document_id: uuid.UUID
    qdrant_id: uuid.UUID
    chunk_index: int
    text: str
    token_count: int | None
    source_type: str
    section_title: str | None
    extra_metadata: dict[str, Any]
    created_at: datetime

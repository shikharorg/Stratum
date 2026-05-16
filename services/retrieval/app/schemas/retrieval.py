import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class RetrievalRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4096)
    source_filter: str | None = Field(None, description="Filter by source_type (e.g. 'pdf', 'url')")
    top_k: int = Field(5, ge=1, le=20)
    include_generation: bool = True


class ChunkResult(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    text: str
    score: float
    source_type: str
    source_url: str | None


class RetrievalResult(BaseModel):
    answer: str
    grounding_passed: bool
    chunks: list[ChunkResult]
    latency_ms: float


class RetrievalResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    query: str
    result: RetrievalResult
    created_at: datetime

    model_config = {"from_attributes": True}

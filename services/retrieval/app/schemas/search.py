import uuid

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4096)
    source_filter: str | None = None
    limit: int = Field(20, ge=1, le=100)


class SearchResult(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    text: str
    dense_score: float
    sparse_score: float
    rrf_score: float
    combined_score: float = 0.0
    source_type: str
    source_url: str | None

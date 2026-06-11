from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EvaluateRequest(BaseModel):
    query: str
    answer: str
    contexts: list[str]
    retrieval_log_id: Optional[str] = None
    tenant_id: str


class EvaluateResponse(BaseModel):
    id: str
    status: str
    faithfulness: Optional[float]
    answer_relevancy: Optional[float]
    context_precision: Optional[float]
    overall_score: Optional[float]
    error_message: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class EvaluationListResponse(BaseModel):
    items: list[EvaluateResponse]
    total: int
    page: int
    page_size: int

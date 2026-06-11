import uuid

from sqlalchemy import Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from stratum_libs.models.base import Base


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    retrieval_log_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    contexts: Mapped[list] = mapped_column(JSONB, nullable=False)
    faithfulness: Mapped[float | None] = mapped_column(Float, nullable=True)
    answer_relevancy: Mapped[float | None] = mapped_column(Float, nullable=True)
    context_precision: Mapped[float | None] = mapped_column(Float, nullable=True)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

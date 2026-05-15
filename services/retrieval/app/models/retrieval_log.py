import uuid
from typing import Any

from sqlalchemy import Boolean, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from stratum_libs.models.base import Base


class RetrievalLog(Base):
    __tablename__ = "retrieval_logs"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    source_filter: Mapped[str | None] = mapped_column(String(50), nullable=True)
    chunks_retrieved: Mapped[int] = mapped_column(Integer, nullable=False)
    chunks_after_rerank: Mapped[int] = mapped_column(Integer, nullable=False)
    grounding_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    __table_args__ = (
        Index("ix_retrieval_logs_tenant_created", "tenant_id", "created_at"),
    )

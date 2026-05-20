import uuid

from sqlalchemy import Boolean, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from stratum_libs.models.base import Base


class Connector(Base):
    __tablename__ = "connectors"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    connector_type: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    credentials: Mapped[dict] = mapped_column(JSONB, nullable=False)
    webhook_secret: Mapped[str | None] = mapped_column(String, nullable=True)
    sync_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    extra_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    __table_args__ = (
        Index("ix_connectors_tenant_id", "tenant_id"),
        Index("ix_connectors_connector_type", "connector_type"),
        Index("ix_connectors_is_active", "is_active"),
    )

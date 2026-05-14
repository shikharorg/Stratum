import uuid
from typing import Any

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document

logger = structlog.get_logger()


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, document_id: uuid.UUID, tenant_id: uuid.UUID) -> Document | None:
        result = await self._session.execute(
            select(Document).where(
                Document.id == document_id,
                Document.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_tenant(
        self, tenant_id: uuid.UUID, skip: int, limit: int
    ) -> tuple[list[Document], int]:
        count_result = await self._session.execute(
            select(func.count()).select_from(Document).where(Document.tenant_id == tenant_id)
        )
        total = count_result.scalar_one()

        rows_result = await self._session.execute(
            select(Document)
            .where(Document.tenant_id == tenant_id)
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        documents = list(rows_result.scalars().all())

        return documents, total

    async def create(
        self,
        tenant_id: uuid.UUID,
        name: str,
        source_type: str,
        source_url: str | None,
        extra_metadata: dict[str, Any],
    ) -> Document:
        document = Document(
            tenant_id=tenant_id,
            name=name,
            source_type=source_type,
            source_url=source_url,
            extra_metadata=extra_metadata,
        )
        self._session.add(document)
        await self._session.flush()
        await self._session.refresh(document)
        logger.info("document.created", document_id=str(document.id), tenant_id=str(tenant_id))
        return document

    async def update_status(
        self,
        document_id: uuid.UUID,
        tenant_id: uuid.UUID,
        status: str,
        error_message: str | None = None,
    ) -> None:
        values: dict[str, Any] = {"status": status}
        if error_message is not None:
            values["error_message"] = error_message

        await self._session.execute(
            update(Document)
            .where(Document.id == document_id, Document.tenant_id == tenant_id)
            .values(**values)
            .execution_options(synchronize_session=False)
        )

    async def update_chunk_count(
        self, document_id: uuid.UUID, tenant_id: uuid.UUID, count: int
    ) -> None:
        await self._session.execute(
            update(Document)
            .where(Document.id == document_id, Document.tenant_id == tenant_id)
            .values(chunk_count=count)
            .execution_options(synchronize_session=False)
        )

import uuid
from typing import Any

import structlog
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk

logger = structlog.get_logger()


class ChunkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_many(self, chunks: list[dict[str, Any]]) -> list[Chunk]:
        instances = [Chunk(**chunk) for chunk in chunks]
        self._session.add_all(instances)
        await self._session.flush()
        for instance in instances:
            await self._session.refresh(instance)
        return instances

    async def get_by_document(
        self, document_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> list[Chunk]:
        result = await self._session.execute(
            select(Chunk)
            .where(Chunk.document_id == document_id, Chunk.tenant_id == tenant_id)
            .order_by(Chunk.chunk_index.asc())
        )
        return list(result.scalars().all())

    async def delete_by_document(
        self, document_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> None:
        await self._session.execute(
            delete(Chunk)
            .where(Chunk.document_id == document_id, Chunk.tenant_id == tenant_id)
            .execution_options(synchronize_session=False)
        )

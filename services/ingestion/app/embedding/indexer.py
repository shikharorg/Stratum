import uuid

import structlog
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.chunking.base import ChunkData
from app.core.config import settings
from app.embedding.encoder import EmbeddingEncoder

logger = structlog.get_logger()


class QdrantIndexer:
    def __init__(self) -> None:
        self._client = AsyncQdrantClient(url=settings.QDRANT_URL)
        self.collection_name = settings.QDRANT_COLLECTION

    async def ensure_collection(self, encoder: EmbeddingEncoder) -> None:
        exists = await self._client.collection_exists(collection_name=self.collection_name)
        if exists:
            return

        vector_size = len(encoder.encode(["__init__"])[0])
        await self._client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        logger.info(
            "indexer.collection_created",
            collection=self.collection_name,
            vector_size=vector_size,
        )

    async def index_chunks(
        self,
        chunks: list[ChunkData],
        embeddings: list[list[float]],
        document_id: str,
        tenant_id: str,
        source_type: str,
        source_url: str | None,
    ) -> list[str]:
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"chunk count {len(chunks)} does not match embedding count {len(embeddings)}"
            )

        points: list[PointStruct] = []
        for chunk, vector in zip(chunks, embeddings):
            if chunk.qdrant_id is None:
                chunk.qdrant_id = str(uuid.uuid4())

            points.append(
                PointStruct(
                    id=chunk.qdrant_id,
                    vector=vector,
                    payload={
                        "tenant_id": tenant_id,
                        "document_id": document_id,
                        "source_type": source_type,
                        "source_url": source_url,
                        "chunk_index": chunk.chunk_index,
                        "section_title": chunk.section_title,
                        "token_count": chunk.token_count,
                        "extra_metadata": chunk.extra_metadata,
                    },
                )
            )

        await self._client.upsert(
            collection_name=self.collection_name,
            points=points,
        )
        logger.info(
            "indexer.chunks_upserted",
            collection=self.collection_name,
            document_id=document_id,
            tenant_id=tenant_id,
            count=len(points),
        )

        return [chunk.qdrant_id for chunk in chunks]  # type: ignore[return-value]

    async def delete_by_document(self, document_id: str, tenant_id: str) -> None:
        await self._client.delete(
            collection_name=self.collection_name,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id),
                        ),
                        FieldCondition(
                            key="tenant_id",
                            match=MatchValue(value=tenant_id),
                        ),
                    ]
                )
            ),
        )
        logger.info(
            "indexer.document_deleted",
            collection=self.collection_name,
            document_id=document_id,
            tenant_id=tenant_id,
        )

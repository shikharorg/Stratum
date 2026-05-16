import asyncio
import uuid

import structlog
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    FieldCondition,
    Filter,
    MatchValue,
    SparseVector,
)

from app.schemas.search import SearchResult

logger = structlog.get_logger()

_RRF_K = 60


class HybridSearcher:
    def __init__(self, client: AsyncQdrantClient, collection: str) -> None:
        self._client = client
        self._collection = collection

    async def search(
        self,
        query_vector: list[float],
        sparse_vector: dict,
        tenant_id: str,
        source_type: str | None,
        top_k: int = 20,
    ) -> list[SearchResult]:
        must = [FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id))]
        if source_type:
            must.append(FieldCondition(key="source_type", match=MatchValue(value=source_type)))

        query_filter = Filter(must=must)

        dense_response, sparse_response = await asyncio.gather(
            self._client.query_points(
                collection_name=self._collection,
                query=query_vector,
                using="dense",
                query_filter=query_filter,
                limit=top_k,
                with_payload=True,
            ),
            self._client.query_points(
                collection_name=self._collection,
                query=SparseVector(
                    indices=sparse_vector["indices"],
                    values=sparse_vector["values"],
                ),
                using="sparse",
                query_filter=query_filter,
                limit=top_k,
                with_payload=True,
            ),
        )

        dense_results = dense_response.points
        sparse_results = sparse_response.points

        logger.info(
            "searcher.results",
            dense_count=len(dense_results),
            sparse_count=len(sparse_results),
            tenant_id=tenant_id,
        )

        return self._rrf_merge(dense_results, sparse_results, top_k)

    def _rrf_merge(
        self,
        dense_results: list,
        sparse_results: list,
        top_k: int,
    ) -> list[SearchResult]:
        rrf_scores: dict[str, float] = {}
        dense_scores: dict[str, float] = {}
        sparse_scores: dict[str, float] = {}
        payloads: dict[str, dict] = {}

        for rank, point in enumerate(dense_results):
            pid = str(point.id)
            rrf_scores[pid] = rrf_scores.get(pid, 0.0) + 1.0 / (_RRF_K + rank + 1)
            dense_scores[pid] = float(point.score)
            if point.payload:
                payloads[pid] = point.payload

        for rank, point in enumerate(sparse_results):
            pid = str(point.id)
            rrf_scores[pid] = rrf_scores.get(pid, 0.0) + 1.0 / (_RRF_K + rank + 1)
            sparse_scores[pid] = float(point.score)
            if point.payload and pid not in payloads:
                payloads[pid] = point.payload

        sorted_ids = sorted(rrf_scores, key=lambda x: rrf_scores[x], reverse=True)[:top_k]

        results: list[SearchResult] = []
        for pid in sorted_ids:
            payload = payloads.get(pid, {})
            doc_id_raw = payload.get("document_id", str(uuid.uuid4()))
            results.append(
                SearchResult(
                    chunk_id=uuid.UUID(pid),
                    document_id=uuid.UUID(doc_id_raw),
                    text=payload.get("text", ""),
                    dense_score=dense_scores.get(pid, 0.0),
                    sparse_score=sparse_scores.get(pid, 0.0),
                    rrf_score=rrf_scores[pid],
                    combined_score=rrf_scores[pid],
                    source_type=payload.get("source_type", ""),
                    source_url=payload.get("source_url"),
                )
            )

        return results

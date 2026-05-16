from qdrant_client import AsyncQdrantClient

from stratum_libs.auth import get_request_context as get_request_context  # noqa: F401

from app.core.config import settings
from app.pipeline.encoder import QueryEncoder
from app.pipeline.reranker import Reranker
from app.pipeline.searcher import HybridSearcher

_encoder: QueryEncoder = QueryEncoder()
_reranker: Reranker = Reranker()
_qdrant_client: AsyncQdrantClient = AsyncQdrantClient(url=settings.QDRANT_URL)
_searcher: HybridSearcher = HybridSearcher(_qdrant_client, settings.QDRANT_COLLECTION)


def get_query_encoder() -> QueryEncoder:
    return _encoder


def get_reranker() -> Reranker:
    return _reranker


def get_searcher() -> HybridSearcher:
    return _searcher

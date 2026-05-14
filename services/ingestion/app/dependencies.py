from arq.connections import ArqRedis
from fastapi import Request

from stratum_libs.auth import RequestContext
from stratum_libs.auth import get_request_context as get_request_context  # noqa: F401

from app.embedding.encoder import EmbeddingEncoder
from app.embedding.indexer import QdrantIndexer

_encoder: EmbeddingEncoder = EmbeddingEncoder()
_indexer: QdrantIndexer = QdrantIndexer()


def get_encoder() -> EmbeddingEncoder:
    return _encoder


def get_indexer() -> QdrantIndexer:
    return _indexer


async def get_arq_pool(request: Request) -> ArqRedis:
    return request.app.state.arq_pool

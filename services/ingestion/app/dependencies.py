from arq.connections import ArqRedis
from fastapi import Request

from stratum_libs.auth import RequestContext
from stratum_libs.auth import get_request_context as get_request_context  # noqa: F401

from app.embedding.encoder import EmbeddingEncoder, SparseEncoder
from app.embedding.indexer import QdrantIndexer
from app.storage.minio_client import MinIOClient

_encoder: EmbeddingEncoder = EmbeddingEncoder()
_sparse_encoder: SparseEncoder = SparseEncoder()
_indexer: QdrantIndexer = QdrantIndexer()
_minio_client: MinIOClient = MinIOClient()


def get_encoder() -> EmbeddingEncoder:
    return _encoder


def get_sparse_encoder() -> SparseEncoder:
    return _sparse_encoder


def get_indexer() -> QdrantIndexer:
    return _indexer


def get_minio_client() -> MinIOClient:
    return _minio_client


async def get_arq_pool(request: Request) -> ArqRedis:
    return request.app.state.arq_pool

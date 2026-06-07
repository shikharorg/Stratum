import json
import uuid as uuid_module
from datetime import UTC, datetime
from typing import Any

import structlog
from arq.connections import RedisSettings

from app.chunking.preprocessor import preprocess_document
from app.chunking.router import DocumentRouter
from app.core.config import settings
from app.db import AsyncSessionFactory
from app.dependencies import get_encoder, get_indexer, get_minio_client, get_sparse_encoder
from app.repositories.chunk import ChunkRepository
from app.repositories.document import DocumentRepository

logger = structlog.get_logger()

_STREAM = "ingestion"


async def _publish(
    redis: Any,
    event_type: str,
    tenant_id: str,
    payload: dict[str, Any],
) -> None:
    event = {
        "event_id": str(uuid_module.uuid4()),
        "event_type": event_type,
        "tenant_id": tenant_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "payload": json.dumps(payload),
    }
    await redis.xadd(_STREAM, event)


async def process_document(
    ctx: dict[str, Any],
    *,
    document_id: str,
    tenant_id: str,
    object_key: str,
    source_type: str,
    source_url: str | None,
    filename: str,
) -> None:
    log = logger.bind(document_id=document_id, tenant_id=tenant_id)
    encoder = get_encoder()
    indexer = get_indexer()
    minio_client = get_minio_client()
    doc_uuid = uuid_module.UUID(document_id)
    tenant_uuid = uuid_module.UUID(tenant_id)

    async with AsyncSessionFactory() as init_session:
        await DocumentRepository(init_session).update_status(doc_uuid, tenant_uuid, "processing")
        await init_session.commit()

    log.info("document.processing.started", document_id=document_id, source_type=source_type)

    download_exc: Exception | None = None
    try:
        log.info("document.download.started", object_key=object_key)
        file_bytes = await minio_client.download_file(object_key)
    except Exception as exc:
        download_exc = exc
        log.error("document.download.failed", error=str(exc), object_key=object_key)
    finally:
        try:
            await minio_client.delete_file(object_key)
        except Exception:
            log.warning("worker.minio_cleanup_failed", key=object_key)

    if download_exc is not None:
        async with AsyncSessionFactory() as err_session:
            await DocumentRepository(err_session).update_status(
                doc_uuid, tenant_uuid, "failed", str(download_exc)
            )
            await err_session.commit()
        raise download_exc

    async with AsyncSessionFactory() as session:
        doc_repo = DocumentRepository(session)
        chunk_repo = ChunkRepository(session)

        try:
            result = preprocess_document(file_bytes, source_type, filename)

            router = DocumentRouter()
            chunks = router.route(source_type, result.content)

            if not chunks:
                await session.rollback()
                log.warning("worker.no_chunks_produced")
                try:
                    async with AsyncSessionFactory() as err_session:
                        await DocumentRepository(err_session).update_status(
                            doc_uuid, tenant_uuid, "failed", "No chunks produced after preprocessing"
                        )
                        await err_session.commit()
                except Exception:
                    log.exception("worker.no_chunks_status_update_failed")
                try:
                    await _publish(
                        ctx["redis"],
                        "ingestion.document.failed",
                        tenant_id,
                        {"document_id": document_id, "tenant_id": tenant_id, "error": "No chunks produced"},
                    )
                except Exception:
                    log.exception("worker.no_chunks_event_publish_failed")
                return

            chunk_texts = [c.text for c in chunks]
            embeddings = encoder.encode(chunk_texts)

            sparse_encoder = get_sparse_encoder()
            sparse_vectors = sparse_encoder.encode_sparse(chunk_texts)

            await indexer.ensure_collection(encoder)
            await indexer.index_chunks(
                chunks,
                embeddings,
                sparse_vectors,
                document_id,
                tenant_id,
                source_type,
                source_url,
            )

            chunk_dicts: list[dict[str, Any]] = [
                {
                    "tenant_id": tenant_uuid,
                    "document_id": doc_uuid,
                    "qdrant_id": uuid_module.UUID(chunk.qdrant_id),  # type: ignore[arg-type]
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                    "token_count": chunk.token_count,
                    "source_type": source_type,
                    "source_url": source_url,
                    "section_title": chunk.section_title,
                    "parent_chunk_id": (
                        uuid_module.UUID(chunk.parent_chunk_id) if chunk.parent_chunk_id else None
                    ),
                    "extra_metadata": chunk.extra_metadata,
                }
                for chunk in chunks
            ]
            await chunk_repo.create_many(chunk_dicts)

            await doc_repo.update_chunk_count(doc_uuid, tenant_uuid, len(chunks))
            await doc_repo.update_status(doc_uuid, tenant_uuid, "completed")
            await session.commit()

            log.info("document.processing.completed", document_id=document_id, chunk_count=len(chunks))

            await _publish(
                ctx["redis"],
                "ingestion.document.completed",
                tenant_id,
                {
                    "document_id": document_id,
                    "tenant_id": tenant_id,
                    "source_type": source_type,
                    "chunk_count": len(chunks),
                },
            )

        except Exception as exc:
            await session.rollback()
            log.error("document.processing.failed", document_id=document_id, error=str(exc))

            try:
                async with AsyncSessionFactory() as err_session:
                    await DocumentRepository(err_session).update_status(
                        doc_uuid, tenant_uuid, "failed", str(exc)
                    )
                    await err_session.commit()
            except Exception:
                log.exception("worker.failed_status_update_failed")

            try:
                await _publish(
                    ctx["redis"],
                    "ingestion.document.failed",
                    tenant_id,
                    {"document_id": document_id, "tenant_id": tenant_id, "error": str(exc)},
                )
            except Exception:
                log.exception("worker.failed_event_publish_failed")


class WorkerSettings:
    functions = [process_document]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    queue_name = "arq:queue:ingestion"
    max_jobs = 10
    job_timeout = 300

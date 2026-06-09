import uuid

import structlog
from arq.connections import ArqRedis
from fastapi import APIRouter, Depends, Form, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from stratum_libs.auth import RequestContext

from app.db import get_session
from app.dependencies import get_arq_pool, get_indexer, get_minio_client, get_request_context
from app.embedding.indexer import QdrantIndexer
from app.repositories.chunk import ChunkRepository
from app.repositories.document import DocumentRepository
from app.schemas.document import DocumentList, DocumentResponse
from app.storage.minio_client import MinIOClient

logger = structlog.get_logger()

_MAX_UPLOAD_BYTES = 50 * 1024 * 1024
_VALID_SOURCE_TYPES = frozenset({"pdf", "markdown", "code", "slack", "jira", "github"})

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile,
    source_type: str = Form(...),
    source_url: str | None = Form(default=None),
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
    arq_pool: ArqRedis = Depends(get_arq_pool),
    minio_client: MinIOClient = Depends(get_minio_client),
) -> DocumentResponse:
    if source_type not in _VALID_SOURCE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "type": "about:blank",
                "title": "Invalid source type",
                "status": 422,
                "detail": f"source_type must be one of: {', '.join(sorted(_VALID_SOURCE_TYPES))}",
            },
        )

    file_bytes = await file.read()

    if len(file_bytes) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "type": "about:blank",
                "title": "File too large",
                "status": 413,
                "detail": "File exceeds the 50MB limit",
            },
        )

    tenant_uuid = uuid.UUID(ctx.tenant_id)
    filename = file.filename or "unknown"
    content_type = file.content_type or "application/octet-stream"

    doc_repo = DocumentRepository(session)
    document = await doc_repo.create(
        tenant_id=tenant_uuid,
        name=filename,
        source_type=source_type,
        source_url=source_url,
        extra_metadata={},
    )
    await session.commit()

    object_key = f"{ctx.tenant_id}/{document.id}/{filename}"

    try:
        await minio_client.upload_file(object_key, file_bytes, content_type)
    except Exception as exc:
        logger.exception("documents.minio_upload_failed", document_id=str(document.id))
        try:
            await doc_repo.update_status(document.id, tenant_uuid, "failed", str(exc))
            await session.commit()
        except Exception:
            logger.exception("documents.failed_status_update_failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "type": "about:blank",
                "title": "Storage error",
                "status": 500,
                "detail": "Failed to upload file to object storage",
            },
        )

    try:
        await arq_pool.enqueue_job(
            "process_document",
            document_id=str(document.id),
            tenant_id=ctx.tenant_id,
            object_key=object_key,
            source_type=source_type,
            source_url=source_url,
            filename=filename,
            _queue_name="arq:queue:ingestion",
        )
    except Exception as exc:
        logger.exception("documents.arq_enqueue_failed", document_id=str(document.id))
        try:
            await minio_client.delete_file(object_key)
        except Exception:
            logger.exception("documents.minio_cleanup_failed", key=object_key)
        try:
            await doc_repo.update_status(document.id, tenant_uuid, "failed", str(exc))
            await session.commit()
        except Exception:
            logger.exception("documents.failed_status_update_failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "type": "about:blank",
                "title": "Queue error",
                "status": 500,
                "detail": "Failed to enqueue ingestion job",
            },
        )

    logger.info(
        "documents.upload_accepted",
        document_id=str(document.id),
        tenant_id=ctx.tenant_id,
        source_type=source_type,
        object_key=object_key,
    )

    return DocumentResponse.model_validate(document)


@router.get("", response_model=DocumentList)
async def list_documents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
) -> DocumentList:
    tenant_uuid = uuid.UUID(ctx.tenant_id)
    skip = (page - 1) * page_size
    doc_repo = DocumentRepository(session)
    documents, total = await doc_repo.get_by_tenant(tenant_uuid, skip=skip, limit=page_size)
    return DocumentList(
        items=[DocumentResponse.model_validate(d) for d in documents],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
) -> DocumentResponse:
    tenant_uuid = uuid.UUID(ctx.tenant_id)
    doc_repo = DocumentRepository(session)
    document = await doc_repo.get_by_id(document_id, tenant_uuid)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "about:blank",
                "title": "Document not found",
                "status": 404,
                "detail": f"Document {document_id} not found",
            },
        )
    return DocumentResponse.model_validate(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
    indexer: QdrantIndexer = Depends(get_indexer),
    minio_client: MinIOClient = Depends(get_minio_client),
) -> Response:
    tenant_uuid = uuid.UUID(ctx.tenant_id)
    doc_repo = DocumentRepository(session)
    chunk_repo = ChunkRepository(session)

    document = await doc_repo.get_by_id(document_id, tenant_uuid)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "about:blank",
                "title": "Document not found",
                "status": 404,
                "detail": f"Document {document_id} not found",
            },
        )

    object_key = f"{ctx.tenant_id}/{document_id}/{document.name}"
    try:
        await minio_client.delete_file(object_key)
    except Exception:
        pass

    try:
        await indexer.delete_by_document(str(document_id), ctx.tenant_id)
    except Exception:
        logger.warning("documents.qdrant_delete_failed", document_id=str(document_id))
    await chunk_repo.delete_by_document(document_id, tenant_uuid)
    await doc_repo.delete_by_id(document_id, tenant_uuid)
    await session.commit()

    logger.info(
        "documents.deleted",
        document_id=str(document_id),
        tenant_id=ctx.tenant_id,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)

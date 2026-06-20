import asyncio
from typing import Any

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.config import settings

router = APIRouter()


def _internal_headers(request: Request) -> dict[str, str]:
    payload: dict = getattr(request.state, "token_payload", None) or {}
    return {
        "x-request-id": getattr(request.state, "request_id", ""),
        "x-trace-id": getattr(request.state, "trace_id", ""),
        "x-tenant-id": payload.get("tenant_id", ""),
        "x-user-id": payload.get("user_id", ""),
        "x-user-roles": ",".join(payload.get("roles", [])),
    }


async def _get(client: httpx.AsyncClient, url: str, headers: dict | None = None) -> Any:
    try:
        resp = await client.get(url, headers=headers or {}, timeout=5.0)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


@router.get("/api/health/services")
async def health_services(request: Request) -> JSONResponse:
    client: httpx.AsyncClient = request.app.state.http_client
    redis = request.app.state.redis

    upstream_health = await asyncio.gather(
        _get(client, f"{settings.IDENTITY_SERVICE_URL}/health"),
        _get(client, f"{settings.INGESTION_SERVICE_URL}/health"),
        _get(client, f"{settings.RETRIEVAL_SERVICE_URL}/health"),
        _get(client, f"{settings.WORKFLOW_SERVICE_URL}/health"),
        _get(client, f"{settings.CONNECTORS_SERVICE_URL}/health"),
        _get(client, f"{settings.EVALUATION_SERVICE_URL}/health"),
        _get(client, f"{settings.OBSERVER_SERVICE_URL}/health"),
        _get(client, f"{settings.QDRANT_URL}/healthz"),
    )
    (
        identity_h, ingestion_h, retrieval_h, workflow_h,
        connectors_h, evaluation_h, observer_h, qdrant_h,
    ) = upstream_health

    redis_ok = False
    try:
        await redis.ping()
        redis_ok = True
    except Exception:
        pass

    def _healthy(data: Any) -> bool:
        return isinstance(data, dict) and data.get("status") == "healthy"

    api_ok = any(_healthy(h) for h in (identity_h, ingestion_h, retrieval_h, workflow_h))
    pg_ok = all(_healthy(h) for h in (identity_h, ingestion_h, workflow_h))
    qdrant_ok = qdrant_h is not None

    def _status(ok: bool) -> str:
        return "operational" if ok else "degraded"

    return JSONResponse({
        "services": [
            {"name": "API server",  "type": "FastAPI · Python",  "status": _status(api_ok),    "uptime": 99.9},
            {"name": "PostgreSQL",  "type": "Primary database",  "status": _status(pg_ok),     "uptime": 99.9},
            {"name": "Qdrant",      "type": "Vector store",      "status": _status(qdrant_ok), "uptime": 99.8},
            {"name": "Redis",       "type": "Cache · queue",     "status": _status(redis_ok),  "uptime": 100.0},
        ]
    })


@router.get("/api/dashboard/stats")
async def dashboard_stats(request: Request) -> JSONResponse:
    client: httpx.AsyncClient = request.app.state.http_client
    headers = _internal_headers(request)

    docs_data, users_data, connectors_data, wf_stats, search_stats = await asyncio.gather(
        _get(client, f"{settings.INGESTION_SERVICE_URL}/api/v1/ingestion/documents?page=1&page_size=100", headers),
        _get(client, f"{settings.IDENTITY_SERVICE_URL}/api/v1/identity/users?page_size=1", headers),
        _get(client, f"{settings.CONNECTORS_SERVICE_URL}/api/v1/connectors?page_size=100", headers),
        _get(client, f"{settings.WORKFLOW_SERVICE_URL}/api/v1/workflow/stats", headers),
        _get(client, f"{settings.RETRIEVAL_SERVICE_URL}/api/v1/retrieval/stats", headers),
    )

    doc_items: list[dict] = (docs_data or {}).get("items", [])
    total_documents: int = (docs_data or {}).get("total", 0)
    pending_documents: int = sum(
        1 for d in doc_items if d.get("status") not in ("completed",)
    )
    indexed_chunks: int = sum(
        (d.get("chunk_count") or 0) for d in doc_items if d.get("status") == "completed"
    )

    active_users: int = (users_data or {}).get("total", 0)

    connector_items: list[dict] = (connectors_data or {}).get("items", [])
    connector_names: list[str] = [c["name"] for c in connector_items if c.get("name")]

    workflow_runs: int = (wf_stats or {}).get("total_runs", 0)
    workflow_success_rate: float = (wf_stats or {}).get("success_rate", 0.0)

    searches: int = (search_stats or {}).get("searches_30d", 0)
    searches_this_week: int = (search_stats or {}).get("searches_7d", 0)

    return JSONResponse({
        "documents": total_documents,
        "pending_documents": pending_documents,
        "workflow_runs": workflow_runs,
        "workflow_success_rate": workflow_success_rate,
        "searches": searches,
        "searches_this_week": searches_this_week,
        "indexed_chunks": indexed_chunks,
        "active_users": active_users,
        "connectors": connector_names,
    })

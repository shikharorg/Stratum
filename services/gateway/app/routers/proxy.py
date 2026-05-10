from collections.abc import AsyncGenerator

import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse

from app.core.config import settings

router = APIRouter()

_ROUTE_MAP: dict[str, str] = {
    "/api/v1/identity": settings.IDENTITY_SERVICE_URL,
    "/api/v1/ingestion": settings.INGESTION_SERVICE_URL,
    "/api/v1/retrieval": settings.RETRIEVAL_SERVICE_URL,
    "/api/v1/workflow": settings.WORKFLOW_SERVICE_URL,
    "/api/v1/connectors": settings.CONNECTORS_SERVICE_URL,
    "/api/v1/evaluation": settings.EVALUATION_SERVICE_URL,
    "/api/v1/observer": settings.OBSERVER_SERVICE_URL,
}

_LONG_TIMEOUT_PREFIXES: frozenset[str] = frozenset({"/api/v1/ingestion", "/api/v1/workflow"})
_DEFAULT_TIMEOUT = 30.0
_LONG_TIMEOUT = 120.0

_HOP_BY_HOP_HEADERS: frozenset[str] = frozenset(
    {"host", "connection", "te", "trailers", "transfer-encoding", "upgrade"}
)


def _resolve(path: str) -> tuple[str, float] | None:
    for prefix, base_url in _ROUTE_MAP.items():
        if path.startswith(prefix):
            timeout = _LONG_TIMEOUT if prefix in _LONG_TIMEOUT_PREFIXES else _DEFAULT_TIMEOUT
            return base_url.rstrip("/") + path, timeout
    return None


async def _stream(upstream: httpx.Response) -> AsyncGenerator[bytes, None]:
    try:
        async for chunk in upstream.aiter_bytes():
            yield chunk
    finally:
        await upstream.aclose()


@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def proxy(request: Request, path: str) -> Response:
    full_path = request.url.path
    resolved = _resolve(full_path)

    if resolved is None:
        return Response(status_code=404)

    upstream_url, timeout = resolved
    if request.url.query:
        upstream_url += f"?{request.url.query}"

    token_payload: dict = request.state.token_payload
    injected = {
        "x-tenant-id": token_payload["tenant_id"],
        "x-user-id": token_payload["user_id"],
        "x-user-roles": ",".join(token_payload.get("roles", [])),
        "x-request-id": request.state.request_id,
        "x-trace-id": request.state.trace_id,
    }

    forward_headers = {
        k.lower(): v
        for k, v in request.headers.items()
        if k.lower() not in _HOP_BY_HOP_HEADERS
    }
    forward_headers.update(injected)

    client: httpx.AsyncClient = request.app.state.http_client

    try:
        upstream_request = client.build_request(
            method=request.method,
            url=upstream_url,
            headers=forward_headers,
            content=request.stream(),
        )
        upstream_response = await client.send(
            upstream_request,
            stream=True,
            timeout=timeout,
        )
    except httpx.ConnectError:
        return Response(status_code=502, content=b"Bad gateway: upstream unreachable")
    except httpx.TimeoutException:
        return Response(status_code=504, content=b"Gateway timeout")

    response_headers = {
        k: v
        for k, v in upstream_response.headers.items()
        if k.lower() not in _HOP_BY_HOP_HEADERS
    }

    return StreamingResponse(
        _stream(upstream_response),
        status_code=upstream_response.status_code,
        headers=response_headers,
        media_type=upstream_response.headers.get("content-type"),
    )

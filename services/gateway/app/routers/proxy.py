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

_HOP_BY_HOP_HEADERS: frozenset[str] = frozenset(
    {"host", "connection", "te", "trailers", "transfer-encoding", "upgrade"}
)


def _resolve(path: str) -> str | None:
    for prefix, base_url in _ROUTE_MAP.items():
        if path.startswith(prefix):
            upstream_path = "/api/v1" + path[len(prefix):]
            return base_url.rstrip("/") + upstream_path
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
    upstream_url = _resolve(full_path)

    if upstream_url is None:
        return Response(status_code=404)
    if request.url.query:
        upstream_url += f"?{request.url.query}"

    token_payload: dict | None = getattr(request.state, "token_payload", None)
    injected: dict[str, str] = {
        "x-request-id": request.state.request_id,
        "x-trace-id": request.state.trace_id,
    }
    if token_payload is not None:
        injected["x-tenant-id"] = token_payload["tenant_id"]
        injected["x-user-id"] = token_payload["user_id"]
        injected["x-user-roles"] = ",".join(token_payload.get("roles", []))

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

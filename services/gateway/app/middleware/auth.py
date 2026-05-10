from fastapi import HTTPException
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.rate_limit import check_rate_limit
from app.core.security import validate_jwt

_SKIP_AUTH_PATHS: frozenset[str] = frozenset({"/health"})


class AuthMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if scope.get("path", "") in _SKIP_AUTH_PATHS:
            await self.app(scope, receive, send)
            return

        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        authorization = headers.get("authorization")

        try:
            payload = validate_jwt(authorization)
        except HTTPException as exc:
            response = JSONResponse(
                status_code=exc.status_code,
                content={
                    "type": "about:blank",
                    "title": "Unauthorized",
                    "status": exc.status_code,
                    "detail": exc.detail,
                },
            )
            await response(scope, receive, send)
            return

        try:
            await check_rate_limit(payload["tenant_id"])
        except HTTPException as exc:
            response = JSONResponse(
                status_code=exc.status_code,
                content={
                    "type": "about:blank",
                    "title": "Too Many Requests",
                    "status": exc.status_code,
                    "detail": exc.detail,
                },
                headers=exc.headers or {},
            )
            await response(scope, receive, send)
            return

        scope.setdefault("state", {})
        scope["state"]["token_payload"] = payload

        await self.app(scope, receive, send)

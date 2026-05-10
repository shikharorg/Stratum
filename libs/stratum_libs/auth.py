from dataclasses import dataclass

from fastapi import Header, HTTPException, status


@dataclass
class RequestContext:
    tenant_id: str
    user_id: str
    roles: list[str]


async def get_request_context(
    x_tenant_id: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
    x_user_roles: str | None = Header(default=None),
) -> RequestContext:
    if not x_tenant_id or not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing required authentication headers",
        )
    roles = [r.strip() for r in x_user_roles.split(",")] if x_user_roles else []
    return RequestContext(tenant_id=x_tenant_id, user_id=x_user_id, roles=roles)

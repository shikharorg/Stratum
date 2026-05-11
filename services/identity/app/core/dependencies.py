from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from app.models.role import Role
from stratum_libs.auth import RequestContext, get_request_context

_ROLE_LEVELS: dict[str, int] = {
    "tenant_admin": 3,
    "editor": 2,
    "viewer": 1,
}


async def get_current_context(
    context: RequestContext = Depends(get_request_context),
) -> RequestContext:
    return context


def require_role(minimum_role: Role) -> Callable:
    required_level = _ROLE_LEVELS.get(minimum_role.value, 0)

    async def dependency(
        context: RequestContext = Depends(get_current_context),
    ) -> RequestContext:
        user_max_level = max(
            (_ROLE_LEVELS.get(r, 0) for r in context.roles),
            default=0,
        )
        if user_max_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return context

    return dependency

import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_context, require_role
from app.db import get_session
from app.models.role import Role
from app.schemas.user import UserCreate, UserList, UserResponse
from app.services.users import UserService
from stratum_libs.auth import RequestContext

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(
    context: RequestContext = Depends(get_current_context),
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    return await UserService(session).get_me(context)


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    data: UserCreate,
    context: RequestContext = Depends(require_role(Role.TENANT_ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    return await UserService(session).create_user(data, context)


@router.get("", response_model=UserList)
async def list_users(
    context: RequestContext = Depends(require_role(Role.TENANT_ADMIN)),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> UserList:
    return await UserService(session).list_users(context, page, page_size)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    context: RequestContext = Depends(require_role(Role.TENANT_ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> Response:
    await UserService(session).deactivate_user(user_id, context)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

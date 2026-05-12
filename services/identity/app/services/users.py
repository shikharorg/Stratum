import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User
from app.repositories.role import UserRoleRepository
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserList, UserResponse
from stratum_libs.auth import RequestContext


def _to_user_response(user: User, roles: list[Role]) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        roles=roles,
        tenant_id=user.tenant_id,
        created_at=user.created_at,
    )


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_me(self, context: RequestContext) -> UserResponse:
        user_id = uuid.UUID(context.user_id)
        tenant_id = uuid.UUID(context.tenant_id)

        user_repo = UserRepository(self._session)
        user = await user_repo.get_with_roles(user_id, tenant_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        roles = [ur.role for ur in user.roles]
        return _to_user_response(user, roles)

    async def create_user(
        self, data: UserCreate, context: RequestContext
    ) -> UserResponse:
        try:
            tenant_id = uuid.UUID(context.tenant_id)
            user_repo = UserRepository(self._session)
            role_repo = UserRoleRepository(self._session)

            if await user_repo.get_by_email_and_tenant(data.email, tenant_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already exists",
                )

            user = await user_repo.create(
                tenant_id=tenant_id,
                email=data.email,
                hashed_password=hash_password(data.password),
                full_name=data.full_name,
            )

            await role_repo.assign_role(user.id, tenant_id, data.role)
            roles = await role_repo.get_roles_for_user(user.id, tenant_id)

            await self._session.commit()
            return _to_user_response(user, roles)

        except Exception:
            await self._session.rollback()
            raise

    async def list_users(
        self, context: RequestContext, page: int, page_size: int
    ) -> UserList:
        tenant_id = uuid.UUID(context.tenant_id)
        user_repo = UserRepository(self._session)
        role_repo = UserRoleRepository(self._session)

        skip = (page - 1) * page_size
        users, total = await user_repo.list_by_tenant(tenant_id, skip, page_size)

        items: list[UserResponse] = []
        for user in users:
            roles = await role_repo.get_roles_for_user(user.id, tenant_id)
            items.append(_to_user_response(user, roles))

        return UserList(items=items, total=total, page=page, page_size=page_size)

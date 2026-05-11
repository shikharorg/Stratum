import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role, UserRole


class UserRoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def assign_role(
        self, user_id: uuid.UUID, tenant_id: uuid.UUID, role: Role
    ) -> UserRole:
        user_role = UserRole(user_id=user_id, tenant_id=tenant_id, role=role)
        self._session.add(user_role)
        await self._session.flush()
        await self._session.refresh(user_role)
        return user_role

    async def get_roles_for_user(
        self, user_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> list[Role]:
        result = await self._session.execute(
            select(UserRole.role).where(
                UserRole.user_id == user_id,
                UserRole.tenant_id == tenant_id,
            )
        )
        return list(result.scalars().all())

    async def remove_role(
        self, user_id: uuid.UUID, tenant_id: uuid.UUID, role: Role
    ) -> None:
        await self._session.execute(
            delete(UserRole)
            .where(
                UserRole.user_id == user_id,
                UserRole.tenant_id == tenant_id,
                UserRole.role == role,
            )
            .execution_options(synchronize_session=False)
        )

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID, tenant_id: uuid.UUID) -> User | None:
        result = await self._session.execute(
            select(User).where(User.id == user_id, User.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email_and_tenant(
        self, email: str, tenant_id: uuid.UUID
    ) -> User | None:
        result = await self._session.execute(
            select(User).where(User.email == email, User.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        tenant_id: uuid.UUID,
        email: str,
        hashed_password: str,
        full_name: str,
    ) -> User:
        user = User(
            tenant_id=tenant_id,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
        )
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def list_by_tenant(
        self, tenant_id: uuid.UUID, skip: int, limit: int
    ) -> tuple[list[User], int]:
        count_result = await self._session.execute(
            select(func.count()).select_from(User).where(User.tenant_id == tenant_id)
        )
        total: int = count_result.scalar_one()

        items_result = await self._session.execute(
            select(User)
            .where(User.tenant_id == tenant_id)
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(items_result.scalars().all()), total

    async def get_with_roles(
        self, user_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> User | None:
        result = await self._session.execute(
            select(User)
            .where(User.id == user_id, User.tenant_id == tenant_id)
            .options(selectinload(User.roles))
        )
        return result.scalar_one_or_none()

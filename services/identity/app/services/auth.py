from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    sha256_token,
    verify_password,
)
from app.models.role import Role
from app.repositories.role import UserRoleRepository
from app.repositories.tenant import TenantRepository
from app.repositories.token import TokenRepository
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest

_INVALID_CREDENTIALS = "Invalid credentials"
_INVALID_TOKEN = "Invalid or expired refresh token"


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _make_login_response(self, access_token: str) -> LoginResponse:
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def _store_refresh_token(
        self,
        token_repo: TokenRepository,
        user_id,
        tenant_id,
        raw_token: str,
    ) -> None:
        expires_at = datetime.now(UTC) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        await token_repo.create_refresh_token(
            user_id=user_id,
            tenant_id=tenant_id,
            token_hash=sha256_token(raw_token),
            expires_at=expires_at,
        )

    async def register(self, data: RegisterRequest) -> tuple[LoginResponse, str]:
        try:
            tenant_repo = TenantRepository(self._session)
            user_repo = UserRepository(self._session)
            role_repo = UserRoleRepository(self._session)
            token_repo = TokenRepository(self._session)

            if await tenant_repo.get_by_slug(data.tenant_slug):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Tenant slug already exists",
                )

            tenant = await tenant_repo.create(
                name=data.tenant_name, slug=data.tenant_slug
            )

            if await user_repo.get_by_email_and_tenant(data.admin_email, tenant.id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already exists",
                )

            user = await user_repo.create(
                tenant_id=tenant.id,
                email=data.admin_email,
                hashed_password=hash_password(data.admin_password),
                full_name=data.admin_full_name,
            )

            await role_repo.assign_role(user.id, tenant.id, Role.TENANT_ADMIN)

            raw_token = create_refresh_token()
            await self._store_refresh_token(token_repo, user.id, tenant.id, raw_token)

            access_token = create_access_token(
                tenant_id=str(tenant.id),
                user_id=str(user.id),
                roles=[Role.TENANT_ADMIN.value],
            )

            await self._session.commit()
            return self._make_login_response(access_token), raw_token

        except Exception:
            await self._session.rollback()
            raise

    async def login(self, data: LoginRequest) -> tuple[LoginResponse, str]:
        try:
            tenant_repo = TenantRepository(self._session)
            user_repo = UserRepository(self._session)
            role_repo = UserRoleRepository(self._session)
            token_repo = TokenRepository(self._session)

            tenant = await tenant_repo.get_by_slug(data.tenant_slug)
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=_INVALID_CREDENTIALS,
                )

            user = await user_repo.get_by_email_and_tenant(data.email, tenant.id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=_INVALID_CREDENTIALS,
                )

            if not verify_password(data.password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=_INVALID_CREDENTIALS,
                )

            roles = await role_repo.get_roles_for_user(user.id, tenant.id)
            roles_str = [r.value for r in roles]

            raw_token = create_refresh_token()
            await self._store_refresh_token(token_repo, user.id, tenant.id, raw_token)

            access_token = create_access_token(
                tenant_id=str(tenant.id),
                user_id=str(user.id),
                roles=roles_str,
            )

            await self._session.commit()
            return self._make_login_response(access_token), raw_token

        except Exception:
            await self._session.rollback()
            raise

    async def refresh(self, token: str) -> tuple[LoginResponse, str]:
        try:
            token_repo = TokenRepository(self._session)
            role_repo = UserRoleRepository(self._session)

            hashed = sha256_token(token)
            record = await token_repo.get_by_hash(hashed)

            if (
                not record
                or record.revoked
                or record.expires_at <= datetime.now(UTC)
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=_INVALID_TOKEN,
                )

            roles = await role_repo.get_roles_for_user(record.user_id, record.tenant_id)
            roles_str = [r.value for r in roles]

            await token_repo.revoke(record.id)

            raw_token = create_refresh_token()
            await self._store_refresh_token(
                token_repo, record.user_id, record.tenant_id, raw_token
            )

            access_token = create_access_token(
                tenant_id=str(record.tenant_id),
                user_id=str(record.user_id),
                roles=roles_str,
            )

            await self._session.commit()
            return self._make_login_response(access_token), raw_token

        except Exception:
            await self._session.rollback()
            raise

    async def logout(self, token: str) -> None:
        try:
            token_repo = TokenRepository(self._session)
            hashed = sha256_token(token)
            record = await token_repo.get_by_hash(hashed)
            if record:
                await token_repo.revoke(record.id)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

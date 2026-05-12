import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.tenant import TenantRepository
from app.schemas.tenant import TenantResponse
from stratum_libs.auth import RequestContext


class TenantService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_me(self, context: RequestContext) -> TenantResponse:
        tenant_id = uuid.UUID(context.tenant_id)
        tenant_repo = TenantRepository(self._session)
        tenant = await tenant_repo.get_by_id(tenant_id)

        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found",
            )

        return TenantResponse.model_validate(tenant)

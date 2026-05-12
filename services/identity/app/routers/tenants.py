from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_context
from app.db import get_session
from app.schemas.tenant import TenantResponse
from app.services.tenants import TenantService
from stratum_libs.auth import RequestContext

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("/me", response_model=TenantResponse)
async def get_me(
    context: RequestContext = Depends(get_current_context),
    session: AsyncSession = Depends(get_session),
) -> TenantResponse:
    return await TenantService(session).get_me(context)

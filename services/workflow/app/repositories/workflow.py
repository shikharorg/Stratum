import uuid

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import Workflow

logger = structlog.get_logger()


class WorkflowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, workflow_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> Workflow | None:
        result = await self._session.execute(
            select(Workflow).where(
                Workflow.id == workflow_id,
                Workflow.tenant_id == tenant_id,
            )
        )
        workflow = result.scalar_one_or_none()
        logger.debug(
            "workflow.get_by_id",
            workflow_id=str(workflow_id),
            tenant_id=str(tenant_id),
            found=workflow is not None,
        )
        return workflow

    async def get_by_tenant(
        self, tenant_id: uuid.UUID, skip: int, limit: int
    ) -> tuple[list[Workflow], int]:
        count_result = await self._session.execute(
            select(func.count())
            .select_from(Workflow)
            .where(Workflow.tenant_id == tenant_id)
        )
        total = count_result.scalar_one()

        rows_result = await self._session.execute(
            select(Workflow)
            .where(Workflow.tenant_id == tenant_id)
            .offset(skip)
            .limit(limit)
        )
        workflows = list(rows_result.scalars().all())
        logger.debug(
            "workflow.get_by_tenant",
            tenant_id=str(tenant_id),
            total=total,
            returned=len(workflows),
        )
        return workflows, total

    async def create(
        self,
        tenant_id: uuid.UUID,
        name: str,
        description: str | None,
        graph_definition: dict,
        extra_metadata: dict,
    ) -> Workflow:
        workflow = Workflow(
            tenant_id=tenant_id,
            name=name,
            description=description,
            graph_definition=graph_definition,
            extra_metadata=extra_metadata,
        )
        self._session.add(workflow)
        await self._session.flush()
        await self._session.refresh(workflow)
        logger.info(
            "workflow.created",
            workflow_id=str(workflow.id),
            tenant_id=str(tenant_id),
        )
        return workflow

    async def deactivate(self, workflow_id: uuid.UUID, tenant_id: uuid.UUID) -> None:
        await self._session.execute(
            update(Workflow)
            .where(Workflow.id == workflow_id, Workflow.tenant_id == tenant_id)
            .values(is_active=False)
            .execution_options(synchronize_session=False)
        )
        logger.info(
            "workflow.deactivated",
            workflow_id=str(workflow_id),
            tenant_id=str(tenant_id),
        )

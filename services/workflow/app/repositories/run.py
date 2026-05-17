import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow_run import WorkflowRun

logger = structlog.get_logger()


class WorkflowRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, run_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> WorkflowRun | None:
        result = await self._session.execute(
            select(WorkflowRun).where(
                WorkflowRun.id == run_id,
                WorkflowRun.tenant_id == tenant_id,
            )
        )
        run = result.scalar_one_or_none()
        logger.debug(
            "workflow_run.get_by_id",
            run_id=str(run_id),
            tenant_id=str(tenant_id),
            found=run is not None,
        )
        return run

    async def get_by_workflow(
        self,
        workflow_id: uuid.UUID,
        tenant_id: uuid.UUID,
        skip: int,
        limit: int,
    ) -> tuple[list[WorkflowRun], int]:
        count_result = await self._session.execute(
            select(func.count())
            .select_from(WorkflowRun)
            .where(
                WorkflowRun.workflow_id == workflow_id,
                WorkflowRun.tenant_id == tenant_id,
            )
        )
        total = count_result.scalar_one()

        rows_result = await self._session.execute(
            select(WorkflowRun)
            .where(
                WorkflowRun.workflow_id == workflow_id,
                WorkflowRun.tenant_id == tenant_id,
            )
            .order_by(WorkflowRun.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        runs = list(rows_result.scalars().all())
        logger.debug(
            "workflow_run.get_by_workflow",
            workflow_id=str(workflow_id),
            tenant_id=str(tenant_id),
            total=total,
            returned=len(runs),
        )
        return runs, total

    async def create(
        self,
        tenant_id: uuid.UUID,
        workflow_id: uuid.UUID,
        input_data: dict,
        extra_metadata: dict,
    ) -> WorkflowRun:
        run = WorkflowRun(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            status="pending",
            input_data=input_data,
            extra_metadata=extra_metadata,
        )
        self._session.add(run)
        await self._session.flush()
        await self._session.refresh(run)
        logger.info(
            "workflow_run.created",
            run_id=str(run.id),
            workflow_id=str(workflow_id),
            tenant_id=str(tenant_id),
        )
        return run

    async def update_status(
        self,
        run_id: uuid.UUID,
        tenant_id: uuid.UUID,
        status: str,
        error_message: str | None = None,
        started_at: datetime | None = None,
    ) -> None:
        values: dict = {"status": status}
        if error_message is not None:
            values["error_message"] = error_message
        if started_at is not None:
            values["started_at"] = started_at
        await self._session.execute(
            update(WorkflowRun)
            .where(WorkflowRun.id == run_id, WorkflowRun.tenant_id == tenant_id)
            .values(**values)
            .execution_options(synchronize_session=False)
        )
        logger.info(
            "workflow_run.status_updated",
            run_id=str(run_id),
            tenant_id=str(tenant_id),
            status=status,
        )

    async def update_output(
        self,
        run_id: uuid.UUID,
        tenant_id: uuid.UUID,
        output_data: dict,
        latency_ms: int,
    ) -> None:
        await self._session.execute(
            update(WorkflowRun)
            .where(WorkflowRun.id == run_id, WorkflowRun.tenant_id == tenant_id)
            .values(
                status="completed",
                output_data=output_data,
                completed_at=datetime.now(timezone.utc),
                latency_ms=latency_ms,
            )
            .execution_options(synchronize_session=False)
        )
        logger.info(
            "workflow_run.output_updated",
            run_id=str(run_id),
            tenant_id=str(tenant_id),
            latency_ms=latency_ms,
        )

    async def update_checkpoint(
        self,
        run_id: uuid.UUID,
        tenant_id: uuid.UUID,
        checkpoint_id: str,
    ) -> None:
        await self._session.execute(
            update(WorkflowRun)
            .where(WorkflowRun.id == run_id, WorkflowRun.tenant_id == tenant_id)
            .values(checkpoint_id=checkpoint_id)
            .execution_options(synchronize_session=False)
        )
        logger.info(
            "workflow_run.checkpoint_updated",
            run_id=str(run_id),
            tenant_id=str(tenant_id),
            checkpoint_id=checkpoint_id,
        )

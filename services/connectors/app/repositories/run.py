import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.connector_run import ConnectorRun

logger = structlog.get_logger()


class ConnectorRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, run_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> ConnectorRun | None:
        result = await self._session.execute(
            select(ConnectorRun).where(
                ConnectorRun.id == run_id,
                ConnectorRun.tenant_id == tenant_id,
            )
        )
        run = result.scalar_one_or_none()
        logger.debug(
            "connector_run.get_by_id",
            run_id=str(run_id),
            tenant_id=str(tenant_id),
            found=run is not None,
        )
        return run

    async def get_by_connector(
        self,
        connector_id: uuid.UUID,
        tenant_id: uuid.UUID,
        skip: int,
        limit: int,
    ) -> tuple[list[ConnectorRun], int]:
        count_result = await self._session.execute(
            select(func.count())
            .select_from(ConnectorRun)
            .where(
                ConnectorRun.connector_id == connector_id,
                ConnectorRun.tenant_id == tenant_id,
            )
        )
        total = count_result.scalar_one()

        rows_result = await self._session.execute(
            select(ConnectorRun)
            .where(
                ConnectorRun.connector_id == connector_id,
                ConnectorRun.tenant_id == tenant_id,
            )
            .order_by(ConnectorRun.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        runs = list(rows_result.scalars().all())
        logger.debug(
            "connector_run.get_by_connector",
            connector_id=str(connector_id),
            tenant_id=str(tenant_id),
            total=total,
            returned=len(runs),
        )
        return runs, total

    async def create(
        self,
        tenant_id: uuid.UUID,
        connector_id: uuid.UUID,
        run_type: str,
        extra_metadata: dict,
    ) -> ConnectorRun:
        run = ConnectorRun(
            tenant_id=tenant_id,
            connector_id=connector_id,
            run_type=run_type,
            status="running",
            started_at=datetime.now(UTC),
            extra_metadata=extra_metadata,
        )
        self._session.add(run)
        await self._session.flush()
        await self._session.refresh(run)
        logger.info(
            "connector_run.created",
            run_id=str(run.id),
            connector_id=str(connector_id),
            tenant_id=str(tenant_id),
            run_type=run_type,
        )
        return run

    async def complete(
        self,
        run_id: uuid.UUID,
        tenant_id: uuid.UUID,
        items_processed: int,
    ) -> None:
        await self._session.execute(
            update(ConnectorRun)
            .where(ConnectorRun.id == run_id, ConnectorRun.tenant_id == tenant_id)
            .values(
                status="completed",
                completed_at=datetime.now(UTC),
                items_processed=items_processed,
            )
            .execution_options(synchronize_session=False)
        )
        logger.info(
            "connector_run.completed",
            run_id=str(run_id),
            tenant_id=str(tenant_id),
            items_processed=items_processed,
        )

    async def fail(
        self,
        run_id: uuid.UUID,
        tenant_id: uuid.UUID,
        error_message: str,
    ) -> None:
        await self._session.execute(
            update(ConnectorRun)
            .where(ConnectorRun.id == run_id, ConnectorRun.tenant_id == tenant_id)
            .values(
                status="failed",
                completed_at=datetime.now(UTC),
                error_message=error_message,
            )
            .execution_options(synchronize_session=False)
        )
        logger.info(
            "connector_run.failed",
            run_id=str(run_id),
            tenant_id=str(tenant_id),
            error_message=error_message,
        )

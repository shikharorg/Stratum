import uuid

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.connector import Connector

logger = structlog.get_logger()


class ConnectorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, connector_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> Connector | None:
        result = await self._session.execute(
            select(Connector).where(
                Connector.id == connector_id,
                Connector.tenant_id == tenant_id,
            )
        )
        connector = result.scalar_one_or_none()
        logger.debug(
            "connector.get_by_id",
            connector_id=str(connector_id),
            tenant_id=str(tenant_id),
            found=connector is not None,
        )
        return connector

    async def get_by_tenant(
        self, tenant_id: uuid.UUID, skip: int, limit: int
    ) -> tuple[list[Connector], int]:
        count_result = await self._session.execute(
            select(func.count())
            .select_from(Connector)
            .where(Connector.tenant_id == tenant_id, Connector.is_active == True)  # noqa: E712
        )
        total = count_result.scalar_one()

        rows_result = await self._session.execute(
            select(Connector)
            .where(Connector.tenant_id == tenant_id, Connector.is_active == True)  # noqa: E712
            .offset(skip)
            .limit(limit)
        )
        connectors = list(rows_result.scalars().all())
        logger.debug(
            "connector.get_by_tenant",
            tenant_id=str(tenant_id),
            total=total,
            returned=len(connectors),
        )
        return connectors, total

    async def get_by_type(
        self, tenant_id: uuid.UUID, connector_type: str
    ) -> list[Connector]:
        result = await self._session.execute(
            select(Connector).where(
                Connector.tenant_id == tenant_id,
                Connector.connector_type == connector_type,
                Connector.is_active == True,  # noqa: E712
            )
        )
        connectors = list(result.scalars().all())
        logger.debug(
            "connector.get_by_type",
            tenant_id=str(tenant_id),
            connector_type=connector_type,
            returned=len(connectors),
        )
        return connectors

    async def create(
        self,
        tenant_id: uuid.UUID,
        name: str,
        connector_type: str,
        credentials: dict,
        webhook_secret: str | None,
        sync_config: dict,
        extra_metadata: dict,
    ) -> Connector:
        connector = Connector(
            tenant_id=tenant_id,
            name=name,
            connector_type=connector_type,
            credentials=credentials,
            webhook_secret=webhook_secret,
            sync_config=sync_config,
            extra_metadata=extra_metadata,
        )
        self._session.add(connector)
        await self._session.flush()
        await self._session.refresh(connector)
        logger.info(
            "connector.created",
            connector_id=str(connector.id),
            tenant_id=str(tenant_id),
            connector_type=connector_type,
        )
        return connector

    async def update_sync_cursor(
        self,
        connector_id: uuid.UUID,
        tenant_id: uuid.UUID,
        cursor: str,
        last_synced_at: str,
    ) -> None:
        await self._session.execute(
            update(Connector)
            .where(Connector.id == connector_id, Connector.tenant_id == tenant_id)
            .values(
                sync_config=Connector.sync_config.concat(
                    {"sync_cursor": cursor, "last_synced_at": last_synced_at}
                )
            )
            .execution_options(synchronize_session=False)
        )
        logger.info(
            "connector.sync_cursor_updated",
            connector_id=str(connector_id),
            tenant_id=str(tenant_id),
            last_synced_at=last_synced_at,
        )

    async def deactivate(
        self, connector_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> None:
        await self._session.execute(
            update(Connector)
            .where(Connector.id == connector_id, Connector.tenant_id == tenant_id)
            .values(is_active=False)
            .execution_options(synchronize_session=False)
        )
        logger.info(
            "connector.deactivated",
            connector_id=str(connector_id),
            tenant_id=str(tenant_id),
        )

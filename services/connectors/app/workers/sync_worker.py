from __future__ import annotations

import json
import uuid as uuid_module
from datetime import UTC, datetime
from typing import Any

import httpx
import structlog
from arq.connections import RedisSettings

from app.connectors.base import BaseConnector
from app.connectors.github import GitHubConnector
from app.connectors.jira import JiraConnector
from app.connectors.slack import SlackConnector
from app.core.config import settings
from app.crypto import decrypt_credentials
from app.db import AsyncSessionFactory
from app.repositories.connector import ConnectorRepository
from app.repositories.run import ConnectorRunRepository

logger = structlog.get_logger()

_STREAM = "connectors"


def add_connector_router(connector_type: str) -> type[BaseConnector]:
    match connector_type:
        case "slack":
            return SlackConnector
        case "jira":
            return JiraConnector
        case "github":
            return GitHubConnector
        case _:
            raise ValueError(f"Unknown connector type: {connector_type}")


async def _publish(
    redis: Any,
    event_type: str,
    tenant_id: str,
    payload: dict[str, Any],
) -> None:
    event = {
        "event_id": str(uuid_module.uuid4()),
        "event_type": event_type,
        "tenant_id": tenant_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "payload": json.dumps(payload),
    }
    await redis.xadd(_STREAM, event)


async def sync_connector(
    ctx: dict[str, Any],
    *,
    connector_id: str,
    tenant_id: str,
) -> None:
    log = logger.bind(connector_id=connector_id, tenant_id=tenant_id)
    connector_uuid = uuid_module.UUID(connector_id)
    tenant_uuid = uuid_module.UUID(tenant_id)

    async with AsyncSessionFactory() as session:
        connector_repo = ConnectorRepository(session)
        run_repo = ConnectorRunRepository(session)

        connector = await connector_repo.get_by_id(connector_uuid, tenant_uuid)
        if connector is None or not connector.is_active:
            log.warning("sync_worker.connector_not_found_or_inactive")
            return

        credentials = decrypt_credentials(connector.credentials)
        connector_class = add_connector_router(connector.connector_type)
        impl = connector_class(connector, credentials)

        run = await run_repo.create(
            tenant_id=tenant_uuid,
            connector_id=connector_uuid,
            run_type="sync",
            extra_metadata={},
        )
        await session.commit()

        try:
            items = await impl.fetch_items()
            formatted_items = [await impl.format_item(item) for item in items]
            items_ingested = 0

            async with httpx.AsyncClient(timeout=30.0) as client:
                for doc in formatted_items:
                    try:
                        response = await client.post(
                            f"{settings.INGESTION_SERVICE_URL}/api/v1/documents/ingest",
                            json={**doc, "tenant_id": tenant_id},
                            headers={
                                "X-Tenant-ID": tenant_id,
                                "X-User-ID": "connector-service",
                            },
                        )
                        response.raise_for_status()
                        items_ingested += 1
                    except Exception as exc:
                        log.warning("sync_worker.ingest_item_failed", error=str(exc))

            if items:
                new_cursor = str(items[-1].get("ts") or items[-1].get("id") or "")
                if new_cursor:
                    last_synced_at = datetime.now(UTC).isoformat()
                    await connector_repo.update_sync_cursor(
                        connector_uuid, tenant_uuid, new_cursor, last_synced_at
                    )

            await run_repo.complete(run.id, tenant_uuid, items_ingested)
            await session.commit()

            log.info("sync_worker.completed", items_ingested=items_ingested)

            try:
                await _publish(
                    ctx["redis"],
                    "connector.sync.completed",
                    tenant_id,
                    {"connector_id": connector_id, "tenant_id": tenant_id, "items_ingested": items_ingested},
                )
            except Exception:
                log.exception("sync_worker.publish_failed")

        except Exception as exc:
            log.exception("sync_worker.failed", error=str(exc))
            try:
                async with AsyncSessionFactory() as err_session:
                    await ConnectorRunRepository(err_session).fail(run.id, tenant_uuid, str(exc))
                    await err_session.commit()
            except Exception:
                log.exception("sync_worker.fail_status_update_failed")


class WorkerSettings:
    functions = [sync_connector]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs: int = 20
    job_timeout: int = 300

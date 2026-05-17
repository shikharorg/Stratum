import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

import asyncpg
import structlog
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata, CheckpointTuple

from app.core.config import settings

logger = structlog.get_logger()


class PostgresCheckpointer(BaseCheckpointSaver):
    def __init__(self, database_url: str) -> None:
        super().__init__()
        self._conn_str = database_url.replace("postgresql+asyncpg://", "postgresql://")

    async def _get_conn(self) -> asyncpg.Connection:
        conn = await asyncpg.connect(self._conn_str)
        await conn.set_type_codec("jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")
        return conn

    async def setup(self) -> None:
        conn = await self._get_conn()
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id TEXT PRIMARY KEY,
                    thread_id TEXT NOT NULL,
                    checkpoint JSONB NOT NULL,
                    metadata JSONB NOT NULL DEFAULT '{}',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            """)
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS ix_checkpoints_thread_id ON checkpoints (thread_id)"
            )
        finally:
            await conn.close()

    async def get(self, config: RunnableConfig) -> Checkpoint | None:
        tuple_ = await self.aget_tuple(config)
        return tuple_.checkpoint if tuple_ else None

    async def aget_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = config.get("configurable", {}).get("checkpoint_id")
        conn = await self._get_conn()
        try:
            if checkpoint_id:
                row = await conn.fetchrow(
                    "SELECT id, thread_id, checkpoint, metadata FROM checkpoints WHERE id = $1 AND thread_id = $2",
                    checkpoint_id,
                    thread_id,
                )
            else:
                row = await conn.fetchrow(
                    "SELECT id, thread_id, checkpoint, metadata FROM checkpoints WHERE thread_id = $1 ORDER BY created_at DESC LIMIT 1",
                    thread_id,
                )
            if row is None:
                return None
            return CheckpointTuple(
                config={"configurable": {"thread_id": row["thread_id"], "checkpoint_id": row["id"]}},
                checkpoint=row["checkpoint"],
                metadata=row["metadata"],
                parent_config=None,
            )
        finally:
            await conn.close()

    async def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: Any = None,
    ) -> RunnableConfig:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = checkpoint.get("id", str(uuid.uuid4()))
        conn = await self._get_conn()
        try:
            await conn.execute(
                """INSERT INTO checkpoints (id, thread_id, checkpoint, metadata)
                   VALUES ($1, $2, $3, $4)
                   ON CONFLICT (id) DO UPDATE SET checkpoint = $3, metadata = $4""",
                checkpoint_id,
                thread_id,
                checkpoint,
                metadata if metadata else {},
            )
        finally:
            await conn.close()
        logger.debug("checkpointer.put", thread_id=thread_id, checkpoint_id=checkpoint_id)
        return {"configurable": {"thread_id": thread_id, "checkpoint_id": checkpoint_id}}

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: Any = None,
    ) -> RunnableConfig:
        return await self.put(config, checkpoint, metadata, new_versions)

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: list[tuple[str, Any]],
        task_id: str,
    ) -> None:
        pass

    async def alist(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[CheckpointTuple]:
        if config is None:
            return
        thread_id = config["configurable"]["thread_id"]
        query = "SELECT id, thread_id, checkpoint, metadata FROM checkpoints WHERE thread_id = $1 ORDER BY created_at DESC"
        args: list[Any] = [thread_id]
        if limit is not None:
            query += f" LIMIT ${len(args) + 1}"
            args.append(limit)
        conn = await self._get_conn()
        try:
            rows = await conn.fetch(query, *args)
            for row in rows:
                yield CheckpointTuple(
                    config={"configurable": {"thread_id": row["thread_id"], "checkpoint_id": row["id"]}},
                    checkpoint=row["checkpoint"],
                    metadata=row["metadata"],
                    parent_config=None,
                )
        finally:
            await conn.close()

    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        raise NotImplementedError("Use async interface")

    def list(self, config: RunnableConfig | None, **kwargs) -> Any:
        raise NotImplementedError("Use async interface")

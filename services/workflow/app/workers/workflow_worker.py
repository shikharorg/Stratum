import json
import time
import uuid as uuid_module
from datetime import UTC, datetime
from typing import Any

import structlog
from arq.connections import RedisSettings

from app.core.config import settings
from app.db import AsyncSessionFactory
from app.engine.checkpointer import PostgresCheckpointer
from app.engine.graph import build_rag_graph
from app.engine.nodes import GraphState
from app.repositories.run import WorkflowRunRepository

logger = structlog.get_logger()

_STREAM = "workflow"


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


async def execute_workflow(
    ctx: dict[str, Any],
    *,
    run_id: str,
    tenant_id: str,
    workflow_id: str,
    input_data: dict,
) -> None:
    log = logger.bind(run_id=run_id, tenant_id=tenant_id, workflow_id=workflow_id)
    run_uuid = uuid_module.UUID(run_id)
    tenant_uuid = uuid_module.UUID(tenant_id)
    start = time.monotonic()

    async with AsyncSessionFactory() as session:
        run_repo = WorkflowRunRepository(session)
        try:
            await run_repo.update_status(
                run_uuid,
                tenant_uuid,
                "running",
                started_at=datetime.now(UTC),
            )
            await session.commit()

            checkpointer = PostgresCheckpointer(settings.DATABASE_URL)
            await checkpointer.setup()

            graph = build_rag_graph(checkpointer)

            initial_state: GraphState = {
                "query": input_data.get("query", ""),
                "tenant_id": tenant_id,
                "retrieved_chunks": [],
                "generated_answer": "",
                "grounding_passed": True,
                "error": None,
                "step_count": 0,
                "extra_metadata": {},
            }

            thread_config = {"configurable": {"thread_id": run_id}}
            cancel_key = f"arq:cancel:{run_id}"
            redis = ctx["redis"]

            final_state: GraphState = initial_state
            cancelled = False

            async for state_update in graph.astream(initial_state, thread_config, stream_mode="values"):
                final_state = state_update
                flag = await redis.get(cancel_key)
                if flag:
                    await redis.delete(cancel_key)
                    cancelled = True
                    break

            if cancelled:
                await run_repo.update_status(run_uuid, tenant_uuid, "cancelled")
                await session.commit()
                log.info("worker.workflow_cancelled")
                return

            latency_ms = int((time.monotonic() - start) * 1000)

            await run_repo.update_checkpoint(run_uuid, tenant_uuid, run_id)

            output_data = {
                "answer": final_state.get("generated_answer", ""),
                "grounding_passed": final_state.get("grounding_passed", True),
                "chunks": final_state.get("retrieved_chunks", []),
                "error": final_state.get("error"),
            }
            await run_repo.update_output(run_uuid, tenant_uuid, output_data, latency_ms)
            await session.commit()

            log.info("worker.workflow_completed", latency_ms=latency_ms)

            try:
                await _publish(
                    ctx["redis"],
                    "workflow.run.completed",
                    tenant_id,
                    {"run_id": run_id, "tenant_id": tenant_id, "workflow_id": workflow_id, "status": "completed"},
                )
            except Exception:
                log.exception("worker.publish_completed_failed")

        except Exception as exc:
            await session.rollback()
            log.exception("worker.workflow_failed", error=str(exc))

            try:
                async with AsyncSessionFactory() as err_session:
                    await WorkflowRunRepository(err_session).update_status(
                        run_uuid, tenant_uuid, "failed", str(exc)
                    )
                    await err_session.commit()
            except Exception:
                log.exception("worker.failed_status_update_failed")

            try:
                await _publish(
                    ctx["redis"],
                    "workflow.run.failed",
                    tenant_id,
                    {"run_id": run_id, "tenant_id": tenant_id, "workflow_id": workflow_id, "status": "failed"},
                )
            except Exception:
                log.exception("worker.publish_failed_event_failed")


class WorkerSettings:
    functions = [execute_workflow]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs: int = 10
    job_timeout: int = 600

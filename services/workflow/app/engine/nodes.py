from typing import TypedDict

import httpx
import structlog
from openai import AsyncOpenAI

from app.core.config import settings

logger = structlog.get_logger()

_openai_client: AsyncOpenAI | None = None


def _get_openai() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


class GraphState(TypedDict):
    query: str
    tenant_id: str
    retrieved_chunks: list[dict]
    generated_answer: str
    grounding_passed: bool
    error: str | None
    step_count: int
    extra_metadata: dict


async def retrieve_node(state: GraphState) -> GraphState:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.RETRIEVAL_SERVICE_URL}/api/v1/retrieve",
                json={"query": state["query"], "include_generation": False},
                headers={
                    "X-Tenant-ID": state["tenant_id"],
                    "X-User-ID": "workflow-service",
                    "X-User-Roles": "internal",
                },
            )
            response.raise_for_status()
            data = response.json()
            chunks = data.get("result", {}).get("chunks", [])
        logger.info(
            "node.retrieve.completed",
            tenant_id=state["tenant_id"],
            chunk_count=len(chunks),
        )
        return {**state, "retrieved_chunks": chunks, "step_count": state["step_count"] + 1}
    except Exception as exc:
        logger.exception("node.retrieve.failed", error=str(exc))
        return {**state, "error": str(exc), "step_count": state["step_count"] + 1}


async def generate_node(state: GraphState) -> GraphState:
    if not settings.OPENAI_API_KEY:
        logger.warning("node.generate.skipped", reason="no_api_key")
        return {**state, "generated_answer": "", "step_count": state["step_count"] + 1}

    chunks = state["retrieved_chunks"]
    context = "\n\n".join(c.get("text", "") for c in chunks)

    try:
        client = _get_openai()
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Answer the question using only the provided context. Be concise and accurate.",
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {state['query']}",
                },
            ],
        )
        answer = response.choices[0].message.content or ""
        logger.info("node.generate.completed", tenant_id=state["tenant_id"])
        return {**state, "generated_answer": answer, "step_count": state["step_count"] + 1}
    except Exception as exc:
        logger.exception("node.generate.failed", error=str(exc))
        return {**state, "error": str(exc), "step_count": state["step_count"] + 1}


async def validate_node(state: GraphState) -> GraphState:
    if not settings.OPENAI_API_KEY:
        logger.warning("node.validate.skipped", reason="no_api_key")
        return {**state, "grounding_passed": True, "step_count": state["step_count"] + 1}

    chunks = state["retrieved_chunks"]
    context = "\n\n".join(c.get("text", "") for c in chunks)
    answer = state["generated_answer"]

    try:
        client = _get_openai()
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a grounding validator. Given a context and an answer, "
                        "estimate what percentage of claims in the answer are NOT supported by the context. "
                        "Respond with ONLY an integer between 0 and 100 representing the unsupported percentage."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nAnswer:\n{answer}",
                },
            ],
        )
        raw = (response.choices[0].message.content or "0").strip().rstrip("%")
        unsupported_pct = float(raw)
        grounding_passed = unsupported_pct < 15.0
        logger.info(
            "node.validate.completed",
            tenant_id=state["tenant_id"],
            unsupported_pct=unsupported_pct,
            grounding_passed=grounding_passed,
        )
        return {**state, "grounding_passed": grounding_passed, "step_count": state["step_count"] + 1}
    except Exception as exc:
        logger.exception("node.validate.failed", error=str(exc))
        return {**state, "error": str(exc), "step_count": state["step_count"] + 1}

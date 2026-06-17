import json

import structlog
from openai import AsyncOpenAI

from app.core.config import settings

logger = structlog.get_logger()

_CONTEXT_SEPARATOR = "\n\n---\n\n"


def _build_client() -> AsyncOpenAI | None:
    if not settings.OPENAI_API_KEY:
        return None
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


_client: AsyncOpenAI | None = _build_client()


async def generate_answer(query: str, context_chunks: list[str], strict: bool = False) -> str:
    if _client is None:
        return ""

    context = _CONTEXT_SEPARATOR.join(context_chunks)

    system_prompt = (
        "You are an enterprise AI assistant. Answer ONLY using the provided context.\n\n"
        "Formatting rules:\n"
        "- Always respond in Markdown format.\n"
        "- Use ## headings for major sections.\n"
        "- Use numbered lists for sequential steps or processes.\n"
        "- Use bullet points for recommendations or non-sequential items.\n"
        "- Bold important terms using **term**.\n"
        "- Use tables for comparisons when appropriate.\n"
        "- Never write one long paragraph when the answer contains multiple steps or items.\n"
        "- When the context contains procedures, policies, or numbered steps, present them "
        "faithfully. You may paraphrase for clarity, but do not omit or invent information.\n"
        "- Keep answers concise and factual.\n"
        "- Only respond with 'I couldn't find that information in the provided documents.' "
        "when the retrieved context genuinely does not contain the information needed to "
        "answer the question. If the answer is present, answer normally."
    )

    response = await _client.chat.completions.create(
        model=settings.OPENAI_GENERATION_MODEL,
        temperature=0,
        max_tokens=settings.OPENAI_GENERATION_MAX_TOKENS,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuery: {query}",
            },
        ],
    )

    return response.choices[0].message.content or ""


async def validate(query: str, answer: str, context_chunks: list[str]) -> bool:
    if _client is None:
        return True

    context = _CONTEXT_SEPARATOR.join(context_chunks)

    system_prompt = (
        "You are a grounding validator. Given a query, an answer, and context chunks, "
        "extract each factual claim from the answer and determine whether each claim "
        "is supported by the provided context. "
        'Return a JSON object with exactly these fields: {"supported_count": <int>, "total_count": <int>}. '
        "supported_count is the number of claims directly supported by the context. "
        "total_count is the total number of claims extracted from the answer."
    )

    response = await _client.chat.completions.create(
        model=settings.OPENAI_VALIDATION_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Query: {query}\n\n"
                    f"Answer: {answer}\n\n"
                    f"Context:\n{context}"
                ),
            },
        ],
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or "{}"
    try:
        data = json.loads(raw)
        supported = int(data.get("supported_count", 0))
        total = int(data.get("total_count", 1))
    except (ValueError, KeyError):
        logger.warning("grounding.parse_failed", raw=raw)
        return True

    if total == 0:
        return True

    unsupported_ratio = (total - supported) / total
    passed = unsupported_ratio < 0.15

    logger.info(
        "grounding.validated",
        supported=supported,
        total=total,
        unsupported_ratio=round(unsupported_ratio, 3),
        passed=passed,
    )

    return passed

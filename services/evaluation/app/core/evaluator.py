import asyncio
import math

import structlog
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas import evaluate
from ragas.dataset_schema import EvaluationDataset, SingleTurnSample
from ragas.embeddings.base import LangchainEmbeddingsWrapper
from ragas.llms.base import LangchainLLMWrapper
from ragas.metrics._answer_relevance import answer_relevancy
from ragas.metrics._context_precision import context_precision
from ragas.metrics._faithfulness import faithfulness

from app.core.config import settings

logger = structlog.get_logger()


def _score(value: object) -> float | None:
    if isinstance(value, list):
        value = value[0] if value else None
    if value is None:
        return None
    try:
        f = float(value)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


def _run_ragas(query: str, answer: str, contexts: list[str]) -> dict:
    """Runs synchronous RAGAS evaluate. Must be called in a thread pool
    (not the uvloop event loop) because RAGAS internally calls asyncio.run()."""
    llm = LangchainLLMWrapper(
        ChatOpenAI(model=settings.OPENAI_EVALUATION_MODEL, api_key=settings.OPENAI_API_KEY)
    )
    emb = LangchainEmbeddingsWrapper(
        OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
    )

    faithfulness.llm = llm
    answer_relevancy.llm = llm
    answer_relevancy.embeddings = emb
    context_precision.llm = llm

    sample = SingleTurnSample(
        user_input=query,
        response=answer,
        retrieved_contexts=contexts,
        reference=answer,
    )
    dataset = EvaluationDataset(samples=[sample])

    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision],
        show_progress=False,
        raise_exceptions=False,
    )

    f = _score(result["faithfulness"])
    ar = _score(result["answer_relevancy"])
    cp = _score(result["context_precision"])

    valid = [v for v in [f, ar, cp] if v is not None]
    overall = sum(valid) / len(valid) if valid else None

    return {
        "faithfulness": f,
        "answer_relevancy": ar,
        "context_precision": cp,
        "overall_score": overall,
    }


async def run_evaluation(query: str, answer: str, contexts: list[str]) -> dict:
    """Offloads RAGAS to a thread pool so asyncio.run() inside RAGAS
    doesn't conflict with the running uvloop event loop."""
    try:
        scores = await asyncio.to_thread(_run_ragas, query, answer, contexts)
        logger.info(
            "evaluation.scores",
            faithfulness=scores["faithfulness"],
            answer_relevancy=scores["answer_relevancy"],
            context_precision=scores["context_precision"],
            overall_score=scores["overall_score"],
        )
        return scores
    except Exception as exc:
        logger.error("evaluation.failed", error=str(exc))
        return {
            "faithfulness": None,
            "answer_relevancy": None,
            "context_precision": None,
            "overall_score": None,
            "error": str(exc),
        }

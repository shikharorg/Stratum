import structlog
from sentence_transformers import CrossEncoder

from app.core.config import settings
from app.schemas.search import SearchResult

logger = structlog.get_logger()


class Reranker:
    def __init__(self) -> None:
        self._model = CrossEncoder(settings.RERANKER_MODEL, device="cpu")
        logger.info("reranker.model_loaded", model=settings.RERANKER_MODEL)

    def rerank(self, query: str, results: list[SearchResult], top_k: int) -> list[SearchResult]:
        if not results:
            return []

        pairs = [(query, r.text) for r in results]
        scores = self._model.predict(pairs)

        for result, score in zip(results, scores):
            result.combined_score = float(score)

        return sorted(results, key=lambda r: r.combined_score, reverse=True)[:top_k]

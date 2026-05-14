import structlog
from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = structlog.get_logger()


class EmbeddingEncoder:
    def __init__(self) -> None:
        self._model = SentenceTransformer(settings.EMBEDDING_MODEL, device="cpu")
        logger.info("encoder.model_loaded", model=settings.EMBEDDING_MODEL)

    def encode(self, texts: list[str]) -> list[list[float]]:
        embeddings = self._model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def encode_query(self, text: str) -> list[float]:
        embedding = self._model.encode([text], normalize_embeddings=True)
        return embedding[0].tolist()

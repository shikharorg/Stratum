import math
import string
from collections import Counter

import structlog
from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = structlog.get_logger()

_K1 = 1.5
_B = 0.75
_PUNCT_TABLE = str.maketrans("", "", string.punctuation)


def _tokenize(text: str) -> list[str]:
    return [t for t in text.lower().translate(_PUNCT_TABLE).split() if t]


class QueryEncoder:
    def __init__(self) -> None:
        self._model = SentenceTransformer(settings.EMBEDDING_MODEL, device="cpu")
        logger.info("query_encoder.model_loaded", model=settings.EMBEDDING_MODEL)

    def encode_query(self, text: str) -> list[float]:
        embedding = self._model.encode([text], normalize_embeddings=True)
        return embedding[0].tolist()

    def encode_sparse(self, text: str) -> dict:
        tokens = _tokenize(text)
        if not tokens:
            return {"indices": [], "values": []}

        df: Counter[str] = Counter(set(tokens))
        n = 1
        vocab: dict[str, int] = {term: i for i, term in enumerate(df)}
        idf: dict[int, float] = {
            vocab[term]: math.log(1.0 + (n - freq + 0.5) / (freq + 0.5))
            for term, freq in df.items()
        }
        avg_len = float(len(tokens))

        tf = Counter(tokens)
        doc_len = len(tokens)
        indices: list[int] = []
        values: list[float] = []

        for term, freq in tf.items():
            if term not in vocab:
                continue
            term_id = vocab[term]
            idf_val = idf.get(term_id, 0.0)
            denom = freq + _K1 * (1.0 - _B + _B * doc_len / avg_len)
            score = idf_val * (freq * (_K1 + 1.0)) / denom
            if score > 0.0:
                indices.append(term_id)
                values.append(score)

        return {"indices": indices, "values": values}

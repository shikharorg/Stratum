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


class SparseEncoder:
    def __init__(self) -> None:
        self._vocab: dict[str, int] = {}
        self._idf: dict[int, float] = {}
        logger.info("sparse_encoder.initialized")

    def fit(self, texts: list[str]) -> None:
        tokenized = [_tokenize(t) for t in texts]
        n = len(tokenized)

        df: Counter[str] = Counter()
        for tokens in tokenized:
            df.update(set(tokens))

        self._vocab = {}
        for term in df:
            if term not in self._vocab:
                self._vocab[term] = len(self._vocab)

        self._idf = {
            self._vocab[term]: math.log(1.0 + (n - freq + 0.5) / (freq + 0.5))
            for term, freq in df.items()
        }

        avg_len = sum(len(t) for t in tokenized) / n if n else 1.0
        self._avg_len = avg_len

    def encode_sparse(self, texts: list[str]) -> list[dict]:
        self.fit(texts)
        tokenized = [_tokenize(t) for t in texts]
        result: list[dict] = []

        for tokens in tokenized:
            tf = Counter(tokens)
            doc_len = len(tokens)
            indices: list[int] = []
            values: list[float] = []

            for term, freq in tf.items():
                if term not in self._vocab:
                    continue
                term_id = self._vocab[term]
                idf = self._idf.get(term_id, 0.0)
                denom = freq + _K1 * (1.0 - _B + _B * doc_len / self._avg_len)
                score = idf * (freq * (_K1 + 1.0)) / denom
                if score > 0.0:
                    indices.append(term_id)
                    values.append(score)

            result.append({"indices": indices, "values": values})

        return result

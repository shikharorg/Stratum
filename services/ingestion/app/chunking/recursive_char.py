import re

from app.chunking.base import BaseChunker, ChunkData

_SEPARATORS = [r"\n\n+", r"(?<=[.!?])\s+", r"\s+"]


class RecursiveCharChunker(BaseChunker):
    def __init__(
        self,
        chunk_size_chars: int = 2048,
        chunk_overlap_chars: int = 200,
    ) -> None:
        self.chunk_size_chars = chunk_size_chars
        self.chunk_overlap_chars = chunk_overlap_chars

    def chunk(self, content: str) -> list[ChunkData]:
        pieces = self._split(content.strip())
        result: list[ChunkData] = []
        for i, text in enumerate(pieces):
            if text:
                result.append(
                    ChunkData(
                        text=text,
                        chunk_index=i,
                        token_count=len(text) // 4,
                        section_title=None,
                        parent_chunk_id=None,
                        extra_metadata={},
                    )
                )
        return result

    def _split(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size_chars:
            return [text]

        for sep in _SEPARATORS:
            parts = [p for p in re.split(sep, text) if p.strip()]
            if len(parts) > 1:
                return self._merge(parts)

        chunks: list[str] = []
        step = max(1, self.chunk_size_chars - self.chunk_overlap_chars)
        for start in range(0, len(text), step):
            piece = text[start : start + self.chunk_size_chars]
            if piece.strip():
                chunks.append(piece.strip())
            if start + self.chunk_size_chars >= len(text):
                break
        return chunks

    def _merge(self, parts: list[str]) -> list[str]:
        chunks: list[str] = []
        buf: list[str] = []
        buf_len = 0

        for part in parts:
            part = part.strip()
            if not part:
                continue

            sep_cost = 1 if buf else 0
            part_len = len(part)

            if buf and buf_len + sep_cost + part_len > self.chunk_size_chars:
                text = " ".join(buf)
                if len(text) > self.chunk_size_chars:
                    chunks.extend(self._split(text))
                else:
                    chunks.append(text)

                overlap: list[str] = []
                overlap_len = 0
                for p in reversed(buf):
                    cost = len(p) + (1 if overlap else 0)
                    if overlap_len + cost <= self.chunk_overlap_chars:
                        overlap.insert(0, p)
                        overlap_len += cost
                    else:
                        break
                buf = overlap
                buf_len = overlap_len

            if part_len > self.chunk_size_chars:
                if buf:
                    chunks.append(" ".join(buf))
                    buf = []
                    buf_len = 0
                chunks.extend(self._split(part))
            else:
                sep_cost = 1 if buf else 0
                buf.append(part)
                buf_len += sep_cost + part_len

        if buf:
            text = " ".join(buf).strip()
            if text:
                chunks.append(text)

        return chunks

import re

from app.chunking.base import BaseChunker, ChunkData

_HEADING_RE = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)


class HeadingAwareChunker(BaseChunker):
    def chunk(self, content: str) -> list[ChunkData]:
        matches = list(_HEADING_RE.finditer(content))
        if not matches:
            return self._split_by_paragraph(content)

        chunks: list[ChunkData] = []

        preamble = content[: matches[0].start()].strip()
        if preamble:
            chunks.append(
                ChunkData(
                    text=preamble,
                    chunk_index=len(chunks),
                    token_count=len(preamble) // 4,
                    section_title=None,
                    parent_chunk_id=None,
                    extra_metadata={},
                )
            )

        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            text = content[start:end].strip()
            if not text:
                continue
            title = match.group(2).strip()
            chunks.append(
                ChunkData(
                    text=text,
                    chunk_index=len(chunks),
                    token_count=len(text) // 4,
                    section_title=title,
                    parent_chunk_id=None,
                    extra_metadata={},
                )
            )

        return chunks

    def _split_by_paragraph(self, content: str) -> list[ChunkData]:
        chunks: list[ChunkData] = []
        for para in re.split(r"\n\n+", content):
            text = para.strip()
            if not text:
                continue
            chunks.append(
                ChunkData(
                    text=text,
                    chunk_index=len(chunks),
                    token_count=len(text) // 4,
                    section_title=None,
                    parent_chunk_id=None,
                    extra_metadata={},
                )
            )
        return chunks

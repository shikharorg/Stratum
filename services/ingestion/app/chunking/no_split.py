from app.chunking.base import BaseChunker, ChunkData


class NoSplitChunker(BaseChunker):
    def chunk(self, content: str) -> list[ChunkData]:
        text = content.strip()
        if not text:
            return []
        return [
            ChunkData(
                text=text,
                chunk_index=0,
                token_count=len(text) // 4,
                section_title=None,
                parent_chunk_id=None,
                extra_metadata={},
            )
        ]

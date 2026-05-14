import structlog

from app.chunking.base import BaseChunker, ChunkData
from app.chunking.code_block import CodeBlockChunker
from app.chunking.heading_aware import HeadingAwareChunker
from app.chunking.no_split import NoSplitChunker
from app.chunking.recursive_char import RecursiveCharChunker

logger = structlog.get_logger()

_NO_SPLIT_TYPES: frozenset[str] = frozenset({"slack", "jira", "github"})


class DocumentRouter:
    def route(self, source_type: str, content: str) -> list[ChunkData]:
        chunker = self._select(source_type)
        logger.info("router.chunker_selected", source_type=source_type, chunker=type(chunker).__name__)
        return chunker.chunk(content)

    def _select(self, source_type: str) -> BaseChunker:
        if source_type == "markdown":
            return HeadingAwareChunker()
        if source_type == "pdf":
            return RecursiveCharChunker()
        if source_type == "code":
            return CodeBlockChunker()
        if source_type in _NO_SPLIT_TYPES:
            return NoSplitChunker()
        logger.warning("router.unknown_source_type_fallback", source_type=source_type)
        return RecursiveCharChunker()

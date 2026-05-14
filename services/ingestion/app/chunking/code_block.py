import ast

import structlog

from app.chunking.base import BaseChunker, ChunkData

logger = structlog.get_logger()


class CodeBlockChunker(BaseChunker):
    def chunk(self, content: str) -> list[ChunkData]:
        try:
            tree = ast.parse(content)
        except SyntaxError:
            logger.warning("code_chunker.ast_parse_failed", reason="SyntaxError")
            return self._fallback(content)

        chunks: list[ChunkData] = []
        for node in ast.iter_child_nodes(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            text = ast.get_source_segment(content, node)
            if not text:
                continue
            text = text.strip()
            if not text:
                continue
            node_type = "class" if isinstance(node, ast.ClassDef) else "function"
            chunks.append(
                ChunkData(
                    text=text,
                    chunk_index=len(chunks),
                    token_count=len(text) // 4,
                    section_title=node.name,
                    parent_chunk_id=None,
                    extra_metadata={"language": "python", "node_type": node_type},
                )
            )

        if not chunks:
            logger.warning("code_chunker.no_top_level_nodes")
            return self._fallback(content)

        return chunks

    def _fallback(self, content: str) -> list[ChunkData]:
        from app.chunking.recursive_char import RecursiveCharChunker

        base_chunks = RecursiveCharChunker().chunk(content)
        for c in base_chunks:
            c.extra_metadata["language"] = "unknown"
        return base_chunks

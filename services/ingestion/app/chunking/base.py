from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ChunkData:
    text: str
    chunk_index: int
    token_count: int
    section_title: str | None
    parent_chunk_id: str | None
    extra_metadata: dict = field(default_factory=dict)


class BaseChunker(ABC):
    @abstractmethod
    def chunk(self, content: str) -> list[ChunkData]:
        ...

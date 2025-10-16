from pydantic import BaseModel
from pydantic import Field


class EmbeddingData(BaseModel):
    chunk_index: int = Field(..., title='Chunk index')
    raw_text: str = Field(..., title='Raw text used for embedding')
    embedding: list[float] = Field(..., title='Vector embedding')
    tags: list[str] = Field(default_factory=list, title='Embedding tags')

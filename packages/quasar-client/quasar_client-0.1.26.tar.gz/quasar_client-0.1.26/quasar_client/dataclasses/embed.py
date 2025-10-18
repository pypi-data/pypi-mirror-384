"""Dataclasses for embeddings."""

from pydantic import BaseModel


class EmbeddingMeta(BaseModel):
    """Metadata for an embedding output."""

    text: str
    embedding: list[float]

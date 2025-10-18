"""Dataclasses for embeddings."""

from pydantic import BaseModel


class ColumnCountClassifierMeta(BaseModel):
    """Metadata for a multi modal embedding output."""

    column_counts: list[int]

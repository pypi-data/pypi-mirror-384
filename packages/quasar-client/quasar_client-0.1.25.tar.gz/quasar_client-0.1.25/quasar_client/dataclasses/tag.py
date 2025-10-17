"""Dataclasses for taggers."""

from pydantic import BaseModel


class TaggerMeta(BaseModel):
    """Metadata for a tagger output."""

    end: int
    label: str
    score: float
    span: str
    start: int

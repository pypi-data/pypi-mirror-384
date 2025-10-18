"""Dataclasses for extractions."""

from pydantic import BaseModel


class Keyword(BaseModel):
    """Keyword dataclass."""

    keyword: str
    score: float


class ExtractMeta(BaseModel):
    """Metadata for an extractor output."""

    text: str
    keywords: list[Keyword] | None = None
    topics: list[str] | None = None

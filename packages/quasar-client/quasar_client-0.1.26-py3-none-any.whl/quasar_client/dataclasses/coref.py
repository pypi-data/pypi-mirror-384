"""Dataclasses for coref."""

from pydantic import BaseModel


class CorefCluster(BaseModel):
    """A coref cluster."""

    start: int
    end: int


class CorefMeta(BaseModel):
    """Metadata for coref output."""

    text: str
    resolved_text: str | None = None
    clusters: list[list[CorefCluster]] | None = None

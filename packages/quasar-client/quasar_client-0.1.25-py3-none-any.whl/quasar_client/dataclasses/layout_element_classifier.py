"""Dataclasses for embeddings."""

from pydantic import BaseModel


class LayoutElementClassifierMeta(BaseModel):
    """Metadata for a multi modal embedding output."""

    classified_blocks_by_page: dict[int, list[dict]]

"""Dataclasses for ranker models."""

from typing import Tuple

from pydantic import BaseModel


class RankerMeta(BaseModel):
    """Metadata for a ranker output."""

    pair: Tuple[str, str]
    score: float

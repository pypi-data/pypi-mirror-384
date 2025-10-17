"""Dataclasses for Quasar."""

from pydantic import BaseModel


class ModelData(BaseModel):
    """Model data from Quasar."""

    id: str
    provider: str
    metadata: dict | None

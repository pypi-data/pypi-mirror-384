"""Dataclasses for text line detection."""

from typing import Any
from pydantic import BaseModel


class TextLineDetectorMeta(BaseModel):
    """Metadata for text line detection output."""

    text_lines_detected: list[dict[str, Any]]

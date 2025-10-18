"""Extract Resource Module."""

from typing import Literal, Union

from ..dataclasses.extract import ExtractMeta, Keyword
from .base import AsyncResource, SyncResource


class SyncExtractorResource(SyncResource):
    """Synchronous ExtractorResource Class."""

    def extract(
        self,
        text: str,
        task: Literal["topics"] | Literal["keyword-extraction"] | None = None,
        model: str | None = None,
        priority: int = 0,
        extractor_args: dict | None = None,
        **kwargs,
    ) -> ExtractMeta:
        """Extract keywords or topics."""
        extractor_args = extractor_args or {}
        data = {
            "input_data": {"docs": [text], **extractor_args},
            "priority": priority,
        }
        if model:
            data["model"] = model
        elif task:
            data["task"] = task
        else:
            raise ValueError("Either `task` or `model` must be provided.")
        output = self._post(
            data=data,
            **kwargs,
        )
        output.raise_for_status()
        extract_response = output.json()["output"]
        return ExtractMeta(
            text=text,
            keywords=[
                Keyword(
                    keyword=kw["keyword"],
                    score=kw["score"],
                )
                for kw in extract_response[0]["keywords"]
            ],
        )


class AsyncExtractorResource(AsyncResource):
    """Asynchronous Extractor Resource Class."""

    async def extract(
        self,
        text: str,
        task: Literal["topics"] | Literal["keyword-extraction"] | None = None,
        model: str | None = None,
        read_timeout: float = 10.0,
        timeout: float = 180.0,
        priority: int = 0,
        extractor_args: dict | None = None,
        **kwargs,
    ) -> ExtractMeta:
        """Extract keywords or topics."""
        extractor_args = extractor_args or {}
        data = {
            "input_data": {"docs": [text], **extractor_args},
            "task": task,
            "priority": priority,
        }
        if model:
            data["model"] = model
        elif task:
            data["task"] = task
        else:
            raise ValueError("Either `task` or `model` must be provided.")
        output = await self._post(
            data=data,
            read_timeout=read_timeout,
            timeout=timeout,
            **kwargs,
        )
        output.raise_for_status()
        extract_response = output.json()["output"]
        return ExtractMeta(
            text=text,
            keywords=[
                Keyword(
                    keyword=kw["keyword"],
                    score=kw["score"],
                )
                for kw in extract_response[0]["keywords"]
            ],
        )

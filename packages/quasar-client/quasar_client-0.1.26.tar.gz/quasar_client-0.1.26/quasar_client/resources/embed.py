"""Ranker Resource Module."""

from ..dataclasses.embed import EmbeddingMeta
from .base import AsyncResource, SyncResource


class SyncEmbeddingResource(SyncResource):
    """Synchronous Embedding Resource Class."""

    def embed(
        self,
        texts: list[str],
        model: str | None = None,
        priority: int = 0,
        **kwargs,
    ) -> list[EmbeddingMeta]:
        """Embed all texts."""
        data: dict = {
            "input_data": {"texts": texts},
        }
        if model:
            data["model"] = model
        else:
            data["task"] = "embedding"
        output = self._post(
            data={
                "input_data": {"texts": texts},
                "task": "embedding",
                "priority": priority,
            },
            **kwargs,
        )
        output.raise_for_status()
        return [
            EmbeddingMeta(
                embedding=emb["embedding"],
                text=emb["text"],
            )
            for emb in output.json()["output"]
        ]


class AsyncEmbeddingResource(AsyncResource):
    """Asynchronous Embedding Resource Class."""

    async def embed(
        self,
        texts: list[str],
        model: str | None = None,
        read_timeout: float = 10.0,
        timeout: float = 180.0,
        priority: int = 0,
        **kwargs,
    ) -> list[EmbeddingMeta]:
        """Asynchronously embed all texts."""
        data: dict = {
            "input_data": {"texts": texts},
            "priority": priority,
        }
        if model:
            data["model"] = model
        else:
            data["task"] = "embedding"
        response = await self._post(
            data=data,
            read_timeout=read_timeout,
            timeout=timeout,
            **kwargs,
        )
        response.raise_for_status()  # Ensure proper exception handling in your async context.
        return [
            EmbeddingMeta(
                embedding=emb["embedding"],
                text=emb["text"],
            )
            for emb in response.json()["output"]
        ]

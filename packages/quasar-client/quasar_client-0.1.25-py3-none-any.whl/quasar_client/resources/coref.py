"""Coreference Resolution Resource Module."""

from ..dataclasses.coref import CorefCluster, CorefMeta
from .base import AsyncResource, SyncResource


class SyncCorefResource(SyncResource):
    """Synchronous Coref Resource Class."""

    def resolve(
        self,
        text: str,
        model: str | None = None,
        priority: int = 0,
        **kwargs,
    ) -> CorefMeta:
        """Get corefs and resolved text."""
        data = {
            "input_data": {
                "text": text,
                "resolve_text": True,
            },
            "priority": priority,
        }
        if model:
            data["model"] = model
        else:
            data["task"] = "coreference-resolution"
        output = self._post(
            data=data,
            **kwargs,
        )
        output.raise_for_status()
        coref_resp = output.json()["output"]
        clusters = [
            [
                CorefCluster(
                    start=ref[0],
                    end=ref[1],
                )
                for ref in cluster
            ]
            for cluster in coref_resp["coref_clusters"]
        ]
        return CorefMeta(
            text=coref_resp["text"],
            resolved_text=coref_resp["resolved_text"],
            clusters=clusters,
        )


class AsyncCorefResource(AsyncResource):
    """Asynchronous Coref Resource Class."""

    async def resolve(
        self,
        text: str,
        model: str | None = None,
        read_timeout: float = 10.0,
        timeout: float = 180.0,
        priority: int = 0,
        **kwargs,
    ) -> CorefMeta:
        """Embed all texts."""
        data = {
            "input_data": {"text": text, "resolve_text": True},
            "priority": priority,
        }
        if model:
            data["model"] = model
        else:
            data["task"] = "coreference-resolution"
        output = await self._post(
            data=data,
            read_timeout=read_timeout,
            timeout=timeout,
            **kwargs,
        )
        output.raise_for_status()
        coref_resp = output.json()["output"]
        clusters = [
            [
                CorefCluster(
                    start=ref[0],
                    end=ref[1],
                )
                for ref in cluster
            ]
            for cluster in coref_resp["coref_clusters"]
        ]
        return CorefMeta(
            text=coref_resp["text"],
            resolved_text=coref_resp["resolved_text"],
            clusters=clusters,
        )

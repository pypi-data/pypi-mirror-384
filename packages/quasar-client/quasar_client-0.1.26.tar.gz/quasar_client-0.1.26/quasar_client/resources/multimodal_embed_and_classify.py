"""Classifier Resource Module."""

from ..dataclasses.layout_element_classifier import LayoutElementClassifierMeta
from .base import AsyncResource, SyncResource


class SyncMultiModalClassifierResource(SyncResource):
    """Synchronous Multimodal embedding and classification resource."""

    def classify(
        self,
        page_properties: dict[int, dict],
        **kwargs,
    ) -> LayoutElementClassifierMeta:
        """Multimodal model classification of page layout"""
        task = "layout-element-classification"
        input_data = {"page_properties": page_properties}

        output = self._post(
            data={
                "input_data": input_data,
                "task": task,
            },
            **kwargs,
        )

        output.raise_for_status()
        return LayoutElementClassifierMeta(classified_blocks_by_page=output.json()["output"])


class AsyncMultiModalClassifierResource(AsyncResource):
    """Asynchronous Multimodal embedding and classification resource"""

    async def classify(
        self,
        page_properties: dict[int, dict],
        read_timeout: float = 10.0,
        timeout: float = 180.0,
        **kwargs,
    ) -> LayoutElementClassifierMeta:
        """Embed all texts."""
        task = "layout-element-classification"
        input_data = {"page_properties": page_properties}

        output = await self._post(
            data={
                "input_data": input_data,
                "task": task,
            },
            read_timeout=read_timeout,
            timeout=timeout,
            **kwargs,
        )

        output.raise_for_status()
        return LayoutElementClassifierMeta(classified_blocks_by_page=output.json()["output"])

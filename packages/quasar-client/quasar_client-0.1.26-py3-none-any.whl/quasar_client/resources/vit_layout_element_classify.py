"""VIT Classifier Resource Module."""

from ..dataclasses.vit_layout_element_classify import VITLayoutElementClassifierMeta
from .base import AsyncResource, SyncResource

from typing import Any


class SyncVITLayoutElementClassifierResource(SyncResource):
    """Synchronous vit based layout classification resource."""

    def classify(
        self,
        pages_image: list[str],
        text_line_detection_results: list[dict[str, Any]],
        model: str = "vit-layout-element-classification",
        **kwargs,
    ) -> VITLayoutElementClassifierMeta:
        """Layout element classification using vit"""
        task = "vit-layout-element-classification"
        input_data = {
            "pages_image": pages_image,
            "text_line_detection_results": text_line_detection_results,
        }

        output = self._post(
            data={"input_data": input_data, "task": task, "model": model},
            **kwargs,
        )

        output.raise_for_status()
        return VITLayoutElementClassifierMeta(layout_elements_classified=output.json()["output"])


class AsyncVITLayoutElementClassifierResource(AsyncResource):
    """Asynchronous vit based layout classification resource."""

    async def classify(
        self,
        pages_image: list[str],
        text_line_detection_results: list[dict[str, Any]],
        model: str = "vit-layout-element-classification",
        read_timeout: float = 10.0,
        timeout: float = 180.0,
        **kwargs,
    ) -> VITLayoutElementClassifierMeta:
        """Layout element classification using vit"""

        task = "vit-layout-element-classification"
        input_data = {
            "pages_image": pages_image,
            "text_line_detection_results": text_line_detection_results,
        }

        output = await self._post(
            data={"input_data": input_data, "task": task, "model": model},
            read_timeout=read_timeout,
            timeout=timeout,
            **kwargs,
        )

        output.raise_for_status()
        return VITLayoutElementClassifierMeta(layout_elements_classified=output.json()["output"])

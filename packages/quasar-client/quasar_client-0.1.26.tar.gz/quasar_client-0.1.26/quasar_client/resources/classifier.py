"""Classifier Resource Module."""

from typing import Literal

from ..dataclasses.classify import Classification, ClassifierMeta
from .base import AsyncResource, SyncResource


class SyncClassifierResource(SyncResource):
    """Synchronous Classififer Resource Class."""

    def classify(
        self,
        text: str,
        task: Literal["zero-shot-classification"] | Literal["text-classification"] | None = None,
        model: str | None = None,
        labels: list[str] | None = None,
        priority: int = 0,
        **kwargs,
    ) -> ClassifierMeta:
        """Classify all texts."""
        data = {
            "input_data": {"text": text},
            "task": task,
            "priority": priority,
        }
        if task == "zero-shot-classification":
            data["input_data"]["candidate_labels"] = labels

        if model:
            data["model"] = model
        elif task:
            data["task"] = task
        else:
            raise ValueError("Either `task` or `model` must be provided.")
        output = self._post(data=data, **kwargs)
        output.raise_for_status()
        classification_resp = output.json()["output"]
        labels = classification_resp["labels"]
        scores = classification_resp["scores"]
        return ClassifierMeta(
            classifications=[
                Classification(label=label, confidence=score)
                for label, score in zip(labels, scores)
            ],
            text=text,
        )


class AsyncClassifierResource(AsyncResource):
    """Asynchronous Classifier Resource Class."""

    async def classify(
        self,
        text: str,
        task: Literal["zero-shot-classification"] | Literal["text-classification"] | None = None,
        model: str | None = None,
        labels: list[str] | None = None,
        read_timeout: float = 10.0,
        timeout: float = 180.0,
        priority: int = 0,
        **kwargs,
    ) -> ClassifierMeta:
        """Embed all texts."""
        data = {
            "input_data": {"text": text},
            "task": task,
            "priority": priority,
        }
        if task == "zero-shot-classification":
            data["input_data"]["candidate_labels"] = labels

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
        classification_resp = output.json()["output"]
        labels = classification_resp["labels"]
        scores = classification_resp["scores"]
        return ClassifierMeta(
            classifications=[
                Classification(label=label, confidence=score)
                for label, score in zip(labels, scores)
            ],
            text=text,
        )

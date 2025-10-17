"""Official Python client for Quasar."""

from urllib.parse import urljoin

import requests
from openai import AsyncOpenAI, OpenAI

from .dataclasses.models import ModelData
from .resources.classifier import AsyncClassifierResource, SyncClassifierResource
from .resources.column_count_classifier import (
    AsyncPageColumnCounterResource,
    SyncPageColumnCounterResource,
)
from .resources.coref import AsyncCorefResource, SyncCorefResource
from .resources.embed import AsyncEmbeddingResource, SyncEmbeddingResource
from .resources.extract import AsyncExtractorResource, SyncExtractorResource
from .resources.vit_layout_element_classify import (
    AsyncVITLayoutElementClassifierResource,
    SyncVITLayoutElementClassifierResource,
)
from .resources.multimodal_embed_and_classify import (
    AsyncMultiModalClassifierResource,
    SyncMultiModalClassifierResource,
)
from .resources.rank import AsyncRankerResource, SyncRankerResource
from .resources.tagger import AsyncTaggerResource, SyncTaggerResource
from .resources.text_line_detect import (
    AsyncTextLineDetectorResource,
    SyncTextLineDetectorResource,
)


class Quasar(OpenAI):
    """Quasar Client"""

    classifier: SyncClassifierResource
    coref: SyncCorefResource
    embed: SyncEmbeddingResource
    extractor: SyncExtractorResource
    multimodal_embed_and_classify: SyncMultiModalClassifierResource
    page_column_counter: SyncPageColumnCounterResource
    ranker: SyncRankerResource
    tagger: SyncTaggerResource
    text_line_detect: SyncTextLineDetectorResource
    vit_layout_element_classifier: SyncVITLayoutElementClassifierResource

    def __init__(
        self,
        quasar_base: str,
        enable_v2: bool | None = False,
        quasar_v2_base: str | None = None,
        split_v2_percentage: float | None = None,
        *args,
        **kwargs,
    ) -> None:
        """Construct an inference client to Quasar."""
        if enable_v2 and not quasar_v2_base:
            raise ValueError("`quasar_v2_base` is required when `enable_v2` is True.")

        self.quasar_base = quasar_base

        quasar_resource_kwargs = {
            "enable_v2": enable_v2,
            "v2_base_url": quasar_v2_base,
            "split_v2_percentage": split_v2_percentage,
        }

        self._models: list[ModelData] = []
        kwargs["api_key"] = "EMPTY"
        # Set OpenAI base_url for OpenAI-compatible methods
        kwargs["base_url"] = urljoin(self.quasar_base, "/predictions/v1")
        super().__init__(*args, **kwargs)
        self.classifier = SyncClassifierResource(
            self.quasar_base, **quasar_resource_kwargs
        )
        self.coref = SyncCorefResource(self.quasar_base, **quasar_resource_kwargs)
        self.embed = SyncEmbeddingResource(self.quasar_base, **quasar_resource_kwargs)
        self.extractor = SyncExtractorResource(
            self.quasar_base, **quasar_resource_kwargs
        )
        self.vit_layout_element_classifier = SyncVITLayoutElementClassifierResource(
            self.quasar_base, **quasar_resource_kwargs
        )
        self.multimodal_embed_and_classify = SyncMultiModalClassifierResource(
            self.quasar_base, **quasar_resource_kwargs
        )
        self.page_column_counter = SyncPageColumnCounterResource(
            self.quasar_base, **quasar_resource_kwargs
        )
        self.ranker = SyncRankerResource(self.quasar_base, **quasar_resource_kwargs)
        self.tagger = SyncTaggerResource(self.quasar_base, **quasar_resource_kwargs)
        self.text_line_detect = SyncTextLineDetectorResource(
            self.quasar_base, **quasar_resource_kwargs
        )

    def list_models(self, use_cache: bool = False) -> list[ModelData]:
        """Get all models callable within Quasar and cache them."""
        # Early exit to use cache
        if use_cache and self._models:
            return self._models
        list_models_endpoint = urljoin(self.quasar_base, "predictions/v1/models")
        response = requests.get(list_models_endpoint)
        response.raise_for_status()
        models_data = response.json()
        all_models_info = []
        for provider, models in models_data.items():
            for model in models:
                model_id = model.pop("id", None) or model.pop("model", None)
                metadata = model.pop("metadata", {})
                all_models_info.append(
                    ModelData(
                        id=model_id,
                        provider=provider,
                        metadata=metadata,
                    )
                )
        self._models = all_models_info
        return all_models_info

    def list_model_info(self, model_id: str) -> ModelData:
        """List model info."""
        for model in self.list_models(use_cache=True):
            if model.id == model_id:
                return model
        raise ValueError(f"Quasar Model Information {model_id} not found.")


class AsyncQuasar(AsyncOpenAI):
    """Quasar Async Client"""

    classifier: AsyncClassifierResource
    coref: AsyncCorefResource
    embed: AsyncEmbeddingResource
    extractor: AsyncExtractorResource
    multimodal_embed_and_classify: AsyncMultiModalClassifierResource
    page_column_counter: AsyncPageColumnCounterResource
    ranker: AsyncRankerResource
    tagger: AsyncTaggerResource
    text_line_detect: AsyncTextLineDetectorResource
    vit_layout_element_classifier: AsyncVITLayoutElementClassifierResource

    def __init__(
        self,
        quasar_base: str,
        enable_v2: bool | None = False,
        quasar_v2_base: str | None = None,
        split_v2_percentage: float | None = None,
        *args,
        **kwargs,
    ) -> None:
        """Construct an inference client to Quasar."""
        if enable_v2 and not quasar_v2_base:
            raise ValueError("`quasar_v2_base` is required when `enable_v2` is True.")

        self.quasar_base = quasar_base

        quasar_resource_kwargs = {
            "enable_v2": enable_v2,
            "v2_base_url": quasar_v2_base,
            "split_v2_percentage": split_v2_percentage,
        }

        self._models: list[ModelData] = []
        kwargs["api_key"] = "EMPTY"
        # Set OpenAI base_url for OpenAI-compatible methods
        kwargs["base_url"] = urljoin(self.quasar_base, "/predictions/v1")
        super().__init__(*args, **kwargs)
        self.classifier = AsyncClassifierResource(
            self.quasar_base, **quasar_resource_kwargs
        )
        self.coref = AsyncCorefResource(self.quasar_base, **quasar_resource_kwargs)
        self.embed = AsyncEmbeddingResource(self.quasar_base, **quasar_resource_kwargs)
        self.extractor = AsyncExtractorResource(
            self.quasar_base, **quasar_resource_kwargs
        )
        self.multimodal_embed_and_classify = AsyncMultiModalClassifierResource(
            self.quasar_base, **quasar_resource_kwargs
        )
        self.page_column_counter = AsyncPageColumnCounterResource(
            self.quasar_base, **quasar_resource_kwargs
        )
        self.ranker = AsyncRankerResource(self.quasar_base, **quasar_resource_kwargs)
        self.tagger = AsyncTaggerResource(self.quasar_base, **quasar_resource_kwargs)
        self.text_line_detect = AsyncTextLineDetectorResource(
            self.quasar_base, **quasar_resource_kwargs
        )
        self.vit_layout_element_classifier = AsyncVITLayoutElementClassifierResource(
            self.quasar_base, **quasar_resource_kwargs
        )

    def list_models(
        self, use_cache: bool = False, extra_headers: dict | None = None
    ) -> list[ModelData]:
        """Get all models callable within Quasar and cache them."""
        # Early exit to use cache
        if use_cache and self._models:
            return self._models
        if extra_headers is None:
            extra_headers = {}
        list_models_endpoint = urljoin(self.quasar_base, "predictions/v1/models")
        response = requests.get(list_models_endpoint, headers=extra_headers)
        response.raise_for_status()
        models_data = response.json()
        all_models_info = []
        for provider, models in models_data.items():
            for model in models:
                model_id = model.pop("id", None) or model.pop("model", None)
                metadata = model.pop("metadata", {})
                all_models_info.append(
                    ModelData(
                        id=model_id,
                        provider=provider,
                        metadata=metadata,
                    )
                )
        self._models = all_models_info
        return all_models_info

    def list_model_info(
        self,
        model_id: str,
        extra_headers: dict | None = None,
    ) -> ModelData:
        """List model info."""
        for model in self.list_models(use_cache=True, extra_headers=extra_headers):
            if model.id == model_id:
                return model
        raise ValueError(f"Quasar Model Information {model_id} not found.")

import random
from abc import ABC, abstractmethod
from urllib.parse import urljoin

import httpx
import requests


# Abstract base class
class ResourceBase(ABC):
    """Base class for Quasar resources."""

    def __init__(
        self,
        base_url: str,
        enable_v2: bool = False,
        v2_base_url: str | None = None,
        split_v2_percentage: float = 0.5,
    ):
        if enable_v2 and not v2_base_url:
            raise ValueError("`v2_base_url` is required when `enable_v2` is True.")
        if not enable_v2 and v2_base_url:
            raise ValueError("`v2_base_url` is only allowed when `enable_v2` is True.")
        self.base_url = base_url
        self.prediction_endpoint = urljoin(self.base_url, "/predictions/")
        self.v2_base_url = v2_base_url
        self.prediction_v2_endpoint = (
            urljoin(self.v2_base_url, "/predictions/") if self.v2_base_url else None
        )
        self.split_v2_percentage = split_v2_percentage

    @abstractmethod
    def _post(self, data: dict):
        pass

    def _determine_endpoint(self):
        """Determine the endpoint to use."""
        endpoint = self.prediction_endpoint
        if self.prediction_v2_endpoint is not None and random.random() < self.split_v2_percentage:
            endpoint = self.prediction_v2_endpoint
        return endpoint


class SyncResource(ResourceBase):
    """Synchronous resource."""

    def _post(self, data: dict, **kwargs):
        extra_headers = kwargs.pop("headers", {})
        return requests.post(
            self._determine_endpoint(),
            json=data,
            headers=extra_headers,
        )


class AsyncResource(ResourceBase):
    """Asynchronous resource."""

    async def _post(
        self,
        data: dict,
        timeout: float = 180.0,
        read_timeout: float = 10.0,
        **kwargs,
    ):
        extra_headers = kwargs.pop("headers", {})
        timeout = httpx.Timeout(timeout=timeout, read=read_timeout)
        async with httpx.AsyncClient() as client:
            return await client.post(
                self._determine_endpoint(),
                json=data,
                timeout=timeout,
                headers=extra_headers,
            )

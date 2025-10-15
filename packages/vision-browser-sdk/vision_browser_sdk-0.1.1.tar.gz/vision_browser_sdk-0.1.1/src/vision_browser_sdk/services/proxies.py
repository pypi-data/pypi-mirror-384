# src/vision_browser_sdk/services/proxies.py

from typing import Any, Coroutine, List, Union

from ._base import BaseService
from ..models import (
    CreateProxyPayload,
    DeleteProxyPayload,
    Proxy,
    UpdateProxyPayload,
    VisionDataResponse,
)


class ProxiesService(BaseService):
    """Service for managing proxies."""

    def list(self, folder_id: str) -> Union[List[Proxy], Coroutine[Any, Any, List[Proxy]]]:
        """Retrieves a list of proxies within a specific folder."""
        response = self._get(f"folders/{folder_id}/proxies", VisionDataResponse[List[Proxy]])

        if isinstance(response, Coroutine):
            async def await_and_extract() -> List[Proxy]:
                return (await response).data

            return await_and_extract()

        return response.data

    def create(self, folder_id: str, payload: CreateProxyPayload) -> Union[
        List[Proxy], Coroutine[Any, Any, List[Proxy]]
    ]:
        """Creates one or more new proxies in a folder."""
        response = self._post(f"folders/{folder_id}/proxies", VisionDataResponse[List[Proxy]], payload)

        if isinstance(response, Coroutine):
            async def await_and_extract() -> List[Proxy]:
                return (await response).data

            return await_and_extract()

        return response.data

    def update(self, folder_id: str, proxy_id: str, payload: UpdateProxyPayload) -> Union[
        Proxy, Coroutine[Any, Any, Proxy]
    ]:
        """Updates an existing proxy."""
        response = self._put(f"folders/{folder_id}/proxies/{proxy_id}", VisionDataResponse[Proxy], payload)

        if isinstance(response, Coroutine):
            async def await_and_extract() -> Proxy:
                return (await response).data

            return await_and_extract()

        return response.data

    def delete(self, folder_id: str, payload: DeleteProxyPayload) -> Union[
        List[Proxy], Coroutine[Any, Any, List[Proxy]]
    ]:
        """Deletes one or more proxies."""
        response = self._delete(f"folders/{folder_id}/proxies", VisionDataResponse[List[Proxy]], payload)

        if isinstance(response, Coroutine):
            async def await_and_extract() -> List[Proxy]:
                return (await response).data

            return await_and_extract()

        return response.data

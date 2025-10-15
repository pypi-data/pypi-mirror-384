# src/vision_browser_sdk/services/statuses.py

from typing import Any, Coroutine, List, Union

from ..models import (
    CreateStatusesPayload,
    DeleteStatusesPayload,
    Status,
    UpdateStatusPayload,
    VisionDataResponse,
)
from ._base import BaseService


class StatusesService(BaseService):
    """Service for managing statuses."""

    def list(self, folder_id: str) -> Union[List[Status], Coroutine[Any, Any, List[Status]]]:
        """Retrieves a list of statuses within a specific folder."""
        response = self._get(f"folders/{folder_id}/statuses", VisionDataResponse[List[Status]])

        if isinstance(response, Coroutine):
            async def await_and_extract() -> List[Status]:
                return (await response).data

            return await_and_extract()

        return response.data

    def create(self, folder_id: str, payload: CreateStatusesPayload) -> Union[
        List[Status], Coroutine[Any, Any, List[Status]]
    ]:
        """Creates one or more new statuses in a folder."""
        response = self._post(f"folders/{folder_id}/statuses", VisionDataResponse[List[Status]], payload)

        if isinstance(response, Coroutine):
            async def await_and_extract() -> List[Status]:
                return (await response).data

            return await_and_extract()

        return response.data

    def update(self, folder_id: str, status_id: str, payload: UpdateStatusPayload) -> Union[
        Status, Coroutine[Any, Any, Status]
    ]:
        """Updates an existing status."""
        response = self._put(f"folders/{folder_id}/statuses/{status_id}", VisionDataResponse[Status], payload)

        if isinstance(response, Coroutine):
            async def await_and_extract() -> Status:
                return (await response).data

            return await_and_extract()

        return response.data

    def delete(self, folder_id: str, payload: DeleteStatusesPayload) -> Union[None, Coroutine[Any, Any, None]]:
        """Deletes one or more statuses."""
        response = self._delete(f"folders/{folder_id}/statuses", VisionDataResponse, payload)

        if isinstance(response, Coroutine):
            async def await_and_return() -> None:
                await response

            return await_and_return()

        return None
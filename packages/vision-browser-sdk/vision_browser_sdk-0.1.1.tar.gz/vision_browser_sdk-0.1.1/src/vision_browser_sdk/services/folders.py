# src/vision_browser_sdk/services/folders.py

from typing import Any, Coroutine, List, Union

from ..models import CreateFolderPayload, Folder, UpdateFolderPayload, VisionDataResponse
from ._base import BaseService


class FoldersService(BaseService):
    """Service for managing folders."""

    def list(self) -> Union[List[Folder], Coroutine[Any, Any, List[Folder]]]:
        """Retrieves a list of all folders."""
        response = self._get("folders", VisionDataResponse[List[Folder]])

        if isinstance(response, Coroutine):
            async def await_and_extract() -> List[Folder]:
                return (await response).data

            return await_and_extract()

        return response.data

    def create(self, payload: CreateFolderPayload) -> Union[Folder, Coroutine[Any, Any, Folder]]:
        """Creates a new folder."""
        # The API returns an array with a single element in the 'data' field.
        response = self._post("folders", VisionDataResponse[List[Folder]], payload)

        if isinstance(response, Coroutine):
            async def await_and_extract() -> Folder:
                return (await response).data[0]

            return await_and_extract()

        return response.data[0]

    def update(self, folder_id: str, payload: UpdateFolderPayload) -> Union[Folder, Coroutine[Any, Any, Folder]]:
        """Updates an existing folder."""
        response = self._patch(f"folders/{folder_id}", VisionDataResponse[List[Folder]], payload)

        if isinstance(response, Coroutine):
            async def await_and_extract() -> Folder:
                return (await response).data[0]

            return await_and_extract()

        return response.data[0]

    def delete(self, folder_id: str) -> Union[None, Coroutine[Any, Any, None]]:
        """Deletes a folder."""
        response = self._delete(f"folders/{folder_id}", VisionDataResponse[List])

        if isinstance(response, Coroutine):
            async def await_and_return_none() -> None:
                await response
                return None

            return await_and_return_none()

        return None
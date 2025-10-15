# src/vision_browser_sdk/services/tags.py

from typing import Any, Coroutine, List, Union

from ..models import (
    CreateTagsPayload,
    DeleteTagsPayload,
    Tag,
    UpdateTagPayload,
    VisionDataResponse,
)
from ._base import BaseService


class TagsService(BaseService):
    """Service for managing tags."""

    def list(self, folder_id: str) -> Union[List[Tag], Coroutine[Any, Any, List[Tag]]]:
        """Retrieves a list of tags within a specific folder."""
        response = self._get(f"folders/{folder_id}/tags", VisionDataResponse[List[Tag]])

        if isinstance(response, Coroutine):
            async def await_and_extract() -> List[Tag]:
                return (await response).data
            return await_and_extract()

        return response.data

    def create(self, folder_id: str, payload: CreateTagsPayload) -> Union[List[Tag], Coroutine[Any, Any, List[Tag]]]:
        """Creates one or more new tags in a folder."""
        response = self._post(f"folders/{folder_id}/tags", VisionDataResponse[List[Tag]], payload)

        if isinstance(response, Coroutine):
            async def await_and_extract() -> List[Tag]:
                return (await response).data
            return await_and_extract()

        return response.data

    def update(self, folder_id: str, tag_id: str, payload: UpdateTagPayload) -> Union[Tag, Coroutine[Any, Any, Tag]]:
        """Updates an existing tag."""
        response = self._put(f"folders/{folder_id}/tags/{tag_id}", VisionDataResponse[Tag], payload)

        if isinstance(response, Coroutine):
            async def await_and_extract() -> Tag:
                return (await response).data
            return await_and_extract()

        return response.data

    def delete(self, folder_id: str, payload: DeleteTagsPayload) -> Union[List[Tag], Coroutine[Any, Any, List[Tag]]]:
        """Deletes one or more tags."""
        response = self._delete(f"folders/{folder_id}/tags", VisionDataResponse[List[Tag]], payload)

        if isinstance(response, Coroutine):
            async def await_and_extract() -> List[Tag]:
                return (await response).data
            return await_and_extract()

        return response.data
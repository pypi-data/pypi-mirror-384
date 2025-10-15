# src/vision_browser_sdk/services/profiles.py

from typing import Any, Coroutine, List, Union

from ._base import BaseService
from ..models import (
    Cookie,
    CreateProfilePayload,
    FingerprintData,
    ImportCookiesPayload,
    Profile,
    ProfileList,
    UpdateProfilePayload,
    VisionDataResponse,
)


class ProfilesService(BaseService):
    """Service for managing profiles."""

    def list(self, folder_id: str) -> Union[ProfileList, Coroutine[Any, Any, ProfileList]]:
        """
        Retrieves a list of profiles within a specific folder.
        :param folder_id: The ID of the folder to retrieve profiles from.
        :return: A list of profiles or a coroutine that resolves to a list of profiles.
        """
        response = self._get(f"folders/{folder_id}/profiles", VisionDataResponse[ProfileList])

        if isinstance(response, Coroutine):
            async def await_and_extract() -> ProfileList:
                return (await response).data

            return await_and_extract()

        return response.data

    def get_info(self, folder_id: str, profile_id: str) -> Union[Profile, Coroutine[Any, Any, Profile]]:
        """
        Retrieves detailed information about a specific profile.
        :param folder_id: The ID of the folder containing the profile.
        :param profile_id: The ID of the profile to retrieve.
        :return: The profile information or a coroutine that resolves to the profile information.
        """
        response = self._get(f"folders/{folder_id}/profiles/{profile_id}", VisionDataResponse[Profile])

        if isinstance(response, Coroutine):
            async def await_and_extract() -> Profile:
                return (await response).data

            return await_and_extract()

        return response.data

    def create(self, folder_id: str, payload: CreateProfilePayload) -> Union[Profile, Coroutine[Any, Any, Profile]]:
        """
        Creates a new profile in a specified folder.
        :param folder_id: The ID of the folder to create the profile in.
        :param payload: The payload containing profile creation details.
        :return: The created profile or a coroutine that resolves to the created profile.
        """
        response = self._post(f"folders/{folder_id}/profiles", VisionDataResponse[Profile], payload)

        if isinstance(response, Coroutine):
            async def await_and_extract() -> Profile:
                return (await response).data

            return await_and_extract()

        return response.data

    def update(
            self, folder_id: str, profile_id: str, payload: UpdateProfilePayload
    ) -> Union[Profile, Coroutine[Any, Any, Profile]]:
        """
        Updates an existing profile.
        :param folder_id: The ID of the folder containing the profile.
        :param profile_id: The ID of the profile to update.
        :param payload: The payload containing profile update details.
        :return: The updated profile or a coroutine that resolves to the updated profile.
        """
        response = self._patch(f"folders/{folder_id}/profiles/{profile_id}", VisionDataResponse[Profile], payload)

        if isinstance(response, Coroutine):
            async def await_and_extract() -> Profile:
                return (await response).data

            return await_and_extract()

        return response.data

    def delete(self, folder_id: str, profile_id: str) -> Union[None, Coroutine[Any, Any, None]]:
        """
        Deletes a specific profile.
        :param folder_id: The ID of the folder containing the profile.
        :param profile_id: The ID of the profile to delete.
        :return: None or a coroutine that resolves to None.
        """
        response = self._delete(f"folders/{folder_id}/profiles/{profile_id}", VisionDataResponse)

        if isinstance(response, Coroutine):
            async def await_and_return() -> None:
                await response

            return await_and_return()

        return None

    def get_fingerprint(self, platform: str, version: str = "latest") -> Union[dict, Coroutine[Any, Any, dict]]:
        """
        Retrieves fingerprint data for a specified platform and version.
        :param platform: The platform for which to retrieve fingerprint data (e.g., 'windows', 'mac', 'linux').
        :param version: The version of the fingerprint data to retrieve (default is 'latest').
        :return: A dictionary containing fingerprint data or a coroutine that resolves to the fingerprint data.
        """
        response = self._get(f"fingerprints/{platform}/{version}", VisionDataResponse[FingerprintData])

        if isinstance(response, Coroutine):
            async def await_and_extract() -> dict:
                return (await response).data.fingerprint

            return await_and_extract()

        return response.data.fingerprint

    def export_cookies(self, folder_id: str, profile_id: str) -> Union[List[Cookie], Coroutine[Any, Any, List[Cookie]]]:
        """
        Exports cookies from a specific profile.
        :param folder_id: The ID of the folder containing the profile.
        :param profile_id: The ID of the profile from which to export cookies.
        :return: A list of cookies or a coroutine that resolves to a list of cookies.
        """
        response = self._get(f"cookies/{folder_id}/{profile_id}", VisionDataResponse[List[Cookie]])

        if isinstance(response, Coroutine):
            async def await_and_extract() -> List[Cookie]:
                return (await response).data

            return await_and_extract()

        return response.data

    def import_cookies(
            self, folder_id: str, profile_id: str, payload: ImportCookiesPayload
    ) -> Union[None, Coroutine[Any, Any, None]]:
        """
        Imports cookies into a specific profile.
        :param folder_id: The ID of the folder containing the profile.
        :param profile_id: The ID of the profile into which to import cookies.
        :param payload: The payload containing cookies to import.
        :return: None or a coroutine that resolves to None.
        """
        response = self._post(f"cookies/import/{folder_id}/{profile_id}", VisionDataResponse, payload=payload)

        if isinstance(response, Coroutine):
            async def await_and_return() -> None:
                await response

            return await_and_return()

        return None

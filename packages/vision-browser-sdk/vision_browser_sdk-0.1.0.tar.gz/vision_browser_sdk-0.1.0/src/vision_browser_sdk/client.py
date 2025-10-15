# src/vision_browser_sdk/client.py

from typing import List, Optional

import httpx

from .exceptions import VisionAPIError
from .models import (RunningProfile, RunningProfileInfo, RunningProfileListResponse, StartProfilePayload)
from .services.folders import FoldersService
from .services.profiles import ProfilesService
from .services.proxies import ProxiesService
from .services.statuses import StatusesService
from .services.tags import TagsService


class _BaseClient:
    """
    A base client that initializes all API services.
    This avoids code duplication between the sync and async clients.
    """
    folder: FoldersService
    profile: ProfilesService
    proxy: ProxiesService
    status: StatusesService
    tag: TagsService

    def __init__(self, cloud_client: httpx.Client | httpx.AsyncClient):
        self.profile = ProfilesService(cloud_client)
        self.folder = FoldersService(cloud_client)
        self.proxy = ProxiesService(cloud_client)
        self.status = StatusesService(cloud_client)
        self.tag = TagsService(cloud_client)


class VisionBrowserClient(_BaseClient):
    """Synchronous client for the Vision Browser API."""

    def __init__(self, token: str,
                 cloud_base_url: str = "https://v1.empr.cloud/api/v1",
                 local_base_url: str = "http://127.0.0.1:3030"):
        if not token:
            raise ValueError("API token is required.")

        headers = {"X-Token": token, "Content-Type": "application/json"}
        self._cloud_client = httpx.Client(base_url=cloud_base_url, headers=headers, timeout=30.0)
        self._local_client = httpx.Client(base_url=local_base_url, headers={"X-Token": token}, timeout=10.0)

        # Initialize all services from the base class
        super().__init__(self._cloud_client)

    # --- Local API Methods ---
    def get_running_profiles(self) -> List[RunningProfile]:
        """Retrieves a list of currently running profiles."""
        response = self._local_client.get("/list")
        response.raise_for_status()
        return RunningProfileListResponse.model_validate(response.json()).profiles

    def start_profile(
            self, folder_id: str, profile_id: str, payload: Optional[StartProfilePayload] = None
    ) -> RunningProfileInfo:
        """Starts a profile and returns its connection info."""
        json_data = payload.model_dump(by_alias=True, exclude_none=True) if payload else None

        if json_data:
            response = self._local_client.post(f"/start/{folder_id}/{profile_id}", json=json_data)
        else:
            response = self._local_client.get(f"/start/{folder_id}/{profile_id}")

        response.raise_for_status()
        data = response.json()
        if not data.get("port"):
            raise VisionAPIError("Profile started, but port was not returned. It might be already running.")
        return RunningProfileInfo.model_validate(data)

    def stop_profile(self, folder_id: str, profile_id: str) -> str:
        """Stops a running profile."""
        response = self._local_client.get(f"/stop/{folder_id}/{profile_id}")
        response.raise_for_status()
        return response.text

    def close(self):
        """Closes the HTTP sessions."""
        self._cloud_client.close()
        self._local_client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class AsyncVisionBrowserClient(_BaseClient):
    """Asynchronous client for the Vision Browser API."""

    def __init__(self, token: str,
                 cloud_base_url: str = "https://v1.empr.cloud/api/v1",
                 local_base_url: str = "http://127.0.0.1:3030"):
        if not token:
            raise ValueError("API token is required.")

        headers = {"X-Token": token, "Content-Type": "application/json"}
        self._cloud_client = httpx.AsyncClient(base_url=cloud_base_url, headers=headers, timeout=30.0)
        self._local_client = httpx.AsyncClient(base_url=local_base_url, headers={"X-Token": token}, timeout=10.0)

        # Initialize all services from the base class
        super().__init__(self._cloud_client)

    # --- Local API Methods ---
    async def get_running_profiles(self) -> List[RunningProfile]:
        """Retrieves a list of currently running profiles."""
        response = await self._local_client.get("/list")
        response.raise_for_status()
        return RunningProfileListResponse.model_validate(response.json()).profiles

    async def start_profile(
            self, folder_id: str, profile_id: str, payload: Optional[StartProfilePayload] = None
    ) -> RunningProfileInfo:
        """Starts a profile and returns its connection info."""
        json_data = payload.model_dump(by_alias=True, exclude_none=True) if payload else None

        if json_data:
            response = await self._local_client.post(f"/start/{folder_id}/{profile_id}", json=json_data)
        else:
            response = await self._local_client.get(f"/start/{folder_id}/{profile_id}")

        response.raise_for_status()
        data = response.json()
        if not data.get("port"):
            raise VisionAPIError("Profile started, but port was not returned. It might be already running.")
        return RunningProfileInfo.model_validate(data)

    async def stop_profile(self, folder_id: str, profile_id: str) -> str:
        """Stops a running profile."""
        response = await self._local_client.get(f"/stop/{folder_id}/{profile_id}")
        response.raise_for_status()
        return response.text

    async def close(self):
        """Closes the HTTP sessions."""
        await self._cloud_client.aclose()
        await self._local_client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

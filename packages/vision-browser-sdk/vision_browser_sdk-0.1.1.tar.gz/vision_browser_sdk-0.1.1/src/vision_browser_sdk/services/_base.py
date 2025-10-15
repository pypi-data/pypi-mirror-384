# src/vision_browser_sdk/services/_base.py

from typing import Any, Coroutine, Optional, Type, TypeVar, Union

import httpx
from pydantic import BaseModel

from ..exceptions import VisionAPIError, VisionAPIRequestError

ResponseType = TypeVar('ResponseType', bound=BaseModel)


class BaseService:
    """
    A base service that encapsulates all HTTP request logic.

    It provides convenient wrapper methods (_get, _post, etc.) for derived services
    and seamlessly handles both synchronous and asynchronous execution.
    """

    def __init__(self, client: Union[httpx.Client, httpx.AsyncClient]):
        self._client = client

    # --- Public wrapper methods for use in derived services ---

    def _get(self, endpoint: str, response_model: Type[ResponseType]) -> Union[
        ResponseType, Coroutine[Any, Any, ResponseType]]:
        """Executes a GET request."""
        return self._request("GET", endpoint, response_model)

    def _post(self, endpoint: str, response_model: Type[ResponseType], payload: BaseModel) -> Union[
        ResponseType, Coroutine[Any, Any, ResponseType]]:
        """Executes a POST request with a payload."""
        return self._request("POST", endpoint, response_model, payload=payload)

    def _patch(self, endpoint: str, response_model: Type[ResponseType], payload: BaseModel) -> Union[
        ResponseType, Coroutine[Any, Any, ResponseType]]:
        """Executes a PATCH request with a payload."""
        return self._request("PATCH", endpoint, response_model, payload=payload)

    def _delete(self, endpoint: str, response_model: Type[ResponseType], payload: Optional[BaseModel] = None) -> Union[
        ResponseType, Coroutine[Any, Any, ResponseType]]:
        """Executes a DELETE request, which may optionally include a payload."""
        return self._request("DELETE", endpoint, response_model, payload=payload)

    def _put(self, endpoint: str, response_model: Type[ResponseType], payload: BaseModel) -> Union[
        ResponseType, Coroutine[Any, Any, ResponseType]]:
        """Executes a PUT request with a payload."""
        return self._request("PUT", endpoint, response_model, payload=payload)

    # --- Core Request Engine ---

    def _request(
            self,
            method: str,
            endpoint: str,
            response_model: Type[ResponseType],
            payload: Optional[BaseModel] = None,
    ) -> Union[ResponseType, Coroutine[Any, Any, ResponseType]]:
        """
        A universal method for executing sync/async requests.

        Returns either a validated Pydantic model or a coroutine
        that will return that model upon await.
        """
        # Serialize the Pydantic model into a dict for JSON, excluding fields with a None value.
        json_data = payload.model_dump(by_alias=True, exclude_none=True) if payload else None

        if isinstance(self._client, httpx.AsyncClient):
            return self._async_request_executor(method, endpoint, response_model, json_data)
        else:
            return self._sync_request_executor(method, endpoint, response_model, json_data)

    # --- Request Executors for each mode ---

    def _sync_request_executor(
            self, method: str, url: str, response_model: Type[ResponseType], json_data: Optional[dict]
    ) -> ResponseType:
        """Synchronous request executor."""
        try:
            response = self._client.request(method, url, json=json_data)
            # Raise an exception for 4xx/5xx status codes.
            response.raise_for_status()

            # Parse the entire JSON response into the specified Pydantic model.
            return response_model.model_validate(response.json())

        except httpx.HTTPStatusError as e:
            # Wrap the HTTP error in our custom exception for better error handling.
            raise VisionAPIRequestError(e.response.status_code, e.response.text) from e
        except Exception as e:
            # Catch other potential errors (e.g., JSON decoding, network issues).
            raise VisionAPIError(f"An unexpected error occurred: {e}") from e

    async def _async_request_executor(
            self, method: str, url: str, response_model: Type[ResponseType], json_data: Optional[dict]
    ) -> ResponseType:
        """Asynchronous request executor."""
        try:
            response = await self._client.request(method, url, json=json_data)
            response.raise_for_status()

            return response_model.model_validate(response.json())

        except httpx.HTTPStatusError as e:
            raise VisionAPIRequestError(e.response.status_code, e.response.text) from e
        except Exception as e:
            raise VisionAPIError(f"An unexpected error occurred: {e}") from e

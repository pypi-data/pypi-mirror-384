import os
import httpx
from typing import Any


API_VERSION = "1"
BASE_URL = f"https://aristotle.harmonic.fun/api/v{API_VERSION}"
DEFAULT_TIMEOUT_SECONDS = 30

API_KEY: str | None = None


def get_api_key() -> str:
    global API_KEY
    api_key = API_KEY or os.environ.get("ARISTOTLE_API_KEY")
    if api_key is None:
        raise ValueError(
            "API key has not been set. Call aristotle.set_api_key() or set the ARISTOTLE_API_KEY environment variable."
        )
    return api_key


def set_api_key(api_key: str) -> str:
    global API_KEY
    API_KEY = api_key
    return API_KEY


class AristotleRequestClient:
    """Async HTTP client for the Aristotle API."""

    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_SECONDS)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    async def get(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> httpx.Response:
        """Make a GET request."""
        return await self._make_request("GET", endpoint, params=params)

    async def post(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        files: list[tuple[str, tuple[str, bytes, str]]] | None = None,
    ) -> httpx.Response:
        """Make a POST request."""
        return await self._make_request("POST", endpoint, params=params, files=files)

    async def put(
        self, endpoint: str, data: dict[str, Any] | None = None
    ) -> httpx.Response:
        """Make a PUT request."""
        return await self._make_request("PUT", endpoint, data=data)

    async def delete(self, endpoint: str) -> httpx.Response:
        """Make a DELETE request."""
        return await self._make_request("DELETE", endpoint)

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        files: list[tuple[str, tuple[str, bytes, str]]] | None = None,
    ) -> httpx.Response:
        """Make an HTTP request to the Aristotle API."""
        url = f"{BASE_URL}/{endpoint.lstrip('/')}"
        headers = {
            "X-API-Key": get_api_key(),
        }

        if not self._client:
            self._client = httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_SECONDS)

        try:
            if files:
                # For file uploads, use multipart/form-data
                files_data = []
                for field_name, (file_path, file_content, content_type) in files:
                    files_data.append(
                        (field_name, (file_path, file_content, content_type))
                    )

                response = await self._client.request(
                    method=method,
                    url=url,
                    data=data,
                    files=files_data,
                    params=params,
                    headers=headers,
                )
            else:
                # For regular requests, use JSON
                headers["Content-Type"] = "application/json"
                response = await self._client.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=headers,
                )
            response.raise_for_status()
            return response
        except httpx.RequestError as e:
            raise AristotleAPIError(f"Request failed: {str(e)}") from e

    async def close(self):
        """Close the async client."""
        if self._client:
            await self._client.aclose()
            self._client = None


class AristotleAPIError(Exception):
    """Exception raised for API-related errors."""

    pass

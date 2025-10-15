import json
from typing import Any, Dict, Optional

import httpx

from .exceptions import (
    ReplicatedAPIError,
    ReplicatedAuthError,
    ReplicatedNetworkError,
    ReplicatedRateLimitError,
)


class HTTPClient:
    """Base HTTP client for making requests to the Replicated API."""

    def __init__(
        self,
        base_url: str = "https://replicated.app",
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.default_headers = headers or {}

    def _build_headers(
        self, headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Build request headers."""
        # Import here to avoid circular import
        from . import __version__

        # Format: "Replicated-SDK/{version}" as expected by Vandoor
        user_agent = f"Replicated-SDK/{__version__}"
        request_headers = {
            "Content-Type": "application/json",
            "User-Agent": user_agent,
            **self.default_headers,
        }
        if headers:
            request_headers.update(headers)
        return request_headers

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle HTTP response and raise appropriate exceptions."""
        try:
            json_body = response.json() if response.content else {}
        except json.JSONDecodeError:
            json_body = {}

        if response.is_success:
            return json_body

        default_msg = f"HTTP {response.status_code}"
        error_message = json_body.get("message", default_msg)
        error_code = json_body.get("code")

        if response.status_code == 401:
            raise ReplicatedAuthError(
                message=error_message,
                http_status=response.status_code,
                http_body=response.text,
                json_body=json_body,
                headers=dict(response.headers),
                code=error_code,
            )
        elif response.status_code == 429:
            raise ReplicatedRateLimitError(
                message=error_message,
                http_status=response.status_code,
                http_body=response.text,
                json_body=json_body,
                headers=dict(response.headers),
                code=error_code,
            )
        elif 400 <= response.status_code < 500:
            raise ReplicatedAPIError(
                message=error_message,
                http_status=response.status_code,
                http_body=response.text,
                json_body=json_body,
                headers=dict(response.headers),
                code=error_code,
            )
        else:
            raise ReplicatedAPIError(
                message=error_message,
                http_status=response.status_code,
                http_body=response.text,
                json_body=json_body,
                headers=dict(response.headers),
                code=error_code,
            )

    def _make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a synchronous HTTP request."""
        raise NotImplementedError("Subclasses must implement _make_request")

    async def _make_request_async(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an asynchronous HTTP request."""
        raise NotImplementedError("Subclasses must implement _make_request_async")


class SyncHTTPClient(HTTPClient):
    """Synchronous HTTP client."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._client: Optional[httpx.Client] = None

    def __enter__(self) -> "SyncHTTPClient":
        self._client = httpx.Client(timeout=self.timeout)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._client:
            self._client.close()
            self._client = None

    def _make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a synchronous HTTP request."""
        if not self._client:
            self._client = httpx.Client(timeout=self.timeout)

        full_url = f"{self.base_url}{url}"
        request_headers = self._build_headers(headers)

        try:
            response = self._client.request(
                method=method,
                url=full_url,
                headers=request_headers,
                json=json_data,
                params=params,
            )
            return self._handle_response(response)
        except httpx.RequestError as e:
            raise ReplicatedNetworkError(f"Network error: {str(e)}")


class AsyncHTTPClient(HTTPClient):
    """Asynchronous HTTP client."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "AsyncHTTPClient":
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _make_request_async(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an asynchronous HTTP request."""
        if not self._client:
            self._client = httpx.AsyncClient(timeout=self.timeout)

        full_url = f"{self.base_url}{url}"
        request_headers = self._build_headers(headers)

        try:
            response = await self._client.request(
                method=method,
                url=full_url,
                headers=request_headers,
                json=json_data,
                params=params,
            )
            return self._handle_response(response)
        except httpx.RequestError as e:
            raise ReplicatedNetworkError(f"Network error: {str(e)}")

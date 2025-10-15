"""
HTTP session management for the Konigle SDK.

This module provides both synchronous and asynchronous HTTP session wrappers
that handle authentication, connection pooling, error handling, and logging
for all API communications.
"""

import time
from typing import Any, Dict, Optional

import httpx

from .config import ClientConfig
from .exceptions import KonigleTimeoutError, NetworkError, map_http_error
from .logging import get_logger


class BaseSession:
    """Base session class with shared functionality."""

    def __init__(self, config: ClientConfig):
        self.config = config
        self.logger = get_logger()
        self._closed = False

    def _create_common_headers(self) -> Dict[str, str]:
        """Create common headers for all requests (no Content-Type)."""
        return {
            "Authorization": f"Token {self.config.api_key}",
            "User-Agent": self.config.get_user_agent(),
            "Accept": "application/json",
        }

    def _add_json_headers_if_needed(self, kwargs: Dict[str, Any]) -> None:
        """Add Content-Type header for JSON requests if not already present."""
        if "json" in kwargs and "headers" not in kwargs:
            kwargs["headers"] = {"Content-Type": "application/json"}
        elif "json" in kwargs and "headers" in kwargs:
            headers = kwargs["headers"].copy()
            if "content-type" not in {k.lower() for k in headers.keys()}:
                headers["Content-Type"] = "application/json"
            kwargs["headers"] = headers

    def _create_timeout(self) -> httpx.Timeout:
        """Create timeout configuration."""
        return httpx.Timeout(self.config.timeout)

    def _create_limits(self) -> httpx.Limits:
        """Create connection limits configuration."""
        limits_config = self.config.get_http_limits()
        return httpx.Limits(
            max_keepalive_connections=limits_config[
                "max_keepalive_connections"
            ],
            max_connections=limits_config["max_connections"],
            keepalive_expiry=limits_config["keepalive_expiry"],
        )

    def _log_request(self, method: str, url: str, **kwargs):
        """Log outgoing HTTP requests."""
        if not self.config.log_requests:
            return

        self.logger.debug(
            f"HTTP Request: {method} {url}",
            extra={
                "http_method": method,
                "url": url,
                "headers": kwargs.get("headers", {}),
                "params": kwargs.get("params", {}),
            },
        )

    def _log_response(self, response: httpx.Response, duration: float):
        """Log HTTP responses."""
        if not self.config.log_responses:
            return

        log_level = (
            self.logger.debug if response.is_success else self.logger.warning
        )

        log_level(
            f"HTTP Response: {response.status_code} ({duration:.3f}s)",
            extra={
                "status_code": response.status_code,
                "response_time": duration,
                "url": str(response.url),
                "headers": dict(response.headers),
            },
        )

    def _handle_response(self, response: httpx.Response) -> httpx.Response:
        """Convert HTTP errors to structured exceptions."""
        if response.is_success:
            return response

        # Extract error details
        try:
            error_data = response.json()
            message = error_data.get(
                "detail",
                error_data.get("message", f"HTTP {response.status_code}"),
            )
        except (ValueError, KeyError):
            message = f"HTTP {response.status_code}: {response.text[:200]}"
            error_data = {}

        # Map status code to specific exception
        raise map_http_error(response.status_code, message, error_data)


class SyncSession(BaseSession):
    """Synchronous HTTP session wrapper."""

    def __init__(self, config: ClientConfig):
        super().__init__(config)
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        """Get or create synchronous HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = self._create_client()
        return self._client

    def _create_client(self) -> httpx.Client:
        """Create configured synchronous HTTP client."""
        return httpx.Client(
            base_url=self.config.base_url,
            headers=self._create_common_headers(),
            timeout=self._create_timeout(),
            limits=self._create_limits(),
            follow_redirects=True,
        )

    def _make_request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make HTTP request with logging and error handling."""
        self._log_request(method, url, **kwargs)
        start_time = time.time()

        try:
            response = self.client.request(method, url, **kwargs)
            duration = time.time() - start_time
            self._log_response(response, duration)
            return self._handle_response(response)

        except httpx.TimeoutException as e:
            duration = time.time() - start_time
            self.logger.error(
                f"HTTP Request Timeout: {method} {url} ({duration:.3f}s)"
            )
            raise KonigleTimeoutError(
                f"Request timed out after {self.config.timeout}s"
            ) from e

        except httpx.NetworkError as e:
            duration = time.time() - start_time
            self.logger.error(
                f"HTTP Network Error: {method} {url} ({duration:.3f}s): {str(e)}"
            )
            raise NetworkError(f"Network error: {str(e)}") from e

        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                f"HTTP Request Failed: {method} {url} ({duration:.3f}s): {str(e)}",
                exc_info=True,
            )
            raise

    def get(self, url: str, **kwargs) -> httpx.Response:
        """Make GET request."""
        return self._make_request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> httpx.Response:
        """Make POST request."""
        self._add_json_headers_if_needed(kwargs)
        return self._make_request("POST", url, **kwargs)

    def patch(self, url: str, **kwargs) -> httpx.Response:
        """Make PATCH request."""
        self._add_json_headers_if_needed(kwargs)
        return self._make_request("PATCH", url, **kwargs)

    def put(self, url: str, **kwargs) -> httpx.Response:
        """Make PUT request."""
        self._add_json_headers_if_needed(kwargs)
        return self._make_request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs) -> httpx.Response:
        """Make DELETE request."""
        return self._make_request("DELETE", url, **kwargs)

    def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            self._client.close()
        self._closed = True


class AsyncSession(BaseSession):
    """Asynchronous HTTP session wrapper."""

    def __init__(self, config: ClientConfig):
        super().__init__(config)
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create asynchronous HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = self._create_client()
        return self._client

    def _create_client(self) -> httpx.AsyncClient:
        """Create configured asynchronous HTTP client."""
        return httpx.AsyncClient(
            base_url=self.config.base_url,
            headers=self._create_common_headers(),
            timeout=self._create_timeout(),
            limits=self._create_limits(),
            follow_redirects=True,
        )

    async def _make_request(
        self, method: str, url: str, **kwargs
    ) -> httpx.Response:
        """Make async HTTP request with logging and error handling."""
        self._log_request(method, url, **kwargs)
        start_time = time.time()

        try:
            response = await self.client.request(method, url, **kwargs)
            duration = time.time() - start_time
            self._log_response(response, duration)
            return self._handle_response(response)

        except httpx.TimeoutException as e:
            duration = time.time() - start_time
            self.logger.error(
                f"HTTP Request Timeout: {method} {url} ({duration:.3f}s)"
            )
            raise KonigleTimeoutError(
                f"Request timed out after {self.config.timeout}s"
            ) from e

        except httpx.NetworkError as e:
            duration = time.time() - start_time
            self.logger.error(
                f"HTTP Network Error: {method} {url} ({duration:.3f}s): {str(e)}"
            )
            raise NetworkError(f"Network error: {str(e)}") from e

        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                f"HTTP Request Failed: {method} {url} ({duration:.3f}s): {str(e)}",
                exc_info=True,
            )
            raise

    async def get(self, url: str, **kwargs) -> httpx.Response:
        """Make async GET request."""
        return await self._make_request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        """Make async POST request."""
        self._add_json_headers_if_needed(kwargs)
        return await self._make_request("POST", url, **kwargs)

    async def patch(self, url: str, **kwargs) -> httpx.Response:
        """Make async PATCH request."""
        self._add_json_headers_if_needed(kwargs)
        return await self._make_request("PATCH", url, **kwargs)

    async def put(self, url: str, **kwargs) -> httpx.Response:
        """Make async PUT request."""
        self._add_json_headers_if_needed(kwargs)
        return await self._make_request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs) -> httpx.Response:
        """Make async DELETE request."""
        return await self._make_request("DELETE", url, **kwargs)

    async def aclose(self):
        """Close the async HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
        self._closed = True

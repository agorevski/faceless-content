"""
Base HTTP client with retry logic and error handling.

This module provides a base class for all HTTP clients in the application,
implementing common patterns like retries, timeouts, and structured logging.
"""

from typing import Any, TypeVar
from collections.abc import Callable

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from faceless.config import get_settings
from faceless.core.exceptions import ClientError, RateLimitError
from faceless.utils.logging import get_logger, LoggerMixin

T = TypeVar("T")

class BaseHTTPClient(LoggerMixin):
    """
    Base HTTP client with retry logic and structured logging.

    Provides common functionality for all API clients:
    - Automatic retries with exponential backoff
    - Request/response logging
    - Timeout handling
    - Error normalization

    Subclasses should implement specific API methods using the
    protected _get, _post, etc. methods.
    """

    def __init__(
        self,
        base_url: str = "",
        timeout: float | None = None,
        max_retries: int | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        """
        Initialize the HTTP client.

        Args:
            base_url: Base URL for all requests
            timeout: Request timeout in seconds (uses settings default if None)
            max_retries: Maximum retry attempts (uses settings default if None)
            headers: Default headers for all requests
        """
        settings = get_settings()
        self._base_url = base_url.rstrip("/") if base_url else ""
        self._timeout = timeout or settings.request_timeout
        self._max_retries = max_retries or settings.max_retries
        self._enable_retry = settings.enable_retry
        self._default_headers = headers or {}

        # Create HTTP client
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=httpx.Timeout(self._timeout),
            headers=self._default_headers,
        )

    def close(self) -> None:
        """Close the HTTP client and release resources."""
        self._client.close()

    def __enter__(self) -> "BaseHTTPClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def _build_url(self, path: str) -> str:
        """Build full URL from path."""
        if path.startswith("http"):
            return path
        return f"{self._base_url}/{path.lstrip('/')}"

    def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make an HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: URL path
            **kwargs: Additional arguments for httpx.request

        Returns:
            httpx.Response object

        Raises:
            ClientError: On request failure
            RateLimitError: On rate limit (429) response
        """
        url = self._build_url(path)
        self.logger.debug(
            "HTTP request",
            method=method,
            url=url,
            has_json="json" in kwargs,
            has_data="data" in kwargs,
        )

        try:
            response = self._client.request(method, path, **kwargs)

            # Log response
            self.logger.debug(
                "HTTP response",
                method=method,
                url=url,
                status_code=response.status_code,
                content_length=len(response.content),
            )

            # Check for rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                raise RateLimitError(
                    message="Rate limit exceeded",
                    retry_after=int(retry_after) if retry_after else None,
                    service=self.__class__.__name__,
                )

            return response

        except httpx.TimeoutException as e:
            self.logger.error("Request timeout", url=url, timeout=self._timeout)
            raise ClientError(f"Request timeout: {url}") from e

        except httpx.RequestError as e:
            self.logger.error("Request failed", url=url, error=str(e))
            raise ClientError(f"Request failed: {e}") from e

    def _get(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make a GET request."""
        return self._request("GET", path, **kwargs)

    def _post(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make a POST request."""
        return self._request("POST", path, **kwargs)

    def _put(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make a PUT request."""
        return self._request("PUT", path, **kwargs)

    def _delete(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make a DELETE request."""
        return self._request("DELETE", path, **kwargs)

    def _post_json(
        self,
        path: str,
        data: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Make a POST request with JSON body and parse JSON response.

        Args:
            path: URL path
            data: JSON payload
            **kwargs: Additional request arguments

        Returns:
            Parsed JSON response as dict
        """
        response = self._post(path, json=data, **kwargs)
        response.raise_for_status()
        return response.json()

    def _get_json(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """
        Make a GET request and parse JSON response.

        Args:
            path: URL path
            **kwargs: Additional request arguments

        Returns:
            Parsed JSON response as dict
        """
        response = self._get(path, **kwargs)
        response.raise_for_status()
        return response.json()

    def _post_binary(
        self,
        path: str,
        data: dict[str, Any],
        **kwargs: Any,
    ) -> bytes:
        """
        Make a POST request and return binary response.

        Args:
            path: URL path
            data: JSON payload
            **kwargs: Additional request arguments

        Returns:
            Binary response content
        """
        response = self._post(path, json=data, **kwargs)
        response.raise_for_status()
        return response.content

def with_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 60.0,
    retry_exceptions: tuple[type[Exception], ...] = (
        httpx.TimeoutException,
        httpx.NetworkError,
    ),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator factory for adding retry logic to functions.

    Args:
        max_attempts: Maximum number of attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)
        retry_exceptions: Exception types to retry on

    Returns:
        Decorator function

    Example:
        >>> @with_retry(max_attempts=5)
        ... def fetch_data():
        ...     return make_request()
    """
    logger = get_logger("retry")

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(retry_exceptions),
            before_sleep=before_sleep_log(logger, log_level=20),  # INFO level
            reraise=True,
        )
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return func(*args, **kwargs)

        return wrapper

    return decorator
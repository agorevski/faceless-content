"""
Unit tests for BaseHTTPClient.

Tests cover:
- Client initialization
- URL building
- HTTP methods (GET, POST, PUT, DELETE)
- Error handling
- Rate limiting
- Context manager support
"""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from faceless.core.exceptions import ClientError, RateLimitError


class TestBaseHTTPClient:
    """Tests for BaseHTTPClient."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for client initialization."""
        with patch("faceless.clients.base.get_settings") as mock:
            settings = MagicMock()
            settings.request_timeout = 120
            settings.max_retries = 3
            settings.enable_retry = True
            mock.return_value = settings
            yield settings

    @pytest.fixture
    def mock_httpx_client(self):
        """Mock httpx.Client."""
        with patch("faceless.clients.base.httpx.Client") as mock:
            yield mock

    def test_init_with_defaults(self, mock_settings, mock_httpx_client) -> None:
        """Test client initialization with defaults."""
        from faceless.clients.base import BaseHTTPClient

        client = BaseHTTPClient()
        assert client._base_url == ""
        assert client._timeout == 120
        assert client._max_retries == 3

    def test_init_with_base_url(self, mock_settings, mock_httpx_client) -> None:
        """Test client initialization with base URL."""
        from faceless.clients.base import BaseHTTPClient

        client = BaseHTTPClient(base_url="https://api.example.com/")
        assert client._base_url == "https://api.example.com"

    def test_init_with_custom_timeout(self, mock_settings, mock_httpx_client) -> None:
        """Test client initialization with custom timeout."""
        from faceless.clients.base import BaseHTTPClient

        client = BaseHTTPClient(timeout=60)
        assert client._timeout == 60

    def test_init_with_custom_retries(self, mock_settings, mock_httpx_client) -> None:
        """Test client initialization with custom retries."""
        from faceless.clients.base import BaseHTTPClient

        client = BaseHTTPClient(max_retries=5)
        assert client._max_retries == 5

    def test_init_with_headers(self, mock_settings, mock_httpx_client) -> None:
        """Test client initialization with headers."""
        from faceless.clients.base import BaseHTTPClient

        headers = {"Authorization": "Bearer token"}
        client = BaseHTTPClient(headers=headers)
        assert client._default_headers == headers

    def test_build_url_with_path(self, mock_settings, mock_httpx_client) -> None:
        """Test URL building with relative path."""
        from faceless.clients.base import BaseHTTPClient

        client = BaseHTTPClient(base_url="https://api.example.com")
        url = client._build_url("/v1/resource")
        assert url == "https://api.example.com/v1/resource"

    def test_build_url_with_absolute_url(
        self, mock_settings, mock_httpx_client
    ) -> None:
        """Test URL building with absolute URL."""
        from faceless.clients.base import BaseHTTPClient

        client = BaseHTTPClient(base_url="https://api.example.com")
        url = client._build_url("https://other.example.com/resource")
        assert url == "https://other.example.com/resource"

    def test_build_url_strips_leading_slash(
        self, mock_settings, mock_httpx_client
    ) -> None:
        """Test URL building strips leading slash from path."""
        from faceless.clients.base import BaseHTTPClient

        client = BaseHTTPClient(base_url="https://api.example.com")
        url = client._build_url("v1/resource")
        assert url == "https://api.example.com/v1/resource"

    def test_close(self, mock_settings, mock_httpx_client) -> None:
        """Test client close method."""
        from faceless.clients.base import BaseHTTPClient

        client = BaseHTTPClient()
        client.close()
        client._client.close.assert_called_once()

    def test_context_manager(self, mock_settings, mock_httpx_client) -> None:
        """Test client context manager."""
        from faceless.clients.base import BaseHTTPClient

        with BaseHTTPClient() as client:
            assert client is not None
        client._client.close.assert_called_once()

    def test_request_success(self, mock_settings, mock_httpx_client) -> None:
        """Test successful HTTP request."""
        from faceless.clients.base import BaseHTTPClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"response"
        mock_httpx_client.return_value.request.return_value = mock_response

        client = BaseHTTPClient(base_url="https://api.example.com")
        response = client._request("GET", "/test")

        assert response.status_code == 200
        client._client.request.assert_called_once()

    def test_request_rate_limit(self, mock_settings, mock_httpx_client) -> None:
        """Test rate limit handling."""
        from faceless.clients.base import BaseHTTPClient

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_httpx_client.return_value.request.return_value = mock_response

        client = BaseHTTPClient(base_url="https://api.example.com")

        with pytest.raises(RateLimitError) as exc_info:
            client._request("GET", "/test")

        assert exc_info.value.retry_after == 60

    def test_request_rate_limit_no_retry_after(
        self, mock_settings, mock_httpx_client
    ) -> None:
        """Test rate limit handling without Retry-After header."""
        from faceless.clients.base import BaseHTTPClient

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {}
        mock_httpx_client.return_value.request.return_value = mock_response

        client = BaseHTTPClient(base_url="https://api.example.com")

        with pytest.raises(RateLimitError) as exc_info:
            client._request("GET", "/test")

        assert exc_info.value.retry_after is None

    def test_request_timeout_error(self, mock_settings, mock_httpx_client) -> None:
        """Test timeout error handling."""
        from faceless.clients.base import BaseHTTPClient

        mock_httpx_client.return_value.request.side_effect = httpx.TimeoutException(
            "Timeout"
        )

        client = BaseHTTPClient(base_url="https://api.example.com")

        with pytest.raises(ClientError) as exc_info:
            client._request("GET", "/test")

        assert "timeout" in str(exc_info.value).lower()

    def test_request_network_error(self, mock_settings, mock_httpx_client) -> None:
        """Test network error handling."""
        from faceless.clients.base import BaseHTTPClient

        mock_httpx_client.return_value.request.side_effect = httpx.RequestError(
            "Connection failed"
        )

        client = BaseHTTPClient(base_url="https://api.example.com")

        with pytest.raises(ClientError) as exc_info:
            client._request("GET", "/test")

        assert "failed" in str(exc_info.value).lower()

    def test_get_method(self, mock_settings, mock_httpx_client) -> None:
        """Test GET method."""
        from faceless.clients.base import BaseHTTPClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"data"
        mock_httpx_client.return_value.request.return_value = mock_response

        client = BaseHTTPClient(base_url="https://api.example.com")
        response = client._get("/test")

        client._client.request.assert_called_with("GET", "/test")
        assert response.status_code == 200

    def test_post_method(self, mock_settings, mock_httpx_client) -> None:
        """Test POST method."""
        from faceless.clients.base import BaseHTTPClient

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.content = b"created"
        mock_httpx_client.return_value.request.return_value = mock_response

        client = BaseHTTPClient(base_url="https://api.example.com")
        response = client._post("/test", json={"key": "value"})

        client._client.request.assert_called_with(
            "POST", "/test", json={"key": "value"}
        )
        assert response.status_code == 201

    def test_put_method(self, mock_settings, mock_httpx_client) -> None:
        """Test PUT method."""
        from faceless.clients.base import BaseHTTPClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"updated"
        mock_httpx_client.return_value.request.return_value = mock_response

        client = BaseHTTPClient(base_url="https://api.example.com")
        response = client._put("/test", json={"key": "updated"})

        client._client.request.assert_called_with(
            "PUT", "/test", json={"key": "updated"}
        )

    def test_delete_method(self, mock_settings, mock_httpx_client) -> None:
        """Test DELETE method."""
        from faceless.clients.base import BaseHTTPClient

        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.content = b""
        mock_httpx_client.return_value.request.return_value = mock_response

        client = BaseHTTPClient(base_url="https://api.example.com")
        response = client._delete("/test")

        client._client.request.assert_called_with("DELETE", "/test")

    def test_post_json_method(self, mock_settings, mock_httpx_client) -> None:
        """Test POST with JSON response parsing."""
        from faceless.clients.base import BaseHTTPClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_httpx_client.return_value.request.return_value = mock_response

        client = BaseHTTPClient(base_url="https://api.example.com")
        result = client._post_json("/test", {"input": "data"})

        assert result == {"result": "success"}

    def test_get_json_method(self, mock_settings, mock_httpx_client) -> None:
        """Test GET with JSON response parsing."""
        from faceless.clients.base import BaseHTTPClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [1, 2, 3]}
        mock_httpx_client.return_value.request.return_value = mock_response

        client = BaseHTTPClient(base_url="https://api.example.com")
        result = client._get_json("/test")

        assert result == {"data": [1, 2, 3]}

    def test_post_binary_method(self, mock_settings, mock_httpx_client) -> None:
        """Test POST with binary response."""
        from faceless.clients.base import BaseHTTPClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"\x00\x01\x02"
        mock_httpx_client.return_value.request.return_value = mock_response

        client = BaseHTTPClient(base_url="https://api.example.com")
        result = client._post_binary("/test", {"format": "binary"})

        assert result == b"\x00\x01\x02"


class TestWithRetry:
    """Tests for the with_retry decorator."""

    def test_with_retry_decorator(self) -> None:
        """Test with_retry decorator exists and is callable."""
        from faceless.clients.base import with_retry

        @with_retry(max_attempts=3)
        def sample_func():
            return "success"

        result = sample_func()
        assert result == "success"

    def test_with_retry_custom_params(self) -> None:
        """Test with_retry with custom parameters."""
        from faceless.clients.base import with_retry

        @with_retry(max_attempts=5, min_wait=2.0, max_wait=30.0)
        def sample_func():
            return 42

        result = sample_func()
        assert result == 42

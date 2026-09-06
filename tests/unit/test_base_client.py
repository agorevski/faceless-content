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

from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from unittest.mock import MagicMock, patch

import httpx
import pytest

from faceless.core.exceptions import ClientError, RateLimitError


class TestBaseHTTPClient:
    """Tests for BaseHTTPClient."""

    @pytest.fixture(autouse=True)
    def retry_sleep(self) -> Generator[MagicMock, None, None]:
        with patch("tenacity.nap.time.sleep") as sleep:
            yield sleep

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

    @pytest.mark.parametrize("status_code", [408, 429, 500, 502, 503, 504])
    def test_request_retries_transient_response(
        self,
        mock_settings: MagicMock,
        mock_httpx_client: MagicMock,
        retry_sleep: MagicMock,
        status_code: int,
    ) -> None:
        from faceless.clients.base import BaseHTTPClient

        success = httpx.Response(200, content=b"success")
        mock_httpx_client.return_value.request.side_effect = [
            httpx.Response(status_code),
            success,
        ]
        client = BaseHTTPClient(base_url="https://api.example.com")

        assert client._post("/test", json={"input": "test"}) is success
        assert client._client.request.call_count == 2
        retry_sleep.assert_called_once_with(1)
        assert (
            client._client.request.call_args_list[0]
            == client._client.request.call_args_list[1]
        )

    @pytest.mark.parametrize(
        "error",
        [
            httpx.ReadTimeout("Timeout"),
            httpx.ConnectError("Connection failed"),
            httpx.RemoteProtocolError("Connection interrupted"),
        ],
    )
    def test_request_retries_transport_failure(
        self,
        mock_settings: MagicMock,
        mock_httpx_client: MagicMock,
        error: httpx.RequestError,
    ) -> None:
        from faceless.clients.base import BaseHTTPClient

        success = httpx.Response(200)
        mock_httpx_client.return_value.request.side_effect = [error, success]
        client = BaseHTTPClient(base_url="https://api.example.com")

        assert client._get("/test") is success
        assert client._client.request.call_count == 2

    @pytest.mark.parametrize("status_code", [400, 401, 403, 404, 422])
    def test_request_does_not_retry_permanent_response(
        self,
        mock_settings: MagicMock,
        mock_httpx_client: MagicMock,
        retry_sleep: MagicMock,
        status_code: int,
    ) -> None:
        from faceless.clients.base import BaseHTTPClient

        response = httpx.Response(status_code)
        mock_httpx_client.return_value.request.return_value = response
        client = BaseHTTPClient(base_url="https://api.example.com")

        assert client._get("/test") is response
        client._client.request.assert_called_once()
        retry_sleep.assert_not_called()

    @pytest.mark.parametrize("enable_retry,max_retries", [(False, 3), (True, 0)])
    def test_request_respects_retry_disable_and_zero_override(
        self,
        mock_settings: MagicMock,
        mock_httpx_client: MagicMock,
        retry_sleep: MagicMock,
        enable_retry: bool,
        max_retries: int,
    ) -> None:
        from faceless.clients.base import BaseHTTPClient

        mock_settings.enable_retry = enable_retry
        response = httpx.Response(503)
        mock_httpx_client.return_value.request.return_value = response
        client = BaseHTTPClient(max_retries=max_retries)

        assert client._max_retries == max_retries
        assert client._get("https://api.example.com/test") is response
        client._client.request.assert_called_once()
        retry_sleep.assert_not_called()

    def test_request_exhaustion_returns_last_response(
        self,
        mock_settings: MagicMock,
        mock_httpx_client: MagicMock,
        retry_sleep: MagicMock,
    ) -> None:
        from faceless.clients.base import BaseHTTPClient

        response = httpx.Response(503)
        mock_httpx_client.return_value.request.return_value = response
        client = BaseHTTPClient(max_retries=2)

        assert client._get("https://api.example.com/test") is response
        assert client._client.request.call_count == 3
        assert [call.args[0] for call in retry_sleep.call_args_list] == [1, 2]

    def test_request_exhaustion_preserves_transport_cause(
        self,
        mock_settings: MagicMock,
        mock_httpx_client: MagicMock,
    ) -> None:
        from faceless.clients.base import BaseHTTPClient

        error = httpx.ConnectError("Connection failed")
        mock_httpx_client.return_value.request.side_effect = error
        client = BaseHTTPClient(max_retries=2)

        with pytest.raises(ClientError) as exc_info:
            client._get("https://api.example.com/test")

        assert exc_info.value.__cause__ is error
        assert client._client.request.call_count == 3

    @pytest.mark.parametrize(
        "header,expected",
        [("invalid", None), ("1.5", None), ("", None), ("-1", 0), ("7", 7)],
    )
    def test_rate_limit_header_never_masks_error(
        self,
        mock_settings: MagicMock,
        mock_httpx_client: MagicMock,
        header: str,
        expected: int | None,
    ) -> None:
        from faceless.clients.base import BaseHTTPClient

        mock_httpx_client.return_value.request.return_value = httpx.Response(
            429, headers={"Retry-After": header}
        )
        client = BaseHTTPClient(max_retries=0)

        with pytest.raises(RateLimitError) as exc_info:
            client._get("https://api.example.com/test")

        assert exc_info.value.retry_after == expected

    @pytest.mark.parametrize("header,expected_wait", [("7", 7), ("999", 60), ("bad", 1)])
    def test_request_honors_bounded_retry_after(
        self,
        mock_settings: MagicMock,
        mock_httpx_client: MagicMock,
        retry_sleep: MagicMock,
        header: str,
        expected_wait: int,
    ) -> None:
        from faceless.clients.base import BaseHTTPClient

        mock_httpx_client.return_value.request.side_effect = [
            httpx.Response(429, headers={"Retry-After": header}),
            httpx.Response(200),
        ]
        client = BaseHTTPClient()

        assert client._get("https://api.example.com/test").status_code == 200
        retry_sleep.assert_called_once_with(expected_wait)

    def test_retry_after_supports_http_date(self) -> None:
        from faceless.clients.base import BaseHTTPClient

        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        response = httpx.Response(
            429,
            headers={"Retry-After": format_datetime(now + timedelta(seconds=30))},
        )
        with patch("faceless.clients.base.datetime") as clock:
            clock.now.return_value = now
            assert BaseHTTPClient._retry_after(response) == 30

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
        client._put("/test", json={"key": "updated"})

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
        client._delete("/test")

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

"""
Unit tests for AzureOpenAIClient.

Tests cover:
- Client initialization
- Image generation
- Chat completions
- Text-to-speech
- Error handling
- Utility methods
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from faceless.core.enums import Niche, Platform, Voice
from faceless.core.exceptions import (
    AzureOpenAIError,
    ContentFilterError,
    ImageGenerationError,
    TTSGenerationError,
)


class TestAzureOpenAIClient:
    """Tests for AzureOpenAIClient."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for client."""
        with patch("faceless.clients.azure_openai.get_settings") as mock:
            settings = MagicMock()
            settings.azure_openai.is_configured = True
            settings.azure_openai.endpoint = "https://test.openai.azure.com/"
            settings.azure_openai.api_key = "test-api-key"
            settings.azure_openai.image_deployment = "gpt-image-1"
            settings.azure_openai.image_api_version = "2025-04-01-preview"
            settings.azure_openai.chat_deployment = "gpt-4o"
            settings.azure_openai.chat_api_version = "2024-08-01-preview"
            settings.azure_openai.tts_deployment = "gpt-4o-mini-tts"
            settings.azure_openai.tts_api_version = "2025-03-01-preview"
            settings.request_timeout = 120
            settings.max_retries = 3
            settings.enable_retry = True
            settings.get_voice_settings.return_value = (Voice.ONYX, 1.0)
            mock.return_value = settings
            yield settings

    @pytest.fixture
    def mock_base_client(self, mock_settings):
        """Mock the base client HTTP methods."""
        with patch("faceless.clients.base.httpx.Client") as mock:
            yield mock

    def test_init_success(self, mock_settings, mock_base_client) -> None:
        """Test successful client initialization."""
        from faceless.clients.azure_openai import AzureOpenAIClient

        client = AzureOpenAIClient()
        assert client._settings == mock_settings.azure_openai

    def test_init_not_configured(self, mock_settings, mock_base_client) -> None:
        """Test initialization fails when not configured."""
        from faceless.clients.azure_openai import AzureOpenAIClient

        mock_settings.azure_openai.is_configured = False

        with pytest.raises(AzureOpenAIError) as exc_info:
            AzureOpenAIClient()

        assert "not configured" in str(exc_info.value).lower()

    def test_build_deployment_url(self, mock_settings, mock_base_client) -> None:
        """Test building deployment URL."""
        from faceless.clients.azure_openai import AzureOpenAIClient

        client = AzureOpenAIClient()
        url = client._build_deployment_url(
            deployment="gpt-4o",
            endpoint="chat/completions",
            api_version="2024-08-01-preview",
        )
        assert "openai/deployments/gpt-4o/chat/completions" in url
        assert "api-version=2024-08-01-preview" in url

    def test_handle_error_response_400_content_filter(
        self, mock_settings, mock_base_client
    ) -> None:
        """Test handling 400 with content filter error."""
        from faceless.clients.azure_openai import AzureOpenAIClient

        client = AzureOpenAIClient()

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {
                "code": "content_filter_policy",
                "message": "Content was filtered",
            }
        }

        with pytest.raises(ContentFilterError):
            client._handle_error_response(mock_response, "Image generation")

    def test_handle_error_response_400_generic(
        self, mock_settings, mock_base_client
    ) -> None:
        """Test handling 400 with generic error."""
        from faceless.clients.azure_openai import AzureOpenAIClient

        client = AzureOpenAIClient()

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {
                "code": "invalid_request",
                "message": "Invalid request",
            }
        }

        with pytest.raises(AzureOpenAIError) as exc_info:
            client._handle_error_response(mock_response, "Test")

        assert exc_info.value.details["status_code"] == 400

    def test_handle_error_response_401(self, mock_settings, mock_base_client) -> None:
        """Test handling 401 authentication error."""
        from faceless.clients.azure_openai import AzureOpenAIClient

        client = AzureOpenAIClient()

        mock_response = MagicMock()
        mock_response.status_code = 401

        with pytest.raises(AzureOpenAIError) as exc_info:
            client._handle_error_response(mock_response, "Test")

        assert "authentication" in str(exc_info.value).lower()

    def test_handle_error_response_404(self, mock_settings, mock_base_client) -> None:
        """Test handling 404 not found error."""
        from faceless.clients.azure_openai import AzureOpenAIClient

        client = AzureOpenAIClient()

        mock_response = MagicMock()
        mock_response.status_code = 404

        with pytest.raises(AzureOpenAIError) as exc_info:
            client._handle_error_response(mock_response, "Test")

        assert "not found" in str(exc_info.value).lower()

    def test_handle_error_response_500(self, mock_settings, mock_base_client) -> None:
        """Test handling 500 server error."""
        from faceless.clients.azure_openai import AzureOpenAIClient

        client = AzureOpenAIClient()

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with pytest.raises(AzureOpenAIError) as exc_info:
            client._handle_error_response(mock_response, "Test")

        assert exc_info.value.details["status_code"] == 500

    def test_generate_image_success_with_url(
        self, mock_settings, mock_base_client
    ) -> None:
        """Test successful image generation with URL response."""
        from faceless.clients.azure_openai import AzureOpenAIClient

        client = AzureOpenAIClient()

        # Mock _post to return success response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"url": "https://example.com/image.png"}]
        }

        # Mock the image download
        mock_img_response = MagicMock()
        mock_img_response.content = b"fake_image_data"

        client._post = MagicMock(return_value=mock_response)
        client._client.get = MagicMock(return_value=mock_img_response)

        result = client.generate_image("A cat sitting on a chair")

        assert result == b"fake_image_data"
        client._post.assert_called_once()

    def test_generate_image_success_with_base64(
        self, mock_settings, mock_base_client
    ) -> None:
        """Test successful image generation with base64 response."""
        import base64

        from faceless.clients.azure_openai import AzureOpenAIClient

        client = AzureOpenAIClient()

        encoded_data = base64.b64encode(b"fake_image_data").decode()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"b64_json": encoded_data}]}

        client._post = MagicMock(return_value=mock_response)

        result = client.generate_image("A dog")

        assert result == b"fake_image_data"

    def test_generate_image_no_data(self, mock_settings, mock_base_client) -> None:
        """Test image generation with no data in response."""
        from faceless.clients.azure_openai import AzureOpenAIClient

        client = AzureOpenAIClient()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}

        client._post = MagicMock(return_value=mock_response)

        with pytest.raises(ImageGenerationError):
            client.generate_image("A bird")

    def test_generate_image_unexpected_format(
        self, mock_settings, mock_base_client
    ) -> None:
        """Test image generation with unexpected response format."""
        from faceless.clients.azure_openai import AzureOpenAIClient

        client = AzureOpenAIClient()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"unknown_field": "value"}]}

        client._post = MagicMock(return_value=mock_response)

        with pytest.raises(ImageGenerationError):
            client.generate_image("A fish")

    def test_generate_image_for_platform(self, mock_settings, mock_base_client) -> None:
        """Test image generation for specific platform."""
        from faceless.clients.azure_openai import AzureOpenAIClient

        client = AzureOpenAIClient()
        client.generate_image = MagicMock(return_value=b"image_data")

        client.generate_image_for_platform("A sunset", Platform.YOUTUBE)

        client.generate_image.assert_called_once()
        call_args = client.generate_image.call_args
        assert call_args.kwargs["size"] == Platform.YOUTUBE.image_size

    def test_chat_success(self, mock_settings, mock_base_client) -> None:
        """Test successful chat completion."""
        from faceless.clients.azure_openai import AzureOpenAIClient

        client = AzureOpenAIClient()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello! How can I help?"}}]
        }

        client._post = MagicMock(return_value=mock_response)

        result = client.chat([{"role": "user", "content": "Hi"}])

        assert result == "Hello! How can I help?"

    def test_chat_with_response_format(self, mock_settings, mock_base_client) -> None:
        """Test chat with response format."""
        from faceless.clients.azure_openai import AzureOpenAIClient

        client = AzureOpenAIClient()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"key": "value"}'}}]
        }

        client._post = MagicMock(return_value=mock_response)

        result = client.chat(
            [{"role": "user", "content": "Return JSON"}],
            response_format={"type": "json_object"},
        )

        assert result == '{"key": "value"}'

    def test_chat_json(self, mock_settings, mock_base_client) -> None:
        """Test chat_json method."""
        from faceless.clients.azure_openai import AzureOpenAIClient

        client = AzureOpenAIClient()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"name": "test", "value": 123}'}}]
        }

        client._post = MagicMock(return_value=mock_response)

        result = client.chat_json("You are a helper", "Return JSON")

        assert result == {"name": "test", "value": 123}

    def test_generate_speech_success(self, mock_settings, mock_base_client) -> None:
        """Test successful speech generation."""
        from faceless.clients.azure_openai import AzureOpenAIClient

        client = AzureOpenAIClient()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"audio_data"

        client._post = MagicMock(return_value=mock_response)

        result = client.generate_speech("Hello world", voice=Voice.NOVA, speed=1.2)

        assert result == b"audio_data"
        client._post.assert_called_once()

    def test_generate_speech_error(self, mock_settings, mock_base_client) -> None:
        """Test speech generation error."""
        from faceless.clients.azure_openai import AzureOpenAIClient

        client = AzureOpenAIClient()
        client._post = MagicMock(side_effect=Exception("API Error"))

        with pytest.raises(TTSGenerationError):
            client.generate_speech("Hello")

    def test_generate_speech_for_niche(self, mock_settings, mock_base_client) -> None:
        """Test speech generation for specific niche."""
        from faceless.clients.azure_openai import AzureOpenAIClient

        client = AzureOpenAIClient()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"audio"

        client._post = MagicMock(return_value=mock_response)

        result = client.generate_speech_for_niche("Text", Niche.SCARY_STORIES)

        assert result == b"audio"

    def test_save_image(self, mock_settings, mock_base_client, tmp_path: Path) -> None:
        """Test save_image method."""
        from faceless.clients.azure_openai import AzureOpenAIClient

        client = AzureOpenAIClient()
        client.generate_image_for_platform = MagicMock(return_value=b"image_bytes")

        output_path = tmp_path / "test_image.png"
        result = client.save_image("A sunset", output_path)

        assert result == output_path
        assert output_path.exists()
        assert output_path.read_bytes() == b"image_bytes"

    def test_save_audio_with_niche(
        self, mock_settings, mock_base_client, tmp_path: Path
    ) -> None:
        """Test save_audio with niche."""
        from faceless.clients.azure_openai import AzureOpenAIClient

        client = AzureOpenAIClient()
        client.generate_speech_for_niche = MagicMock(return_value=b"audio_bytes")

        output_path = tmp_path / "test_audio.mp3"
        result = client.save_audio("Hello", output_path, niche=Niche.FINANCE)

        assert result == output_path
        assert output_path.exists()
        assert output_path.read_bytes() == b"audio_bytes"

    def test_save_audio_with_voice(
        self, mock_settings, mock_base_client, tmp_path: Path
    ) -> None:
        """Test save_audio with specific voice."""
        from faceless.clients.azure_openai import AzureOpenAIClient

        client = AzureOpenAIClient()
        client.generate_speech = MagicMock(return_value=b"audio_bytes")

        output_path = tmp_path / "test_audio.mp3"
        result = client.save_audio("Hello", output_path, voice=Voice.ALLOY)

        assert result == output_path
        client.generate_speech.assert_called_with(
            text="Hello", voice=Voice.ALLOY, speed=1.0
        )

    def test_test_connection_success(self, mock_settings, mock_base_client) -> None:
        """Test successful connection test."""
        from faceless.clients.azure_openai import AzureOpenAIClient

        client = AzureOpenAIClient()
        client.chat = MagicMock(return_value="ok")

        result = client.test_connection()

        assert result is True

    def test_test_connection_failure(self, mock_settings, mock_base_client) -> None:
        """Test failed connection test."""
        from faceless.clients.azure_openai import AzureOpenAIClient

        client = AzureOpenAIClient()
        client.chat = MagicMock(side_effect=Exception("Connection failed"))

        result = client.test_connection()

        assert result is False

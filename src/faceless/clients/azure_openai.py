"""
Azure OpenAI API client.

This module provides a client for interacting with Azure OpenAI services:
- Image generation (DALL-E 3, GPT-Image-1)
- Chat completions (GPT-4o)
- Text-to-Speech (gpt-4o-mini-tts)
"""

import base64
from pathlib import Path
from typing import Any

import httpx

from faceless.clients.base import BaseHTTPClient
from faceless.config import get_settings
from faceless.core.enums import Niche, Platform, Voice
from faceless.core.exceptions import (
    AzureOpenAIError,
    ContentFilterError,
    ImageGenerationError,
    TTSGenerationError,
)


class AzureOpenAIClient(BaseHTTPClient):
    """
    Client for Azure OpenAI API.

    Provides methods for:
    - Image generation
    - Chat completions
    - Text-to-speech generation

    Example:
        >>> client = AzureOpenAIClient()
        >>> image_bytes = client.generate_image(
        ...     prompt="A dark forest at night",
        ...     size="1536x1024",
        ... )
    """

    def __init__(self) -> None:
        """Initialize Azure OpenAI client from settings."""
        settings = get_settings()
        azure_settings = settings.azure_openai

        if not azure_settings.is_configured:
            raise AzureOpenAIError(
                "Azure OpenAI is not configured. "
                "Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY environment variables."
            )

        super().__init__(
            base_url=azure_settings.endpoint,
            headers={
                "api-key": azure_settings.api_key,
                "Content-Type": "application/json",
            },
        )
        self._settings = azure_settings

    def _build_deployment_url(
        self,
        deployment: str,
        endpoint: str,
        api_version: str,
    ) -> str:
        """Build URL for a specific deployment endpoint."""
        return f"openai/deployments/{deployment}/{endpoint}?api-version={api_version}"

    def _handle_error_response(
        self,
        response: httpx.Response,
        operation: str,
    ) -> None:
        """Handle error responses from Azure OpenAI API."""
        if response.status_code == 400:
            error_data = response.json().get("error", {})
            error_code = error_data.get("code", "")
            error_message = error_data.get("message", "Unknown error")

            # Check for content filter
            if (
                "content_filter" in error_code.lower()
                or "content" in error_message.lower()
            ):
                raise ContentFilterError(
                    message=f"Content rejected by safety filter: {error_message}",
                    filter_reason=error_code,
                )

            raise AzureOpenAIError(
                message=f"{operation} failed: {error_message}",
                status_code=response.status_code,
                error_code=error_code,
            )

        if response.status_code == 401:
            raise AzureOpenAIError(
                message="Authentication failed. Check your API key.",
                status_code=401,
            )

        if response.status_code == 404:
            raise AzureOpenAIError(
                message="Deployment not found. Check your deployment name.",
                status_code=404,
            )

        if response.status_code >= 400:
            raise AzureOpenAIError(
                message=f"{operation} failed with status {response.status_code}",
                status_code=response.status_code,
                response_body=response.text[:500],
            )

    # =========================================================================
    # Image Generation
    # =========================================================================

    def generate_image(
        self,
        prompt: str,
        size: str = "1536x1024",
        quality: str = "high",
        n: int = 1,
    ) -> bytes:
        """
        Generate an image using Azure OpenAI.

        Args:
            prompt: Image generation prompt
            size: Image size (1024x1024, 1536x1024, 1024x1536, etc.)
            quality: Quality setting (standard, high, hd)
            n: Number of images to generate

        Returns:
            Image bytes (PNG format)

        Raises:
            ImageGenerationError: On generation failure
            ContentFilterError: If prompt is rejected by content filter
        """
        url = self._build_deployment_url(
            deployment=self._settings.image_deployment,
            endpoint="images/generations",
            api_version=self._settings.image_api_version,
        )

        payload = {
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "n": n,
        }

        self.logger.info(
            "Generating image",
            prompt_preview=prompt[:100],
            size=size,
            quality=quality,
        )

        try:
            response = self._post(url, json=payload)

            if response.status_code != 200:
                self._handle_error_response(response, "Image generation")

            result = response.json()

            if "data" not in result or len(result["data"]) == 0:
                raise ImageGenerationError(
                    message="No image data in response",
                    prompt=prompt,
                )

            image_data = result["data"][0]

            # Handle URL or base64 response
            if "url" in image_data:
                # Download from URL
                img_response = self._client.get(image_data["url"])
                img_response.raise_for_status()
                return img_response.content
            elif "b64_json" in image_data:
                # Decode base64
                return base64.b64decode(image_data["b64_json"])
            else:
                raise ImageGenerationError(
                    message="Unexpected response format",
                    prompt=prompt,
                )

        except (ImageGenerationError, ContentFilterError):
            raise
        except Exception as e:
            self.logger.error("Image generation failed", error=str(e))
            raise ImageGenerationError(
                message=f"Image generation failed: {e}",
                prompt=prompt,
                api_error=str(e),
            ) from e

    def generate_image_for_platform(
        self,
        prompt: str,
        platform: Platform,
        quality: str = "high",
    ) -> bytes:
        """
        Generate an image sized for a specific platform.

        Args:
            prompt: Image generation prompt
            platform: Target platform (YouTube or TikTok)
            quality: Quality setting

        Returns:
            Image bytes
        """
        size = platform.image_size
        return self.generate_image(prompt, size=size, quality=quality)

    # =========================================================================
    # Chat Completions
    # =========================================================================

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4000,
        response_format: dict[str, str] | None = None,
    ) -> str:
        """
        Generate a chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            response_format: Optional format specification (e.g., {"type": "json_object"})

        Returns:
            Generated text response

        Raises:
            AzureOpenAIError: On API failure
        """
        url = self._build_deployment_url(
            deployment=self._settings.chat_deployment,
            endpoint="chat/completions",
            api_version=self._settings.chat_api_version,
        )

        payload: dict[str, Any] = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format:
            payload["response_format"] = response_format

        self.logger.info(
            "Generating chat completion",
            message_count=len(messages),
            max_tokens=max_tokens,
        )

        try:
            response = self._post(url, json=payload)

            if response.status_code != 200:
                self._handle_error_response(response, "Chat completion")

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except AzureOpenAIError:
            raise
        except Exception as e:
            self.logger.error("Chat completion failed", error=str(e))
            raise AzureOpenAIError(
                message=f"Chat completion failed: {e}",
            ) from e

    def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> dict[str, Any]:
        """
        Generate a chat completion with JSON response.

        Args:
            system_prompt: System message
            user_prompt: User message
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Returns:
            Parsed JSON response
        """
        import json

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response_text = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )

        return json.loads(response_text)

    # =========================================================================
    # Text-to-Speech
    # =========================================================================

    def generate_speech(
        self,
        text: str,
        voice: Voice = Voice.ONYX,
        speed: float = 1.0,
        response_format: str = "mp3",
    ) -> bytes:
        """
        Generate speech from text using Azure OpenAI TTS.

        Args:
            text: Text to convert to speech
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            speed: Speech speed (0.25 to 4.0)
            response_format: Audio format (mp3, opus, aac, flac)

        Returns:
            Audio bytes

        Raises:
            TTSGenerationError: On generation failure
        """
        url = self._build_deployment_url(
            deployment=self._settings.tts_deployment,
            endpoint="audio/speech",
            api_version=self._settings.tts_api_version,
        )

        payload = {
            "model": self._settings.tts_deployment,
            "input": text,
            "voice": voice.value,
            "speed": speed,
            "response_format": response_format,
        }

        self.logger.info(
            "Generating speech",
            text_preview=text[:50],
            voice=voice.value,
            speed=speed,
        )

        try:
            response = self._post(url, json=payload)

            if response.status_code != 200:
                self._handle_error_response(response, "TTS generation")

            return response.content

        except AzureOpenAIError:
            raise
        except Exception as e:
            self.logger.error("TTS generation failed", error=str(e))
            raise TTSGenerationError(
                message=f"TTS generation failed: {e}",
                text=text,
                voice=voice.value,
                api_error=str(e),
            ) from e

    def generate_speech_for_niche(
        self,
        text: str,
        niche: Niche,
        response_format: str = "mp3",
    ) -> bytes:
        """
        Generate speech using voice settings for a specific niche.

        Args:
            text: Text to convert to speech
            niche: Content niche
            response_format: Audio format

        Returns:
            Audio bytes
        """
        settings = get_settings()
        voice, speed = settings.get_voice_settings(niche)
        return self.generate_speech(
            text=text,
            voice=voice,
            speed=speed,
            response_format=response_format,
        )

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def save_image(
        self,
        prompt: str,
        output_path: Path,
        platform: Platform = Platform.YOUTUBE,
        quality: str = "high",
    ) -> Path:
        """
        Generate and save an image to file.

        Args:
            prompt: Image generation prompt
            output_path: Path to save the image
            platform: Target platform for sizing
            quality: Quality setting

        Returns:
            Path to saved image
        """
        image_bytes = self.generate_image_for_platform(prompt, platform, quality)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(image_bytes)

        self.logger.info("Image saved", path=str(output_path))
        return output_path

    def save_audio(
        self,
        text: str,
        output_path: Path,
        niche: Niche | None = None,
        voice: Voice | None = None,
        speed: float = 1.0,
    ) -> Path:
        """
        Generate and save audio to file.

        Args:
            text: Text to convert to speech
            output_path: Path to save the audio
            niche: Content niche (for default voice settings)
            voice: Specific voice override
            speed: Speech speed override

        Returns:
            Path to saved audio
        """
        if niche and not voice:
            audio_bytes = self.generate_speech_for_niche(text, niche)
        else:
            audio_bytes = self.generate_speech(
                text=text,
                voice=voice or Voice.ONYX,
                speed=speed,
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(audio_bytes)

        self.logger.info("Audio saved", path=str(output_path))
        return output_path

    def test_connection(self) -> bool:
        """
        Test connection to Azure OpenAI.

        Returns:
            True if connection is successful
        """
        try:
            # Make a minimal chat request
            self.chat(
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1,
            )
            return True
        except Exception as e:
            self.logger.error("Connection test failed", error=str(e))
            return False

"""
Application settings using pydantic-settings.

This module provides a Settings class that loads configuration from
environment variables and .env files, with validation and type safety.
"""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from faceless.core.enums import Niche, Voice

# =============================================================================
# Output Settings (Video Platform Configuration)
# =============================================================================


@dataclass(frozen=True)
class OutputConfig:
    """Video output configuration for a platform."""

    resolution: str
    fps: int
    format: str
    codec: str


# Platform-specific output settings
OUTPUT_SETTINGS: dict[str, OutputConfig] = {
    "youtube": OutputConfig(
        resolution="1920x1080",
        fps=30,
        format="mp4",
        codec="libx264",
    ),
    "tiktok": OutputConfig(
        resolution="1080x1920",
        fps=30,
        format="mp4",
        codec="libx264",
    ),
}

# =============================================================================
# Settings Classes
# =============================================================================


class AzureOpenAISettings(BaseSettings):
    """Azure OpenAI API configuration."""

    model_config = SettingsConfigDict(
        env_prefix="AZURE_OPENAI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    endpoint: str = Field(
        default="",
        description="Azure OpenAI endpoint URL",
    )
    api_key: str = Field(
        default="",
        alias="AZURE_OPENAI_API_KEY",
        description="Azure OpenAI API key",
    )

    # Image generation
    image_deployment: str = Field(
        default="gpt-image-1",
        description="Image generation model deployment name",
    )
    image_api_version: str = Field(
        default="2025-04-01-preview",
        description="Image API version",
    )

    # Chat/completion
    chat_deployment: str = Field(
        default="gpt-4o",
        description="Chat model deployment name",
    )
    chat_api_version: str = Field(
        default="2024-08-01-preview",
        description="Chat API version",
    )

    # TTS
    tts_deployment: str = Field(
        default="gpt-4o-mini-tts",
        description="TTS model deployment name",
    )
    tts_api_version: str = Field(
        default="2025-03-01-preview",
        description="TTS API version",
    )

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, v: str) -> str:
        """Ensure endpoint ends with /."""
        if v and not v.endswith("/"):
            return v + "/"
        return v

    @property
    def is_configured(self) -> bool:
        """Check if Azure OpenAI is properly configured."""
        return bool(self.endpoint and self.api_key)


class ElevenLabsSettings(BaseSettings):
    """ElevenLabs API configuration."""

    model_config = SettingsConfigDict(
        env_prefix="ELEVENLABS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: str = Field(default="", description="ElevenLabs API key")
    voice_id_scary: str = Field(default="", description="Voice ID for scary stories")
    voice_id_finance: str = Field(default="", description="Voice ID for finance")
    voice_id_luxury: str = Field(default="", description="Voice ID for luxury")

    def get_voice_id(self, niche: Niche) -> str:
        """Get voice ID for a specific niche."""
        voice_map = {
            Niche.SCARY_STORIES: self.voice_id_scary,
            Niche.FINANCE: self.voice_id_finance,
            Niche.LUXURY: self.voice_id_luxury,
        }
        return voice_map.get(niche, "")

    @property
    def is_configured(self) -> bool:
        """Check if ElevenLabs is properly configured."""
        return bool(self.api_key)


class RedditSettings(BaseSettings):
    """Reddit API configuration for authenticated scraping."""

    model_config = SettingsConfigDict(
        env_prefix="REDDIT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    client_id: str = Field(default="", description="Reddit client ID")
    client_secret: str = Field(default="", description="Reddit client secret")
    user_agent: str = Field(
        default="FacelessContent/1.0",
        description="User agent for Reddit API",
    )

    @property
    def is_configured(self) -> bool:
        """Check if Reddit API is properly configured."""
        return bool(self.client_id and self.client_secret)


class VoiceConfig(BaseSettings):
    """Voice configuration for a specific niche."""

    voice: Voice = Field(default=Voice.ONYX, description="Azure OpenAI TTS voice")
    speed: float = Field(default=1.0, ge=0.25, le=4.0, description="Speech speed")


class Settings(BaseSettings):
    """
    Main application settings.

    Loads configuration from environment variables and .env files.
    All settings can be overridden via environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
    )

    # Sub-settings (will be populated from nested env vars)
    azure_openai: AzureOpenAISettings = Field(default_factory=AzureOpenAISettings)
    elevenlabs: ElevenLabsSettings = Field(default_factory=ElevenLabsSettings)
    reddit: RedditSettings = Field(default_factory=RedditSettings)

    # TTS provider selection
    use_elevenlabs: bool = Field(
        default=False,
        description="Use ElevenLabs instead of Azure TTS",
    )

    # Application settings
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    log_json_format: bool = Field(
        default=False,
        description="Use JSON structured logging",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )

    # Paths
    output_base_dir: Path = Field(
        default=Path("output"),
        description="Base directory for output files",
    )
    shared_dir: Path = Field(
        default=Path("shared"),
        description="Directory for shared resources",
    )

    # FFmpeg paths (empty string means use system PATH)
    ffmpeg_path: str = Field(
        default="ffmpeg",
        description="Path to FFmpeg binary",
    )
    ffprobe_path: str = Field(
        default="ffprobe",
        description="Path to FFprobe binary",
    )

    @field_validator("ffmpeg_path", "ffprobe_path", mode="before")
    @classmethod
    def empty_to_default(cls, v: str, info) -> str:
        """Convert empty string to default command name."""
        if v == "" or v is None:
            # Return default based on field name
            return "ffmpeg" if info.field_name == "ffmpeg_path" else "ffprobe"
        return v

    # Processing settings
    max_concurrent_requests: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum concurrent API requests (general)",
    )
    max_concurrent_images: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum concurrent image generation requests",
    )
    max_concurrent_tts: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum concurrent TTS (text-to-speech) requests",
    )
    request_timeout: int = Field(
        default=120,
        ge=10,
        le=600,
        description="Request timeout in seconds",
    )
    enable_retry: bool = Field(
        default=True,
        description="Enable automatic retry on failure",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts",
    )

    # Feature flags
    enable_checkpointing: bool = Field(
        default=True,
        description="Enable checkpointing for resumable jobs",
    )
    enable_thumbnails: bool = Field(
        default=True,
        description="Enable thumbnail generation",
    )
    enable_subtitles: bool = Field(
        default=True,
        description="Enable subtitle generation",
    )

    # Voice settings per niche
    voice_scary_stories: Voice = Field(default=Voice.ONYX)
    voice_speed_scary_stories: float = Field(default=0.9)
    voice_finance: Voice = Field(default=Voice.ONYX)
    voice_speed_finance: float = Field(default=1.0)
    voice_luxury: Voice = Field(default=Voice.NOVA)
    voice_speed_luxury: float = Field(default=0.95)

    def get_voice_settings(self, niche: Niche) -> tuple[Voice, float]:
        """Get voice and speed settings for a niche."""
        settings_map = {
            Niche.SCARY_STORIES: (
                self.voice_scary_stories,
                self.voice_speed_scary_stories,
            ),
            Niche.FINANCE: (self.voice_finance, self.voice_speed_finance),
            Niche.LUXURY: (self.voice_luxury, self.voice_speed_luxury),
        }
        return settings_map.get(niche, (Voice.ONYX, 1.0))

    def get_output_dir(self, niche: Niche) -> Path:
        """Get output directory for a niche."""
        return self.output_base_dir / niche.value

    def get_scripts_dir(self, niche: Niche) -> Path:
        """Get scripts directory for a niche."""
        return self.get_output_dir(niche) / "scripts"

    def get_images_dir(self, niche: Niche) -> Path:
        """Get images directory for a niche."""
        return self.get_output_dir(niche) / "images"

    def get_audio_dir(self, niche: Niche) -> Path:
        """Get audio directory for a niche."""
        return self.get_output_dir(niche) / "audio"

    def get_videos_dir(self, niche: Niche) -> Path:
        """Get videos directory for a niche."""
        return self.get_output_dir(niche) / "videos"

    def get_final_output_dir(self, niche: Niche) -> Path:
        """Get final output directory for a niche."""
        return self.get_output_dir(niche) / "final"

    def get_checkpoints_dir(self, niche: Niche) -> Path:
        """Get checkpoints directory for a niche."""
        return self.get_output_dir(niche) / ".checkpoints"

    def get_music_dir(self) -> Path:
        """Get shared music directory."""
        return self.shared_dir / "music"

    def get_prompts_dir(self) -> Path:
        """Get shared prompts directory."""
        return self.shared_dir / "prompts"

    def get_templates_dir(self) -> Path:
        """Get shared templates directory."""
        return self.shared_dir / "templates"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.debug and self.log_json_format

    def ensure_directories(self, niche: Niche | None = None) -> None:
        """Create all required directories."""
        niches = [niche] if niche else list(Niche)
        for n in niches:
            self.get_scripts_dir(n).mkdir(parents=True, exist_ok=True)
            self.get_images_dir(n).mkdir(parents=True, exist_ok=True)
            self.get_audio_dir(n).mkdir(parents=True, exist_ok=True)
            self.get_videos_dir(n).mkdir(parents=True, exist_ok=True)
            self.get_final_output_dir(n).mkdir(parents=True, exist_ok=True)
            if self.enable_checkpointing:
                self.get_checkpoints_dir(n).mkdir(parents=True, exist_ok=True)

        # Shared directories
        self.get_music_dir().mkdir(parents=True, exist_ok=True)
        self.get_prompts_dir().mkdir(parents=True, exist_ok=True)
        self.get_templates_dir().mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.

    Settings are loaded once and cached for the lifetime of the application.
    To reload settings, call get_settings.cache_clear() first.

    Returns:
        Settings instance with all configuration values.
    """
    return Settings()


def reload_settings() -> Settings:
    """
    Force reload of settings.

    Clears the cache and returns a fresh Settings instance.
    Useful for testing or dynamic configuration changes.
    """
    get_settings.cache_clear()
    return get_settings()


def get_output_settings_dict(platform: str) -> dict[str, str | int]:
    """
    Get output settings for a platform as a dictionary.

    This provides backward compatibility with legacy code expecting
    a dict with resolution, fps, format, codec keys.

    Args:
        platform: One of "youtube" or "tiktok"

    Returns:
        Dictionary with output settings
    """
    config = OUTPUT_SETTINGS.get(platform)
    if not config:
        raise ValueError(f"Unknown platform: {platform}")
    return {
        "resolution": config.resolution,
        "fps": config.fps,
        "format": config.format,
        "codec": config.codec,
    }


def get_legacy_paths(settings: Settings | None = None) -> dict[str, dict[str, str]]:
    """
    Generate a PATHS dictionary compatible with legacy pipeline code.

    This creates the same structure as the old config.py PATHS dict,
    but using paths derived from the settings.

    Args:
        settings: Settings instance (defaults to cached settings)

    Returns:
        Dictionary with paths for each niche and shared resources
    """
    if settings is None:
        settings = get_settings()

    paths: dict[str, dict[str, str]] = {}

    # Add paths for each niche
    for niche in Niche:
        niche_key = niche.value  # e.g., "scary-stories"
        paths[niche_key] = {
            "scripts": str(settings.get_scripts_dir(niche)),
            "images": str(settings.get_images_dir(niche)),
            "audio": str(settings.get_audio_dir(niche)),
            "videos": str(settings.get_videos_dir(niche)),
            "output": str(settings.get_final_output_dir(niche)),
        }

    # Add shared paths
    paths["shared"] = {
        "templates": str(settings.get_templates_dir()),
        "prompts": str(settings.get_prompts_dir()),
        "music": str(settings.get_music_dir()),
    }

    return paths


def get_legacy_voice_settings(
    settings: Settings | None = None,
) -> dict[str, dict[str, str | float]]:
    """
    Generate a VOICE_SETTINGS dictionary compatible with legacy pipeline code.

    Args:
        settings: Settings instance (defaults to cached settings)

    Returns:
        Dictionary with voice settings for each niche
    """
    if settings is None:
        settings = get_settings()

    voice_settings: dict[str, dict[str, str | float]] = {}

    for niche in Niche:
        voice, speed = settings.get_voice_settings(niche)
        niche_key = niche.value
        elevenlabs_voice_id = settings.elevenlabs.get_voice_id(niche)

        voice_settings[niche_key] = {
            "openai_voice": voice.value,
            "openai_speed": speed,
            "elevenlabs_voice_id": elevenlabs_voice_id,
        }

    return voice_settings

"""
Application settings using pydantic-settings.

This module provides a Settings class that loads configuration from
environment variables and .env files, with validation and type safety.
"""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationInfo, field_validator
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
    # Original niches
    voice_id_scary: str = Field(default="", description="Voice ID for scary stories")
    voice_id_finance: str = Field(default="", description="Voice ID for finance")
    voice_id_luxury: str = Field(default="", description="Voice ID for luxury")
    # New niches
    voice_id_true_crime: str = Field(default="", description="Voice ID for true crime")
    voice_id_psychology: str = Field(
        default="", description="Voice ID for psychology facts"
    )
    voice_id_history: str = Field(default="", description="Voice ID for history")
    voice_id_motivation: str = Field(default="", description="Voice ID for motivation")
    voice_id_space: str = Field(
        default="", description="Voice ID for space & astronomy"
    )
    voice_id_conspiracy: str = Field(
        default="", description="Voice ID for conspiracy & mysteries"
    )
    voice_id_animals: str = Field(default="", description="Voice ID for animal facts")
    voice_id_health: str = Field(
        default="", description="Voice ID for health & wellness"
    )
    voice_id_relationships: str = Field(
        default="", description="Voice ID for relationship advice"
    )
    voice_id_tech: str = Field(default="", description="Voice ID for tech & gadgets")
    voice_id_lifehacks: str = Field(default="", description="Voice ID for life hacks")
    voice_id_mythology: str = Field(
        default="", description="Voice ID for mythology & folklore"
    )
    voice_id_unsolved: str = Field(
        default="", description="Voice ID for unsolved mysteries"
    )
    voice_id_geography: str = Field(
        default="", description="Voice ID for geography facts"
    )
    voice_id_ai_future: str = Field(
        default="", description="Voice ID for AI & future tech"
    )
    voice_id_philosophy: str = Field(default="", description="Voice ID for philosophy")
    voice_id_books: str = Field(default="", description="Voice ID for book summaries")
    voice_id_celebrity: str = Field(
        default="", description="Voice ID for celebrity net worth"
    )
    voice_id_survival: str = Field(default="", description="Voice ID for survival tips")
    voice_id_sleep: str = Field(
        default="", description="Voice ID for sleep & relaxation"
    )
    voice_id_netflix: str = Field(
        default="", description="Voice ID for Netflix recommendations"
    )
    voice_id_mockumentary: str = Field(
        default="", description="Voice ID for mockumentary How It's Made"
    )

    def get_voice_id(self, niche: Niche) -> str:
        """Get voice ID for a specific niche."""
        voice_map = {
            Niche.SCARY_STORIES: self.voice_id_scary,
            Niche.FINANCE: self.voice_id_finance,
            Niche.LUXURY: self.voice_id_luxury,
            Niche.TRUE_CRIME: self.voice_id_true_crime,
            Niche.PSYCHOLOGY_FACTS: self.voice_id_psychology,
            Niche.HISTORY: self.voice_id_history,
            Niche.MOTIVATION: self.voice_id_motivation,
            Niche.SPACE_ASTRONOMY: self.voice_id_space,
            Niche.CONSPIRACY_MYSTERIES: self.voice_id_conspiracy,
            Niche.ANIMAL_FACTS: self.voice_id_animals,
            Niche.HEALTH_WELLNESS: self.voice_id_health,
            Niche.RELATIONSHIP_ADVICE: self.voice_id_relationships,
            Niche.TECH_GADGETS: self.voice_id_tech,
            Niche.LIFE_HACKS: self.voice_id_lifehacks,
            Niche.MYTHOLOGY_FOLKLORE: self.voice_id_mythology,
            Niche.UNSOLVED_MYSTERIES: self.voice_id_unsolved,
            Niche.GEOGRAPHY_FACTS: self.voice_id_geography,
            Niche.AI_FUTURE_TECH: self.voice_id_ai_future,
            Niche.PHILOSOPHY: self.voice_id_philosophy,
            Niche.BOOK_SUMMARIES: self.voice_id_books,
            Niche.CELEBRITY_NET_WORTH: self.voice_id_celebrity,
            Niche.SURVIVAL_TIPS: self.voice_id_survival,
            Niche.SLEEP_RELAXATION: self.voice_id_sleep,
            Niche.NETFLIX_RECOMMENDATIONS: self.voice_id_netflix,
            Niche.MOCKUMENTARY_HOWMADE: self.voice_id_mockumentary,
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


class ContentSourceSettings(BaseSettings):
    """Configuration for content sources."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Optional API keys for extended sources
    youtube_api_key: str = Field(
        default="",
        alias="YOUTUBE_API_KEY",
        description="YouTube Data API v3 key (optional)",
    )
    newsapi_key: str = Field(
        default="",
        alias="NEWSAPI_KEY",
        description="NewsAPI.org API key (optional)",
    )

    # Rate limiting settings
    reddit_rate_limit: int = Field(
        default=60,
        ge=1,
        le=120,
        description="Reddit requests per minute",
    )
    wikipedia_rate_limit: int = Field(
        default=200,
        ge=1,
        le=500,
        description="Wikipedia requests per minute",
    )
    hackernews_rate_limit: int = Field(
        default=60,
        ge=1,
        le=120,
        description="Hacker News requests per minute",
    )

    # Caching settings
    cache_enabled: bool = Field(
        default=True,
        description="Enable content caching",
    )
    cache_ttl_seconds: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Cache time-to-live in seconds (1 hour default)",
    )

    # Content filtering
    min_content_words: int = Field(
        default=100,
        ge=50,
        le=500,
        description="Minimum word count for content to be included",
    )
    min_score: int = Field(
        default=50,
        ge=0,
        le=1000,
        description="Minimum engagement score (Reddit upvotes, etc.)",
    )

    @property
    def youtube_configured(self) -> bool:
        """Check if YouTube API is configured."""
        return bool(self.youtube_api_key)

    @property
    def newsapi_configured(self) -> bool:
        """Check if NewsAPI is configured."""
        return bool(self.newsapi_key)


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
    content_sources: ContentSourceSettings = Field(
        default_factory=ContentSourceSettings
    )

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
    def empty_to_default(cls, v: str, info: ValidationInfo) -> str:
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
    max_concurrent_videos: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Maximum concurrent video scene rendering (FFmpeg processes)",
    )
    request_timeout: int = Field(
        default=120,
        ge=10,
        le=600,
        description="Request timeout in seconds",
    )
    image_generation_timeout: int = Field(
        default=120,
        ge=10,
        le=600,
        description="Timeout for image generation requests (seconds)",
    )
    tts_generation_timeout: int = Field(
        default=180,
        ge=10,
        le=600,
        description="Timeout for TTS generation requests (seconds)",
    )
    scraper_timeout: int = Field(
        default=30,
        ge=5,
        le=120,
        description="Timeout for web scraping requests (seconds)",
    )

    # Content generation settings
    words_per_scene: int = Field(
        default=150,
        ge=50,
        le=500,
        description="Target words per scene when splitting content",
    )

    # Video effect settings
    ken_burns_scale_factor: float = Field(
        default=1.15,
        ge=1.0,
        le=2.0,
        description="Scale factor for Ken Burns effect (zoom/pan)",
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

    # Voice settings per niche - Original
    voice_scary_stories: Voice = Field(default=Voice.ONYX)
    voice_speed_scary_stories: float = Field(default=0.9)
    voice_finance: Voice = Field(default=Voice.ONYX)
    voice_speed_finance: float = Field(default=1.0)
    voice_luxury: Voice = Field(default=Voice.NOVA)
    voice_speed_luxury: float = Field(default=0.95)

    # Voice settings per niche - New niches
    voice_true_crime: Voice = Field(default=Voice.ONYX)
    voice_speed_true_crime: float = Field(default=0.9)
    voice_psychology_facts: Voice = Field(default=Voice.NOVA)
    voice_speed_psychology_facts: float = Field(default=1.0)
    voice_history: Voice = Field(default=Voice.ONYX)
    voice_speed_history: float = Field(default=0.95)
    voice_motivation: Voice = Field(default=Voice.ECHO)
    voice_speed_motivation: float = Field(default=1.0)
    voice_space_astronomy: Voice = Field(default=Voice.ONYX)
    voice_speed_space_astronomy: float = Field(default=0.95)
    voice_conspiracy_mysteries: Voice = Field(default=Voice.ONYX)
    voice_speed_conspiracy_mysteries: float = Field(default=0.9)
    voice_animal_facts: Voice = Field(default=Voice.NOVA)
    voice_speed_animal_facts: float = Field(default=1.0)
    voice_health_wellness: Voice = Field(default=Voice.NOVA)
    voice_speed_health_wellness: float = Field(default=1.0)
    voice_relationship_advice: Voice = Field(default=Voice.NOVA)
    voice_speed_relationship_advice: float = Field(default=0.95)
    voice_tech_gadgets: Voice = Field(default=Voice.ALLOY)
    voice_speed_tech_gadgets: float = Field(default=1.0)
    voice_life_hacks: Voice = Field(default=Voice.ECHO)
    voice_speed_life_hacks: float = Field(default=1.05)
    voice_mythology_folklore: Voice = Field(default=Voice.FABLE)
    voice_speed_mythology_folklore: float = Field(default=0.9)
    voice_unsolved_mysteries: Voice = Field(default=Voice.ONYX)
    voice_speed_unsolved_mysteries: float = Field(default=0.9)
    voice_geography_facts: Voice = Field(default=Voice.NOVA)
    voice_speed_geography_facts: float = Field(default=1.0)
    voice_ai_future_tech: Voice = Field(default=Voice.ALLOY)
    voice_speed_ai_future_tech: float = Field(default=1.0)
    voice_philosophy: Voice = Field(default=Voice.ONYX)
    voice_speed_philosophy: float = Field(default=0.9)
    voice_book_summaries: Voice = Field(default=Voice.NOVA)
    voice_speed_book_summaries: float = Field(default=1.0)
    voice_celebrity_net_worth: Voice = Field(default=Voice.ECHO)
    voice_speed_celebrity_net_worth: float = Field(default=1.0)
    voice_survival_tips: Voice = Field(default=Voice.ONYX)
    voice_speed_survival_tips: float = Field(default=0.95)
    voice_sleep_relaxation: Voice = Field(default=Voice.SHIMMER)
    voice_speed_sleep_relaxation: float = Field(default=0.8)
    voice_netflix_recommendations: Voice = Field(default=Voice.ECHO)
    voice_speed_netflix_recommendations: float = Field(default=1.0)
    voice_mockumentary_howmade: Voice = Field(default=Voice.FABLE)
    voice_speed_mockumentary_howmade: float = Field(default=0.95)

    def get_voice_settings(self, niche: Niche) -> tuple[Voice, float]:
        """Get voice and speed settings for a niche."""
        settings_map = {
            Niche.SCARY_STORIES: (
                self.voice_scary_stories,
                self.voice_speed_scary_stories,
            ),
            Niche.FINANCE: (self.voice_finance, self.voice_speed_finance),
            Niche.LUXURY: (self.voice_luxury, self.voice_speed_luxury),
            Niche.TRUE_CRIME: (self.voice_true_crime, self.voice_speed_true_crime),
            Niche.PSYCHOLOGY_FACTS: (
                self.voice_psychology_facts,
                self.voice_speed_psychology_facts,
            ),
            Niche.HISTORY: (self.voice_history, self.voice_speed_history),
            Niche.MOTIVATION: (self.voice_motivation, self.voice_speed_motivation),
            Niche.SPACE_ASTRONOMY: (
                self.voice_space_astronomy,
                self.voice_speed_space_astronomy,
            ),
            Niche.CONSPIRACY_MYSTERIES: (
                self.voice_conspiracy_mysteries,
                self.voice_speed_conspiracy_mysteries,
            ),
            Niche.ANIMAL_FACTS: (
                self.voice_animal_facts,
                self.voice_speed_animal_facts,
            ),
            Niche.HEALTH_WELLNESS: (
                self.voice_health_wellness,
                self.voice_speed_health_wellness,
            ),
            Niche.RELATIONSHIP_ADVICE: (
                self.voice_relationship_advice,
                self.voice_speed_relationship_advice,
            ),
            Niche.TECH_GADGETS: (
                self.voice_tech_gadgets,
                self.voice_speed_tech_gadgets,
            ),
            Niche.LIFE_HACKS: (self.voice_life_hacks, self.voice_speed_life_hacks),
            Niche.MYTHOLOGY_FOLKLORE: (
                self.voice_mythology_folklore,
                self.voice_speed_mythology_folklore,
            ),
            Niche.UNSOLVED_MYSTERIES: (
                self.voice_unsolved_mysteries,
                self.voice_speed_unsolved_mysteries,
            ),
            Niche.GEOGRAPHY_FACTS: (
                self.voice_geography_facts,
                self.voice_speed_geography_facts,
            ),
            Niche.AI_FUTURE_TECH: (
                self.voice_ai_future_tech,
                self.voice_speed_ai_future_tech,
            ),
            Niche.PHILOSOPHY: (self.voice_philosophy, self.voice_speed_philosophy),
            Niche.BOOK_SUMMARIES: (
                self.voice_book_summaries,
                self.voice_speed_book_summaries,
            ),
            Niche.CELEBRITY_NET_WORTH: (
                self.voice_celebrity_net_worth,
                self.voice_speed_celebrity_net_worth,
            ),
            Niche.SURVIVAL_TIPS: (
                self.voice_survival_tips,
                self.voice_speed_survival_tips,
            ),
            Niche.SLEEP_RELAXATION: (
                self.voice_sleep_relaxation,
                self.voice_speed_sleep_relaxation,
            ),
            Niche.NETFLIX_RECOMMENDATIONS: (
                self.voice_netflix_recommendations,
                self.voice_speed_netflix_recommendations,
            ),
            Niche.MOCKUMENTARY_HOWMADE: (
                self.voice_mockumentary_howmade,
                self.voice_speed_mockumentary_howmade,
            ),
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

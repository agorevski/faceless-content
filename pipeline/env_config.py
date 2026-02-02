"""
Environment-based Configuration for Pipeline.

This module provides backward compatibility with the legacy config.py by
exporting the same variable names, but loading values from .env via
the pydantic settings system.

Usage:
    Replace `from config import X` with `from env_config import X`
"""

import sys
from pathlib import Path

# Add the src directory to Python path so we can import faceless modules
_src_path = Path(__file__).parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

from faceless.utils.logging import get_logger

logger = get_logger(__name__)

# Add shared directory to path for prompt imports
_shared_path = Path(__file__).parent.parent / "shared"
if str(_shared_path) not in sys.path:
    sys.path.insert(0, str(_shared_path))

# Now import from the faceless package
from faceless.config.settings import (
    OUTPUT_SETTINGS as _OUTPUT_SETTINGS,
    get_legacy_paths,
    get_legacy_voice_settings,
    get_output_settings_dict,
    get_settings,
)

# Import image settings from shared prompts
from prompts.image_prompts import (
    AI_FUTURE_TECH_IMAGE_SETTINGS,
    ANIMAL_FACTS_IMAGE_SETTINGS,
    BOOK_SUMMARIES_IMAGE_SETTINGS,
    CELEBRITY_NET_WORTH_IMAGE_SETTINGS,
    CONSPIRACY_MYSTERIES_IMAGE_SETTINGS,
    FINANCE_IMAGE_SETTINGS,
    GEOGRAPHY_FACTS_IMAGE_SETTINGS,
    HEALTH_WELLNESS_IMAGE_SETTINGS,
    HISTORY_IMAGE_SETTINGS,
    LIFE_HACKS_IMAGE_SETTINGS,
    LUXURY_IMAGE_SETTINGS,
    MOCKUMENTARY_HOWMADE_IMAGE_SETTINGS,
    MOTIVATION_IMAGE_SETTINGS,
    MYTHOLOGY_FOLKLORE_IMAGE_SETTINGS,
    NETFLIX_RECOMMENDATIONS_IMAGE_SETTINGS,
    PHILOSOPHY_IMAGE_SETTINGS,
    PSYCHOLOGY_FACTS_IMAGE_SETTINGS,
    RELATIONSHIP_ADVICE_IMAGE_SETTINGS,
    SCARY_STORIES_IMAGE_SETTINGS,
    SLEEP_RELAXATION_IMAGE_SETTINGS,
    SPACE_ASTRONOMY_IMAGE_SETTINGS,
    SURVIVAL_TIPS_IMAGE_SETTINGS,
    TECH_GADGETS_IMAGE_SETTINGS,
    TRUE_CRIME_IMAGE_SETTINGS,
    UNSOLVED_MYSTERIES_IMAGE_SETTINGS,
    build_enhanced_prompt,
    get_image_settings,
)

# =============================================================================
# Load settings from .env
# =============================================================================

_settings = get_settings()

# =============================================================================
# AZURE OPENAI CONFIGURATION
# =============================================================================

AZURE_OPENAI_ENDPOINT = _settings.azure_openai.endpoint
AZURE_OPENAI_KEY = _settings.azure_openai.api_key

# Image Generation (GPT-Image-1)
AZURE_OPENAI_IMAGE_DEPLOYMENT = _settings.azure_openai.image_deployment
AZURE_OPENAI_IMAGE_API_VERSION = _settings.azure_openai.image_api_version

# Chat/Completion Model for Script Enhancement
AZURE_OPENAI_CHAT_DEPLOYMENT = _settings.azure_openai.chat_deployment
AZURE_OPENAI_CHAT_API_VERSION = _settings.azure_openai.chat_api_version

# Text-to-Speech (Azure OpenAI TTS)
AZURE_OPENAI_TTS_DEPLOYMENT = _settings.azure_openai.tts_deployment
AZURE_OPENAI_TTS_API_VERSION = _settings.azure_openai.tts_api_version

# Legacy Azure Speech TTS (not used - keeping for compatibility)
AZURE_TTS_ENDPOINT = ""
AZURE_TTS_KEY = ""
AZURE_TTS_REGION = ""

# =============================================================================
# ELEVENLABS CONFIGURATION
# =============================================================================

ELEVENLABS_API_KEY = _settings.elevenlabs.api_key
ELEVENLABS_VOICE_ID = ""  # Generic voice ID (use VOICE_SETTINGS for per-niche)

# =============================================================================
# USE ELEVENLABS INSTEAD OF AZURE?
# =============================================================================

USE_ELEVENLABS = _settings.use_elevenlabs

# =============================================================================
# VOICE SETTINGS PER NICHE
# =============================================================================

# Generate from settings (these match the old config.py structure)
VOICE_SETTINGS = get_legacy_voice_settings(_settings)

# =============================================================================
# IMAGE GENERATION SETTINGS PER NICHE
# =============================================================================

# Combine all image settings into one dict matching old config.py structure
IMAGE_SETTINGS = {
    # Original niches
    "scary-stories": SCARY_STORIES_IMAGE_SETTINGS,
    "finance": FINANCE_IMAGE_SETTINGS,
    "luxury": LUXURY_IMAGE_SETTINGS,
    # New niches
    "true-crime": TRUE_CRIME_IMAGE_SETTINGS,
    "psychology-facts": PSYCHOLOGY_FACTS_IMAGE_SETTINGS,
    "history": HISTORY_IMAGE_SETTINGS,
    "motivation": MOTIVATION_IMAGE_SETTINGS,
    "space-astronomy": SPACE_ASTRONOMY_IMAGE_SETTINGS,
    "conspiracy-mysteries": CONSPIRACY_MYSTERIES_IMAGE_SETTINGS,
    "animal-facts": ANIMAL_FACTS_IMAGE_SETTINGS,
    "health-wellness": HEALTH_WELLNESS_IMAGE_SETTINGS,
    "relationship-advice": RELATIONSHIP_ADVICE_IMAGE_SETTINGS,
    "tech-gadgets": TECH_GADGETS_IMAGE_SETTINGS,
    "life-hacks": LIFE_HACKS_IMAGE_SETTINGS,
    "mythology-folklore": MYTHOLOGY_FOLKLORE_IMAGE_SETTINGS,
    "unsolved-mysteries": UNSOLVED_MYSTERIES_IMAGE_SETTINGS,
    "geography-facts": GEOGRAPHY_FACTS_IMAGE_SETTINGS,
    "ai-future-tech": AI_FUTURE_TECH_IMAGE_SETTINGS,
    "philosophy": PHILOSOPHY_IMAGE_SETTINGS,
    "book-summaries": BOOK_SUMMARIES_IMAGE_SETTINGS,
    "celebrity-net-worth": CELEBRITY_NET_WORTH_IMAGE_SETTINGS,
    "survival-tips": SURVIVAL_TIPS_IMAGE_SETTINGS,
    "sleep-relaxation": SLEEP_RELAXATION_IMAGE_SETTINGS,
    "netflix-recommendations": NETFLIX_RECOMMENDATIONS_IMAGE_SETTINGS,
    "mockumentary-howmade": MOCKUMENTARY_HOWMADE_IMAGE_SETTINGS,
}

# =============================================================================
# OUTPUT SETTINGS
# =============================================================================

# Convert OUTPUT_SETTINGS to dict format matching old config.py
OUTPUT_SETTINGS = {
    platform: {
        "resolution": config.resolution,
        "fps": config.fps,
        "format": config.format,
        "codec": config.codec,
    }
    for platform, config in _OUTPUT_SETTINGS.items()
}

# =============================================================================
# PATHS
# =============================================================================

# Generate paths from settings (using OUTPUT_BASE_DIR from .env)
PATHS = get_legacy_paths(_settings)

# =============================================================================
# PROCESSING SETTINGS (from .env)
# =============================================================================

MAX_CONCURRENT_REQUESTS = _settings.max_concurrent_requests
REQUEST_TIMEOUT = _settings.request_timeout
ENABLE_RETRY = _settings.enable_retry
MAX_RETRIES = _settings.max_retries

# =============================================================================
# FEATURE FLAGS (from .env)
# =============================================================================

ENABLE_CHECKPOINTING = _settings.enable_checkpointing
ENABLE_THUMBNAILS = _settings.enable_thumbnails
ENABLE_SUBTITLES = _settings.enable_subtitles

# =============================================================================
# FFmpeg PATHS (from .env)
# =============================================================================

FFMPEG_PATH = _settings.ffmpeg_path
FFPROBE_PATH = _settings.ffprobe_path

# =============================================================================
# DEBUG MODE
# =============================================================================

DEBUG = _settings.debug

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def validate_config() -> bool:
    """
    Validate that the configuration is properly set.

    Returns:
        True if configuration is valid, False otherwise
    """
    errors = []

    if not _settings.azure_openai.is_configured:
        errors.append(
            "Azure OpenAI not configured (check AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY)"
        )

    if USE_ELEVENLABS and not _settings.elevenlabs.is_configured:
        errors.append(
            "ElevenLabs enabled but not configured (check ELEVENLABS_API_KEY)"
        )

    if errors:
        for error in errors:
            logger.error("Configuration error", error=error)
        return False

    logger.info("Configuration validated successfully")
    return True


def print_config_summary() -> None:
    """Print a summary of the current configuration."""
    logger.info("Configuration summary loaded from .env")

    logger.info(
        "Azure OpenAI configuration",
        endpoint=f"{AZURE_OPENAI_ENDPOINT[:50]}..." if AZURE_OPENAI_ENDPOINT else "Not set",
        api_key_set=bool(AZURE_OPENAI_KEY),
        image_deployment=AZURE_OPENAI_IMAGE_DEPLOYMENT,
        chat_deployment=AZURE_OPENAI_CHAT_DEPLOYMENT,
        tts_deployment=AZURE_OPENAI_TTS_DEPLOYMENT,
    )

    logger.info(
        "ElevenLabs configuration",
        enabled=USE_ELEVENLABS,
        api_key_set=bool(ELEVENLABS_API_KEY) if USE_ELEVENLABS else None,
    )

    logger.info(
        "Output settings",
        base_dir=str(_settings.output_base_dir),
        youtube_resolution=OUTPUT_SETTINGS["youtube"]["resolution"],
        tiktok_resolution=OUTPUT_SETTINGS["tiktok"]["resolution"],
    )

    logger.info(
        "Processing settings",
        max_concurrent_requests=MAX_CONCURRENT_REQUESTS,
        request_timeout_seconds=REQUEST_TIMEOUT,
        retry_enabled=ENABLE_RETRY,
        debug_mode=DEBUG,
    )


# =============================================================================
# STANDALONE USAGE
# =============================================================================

if __name__ == "__main__":
    print_config_summary()
    validate_config()

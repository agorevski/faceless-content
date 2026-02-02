"""
Text-to-Speech Module - LEGACY WRAPPER.

⚠️ DEPRECATED: This module is a backward-compatibility wrapper.
Please use faceless.services.tts_service.TTSService for new code.

This wrapper delegates to the modern implementation in src/faceless/services/
while maintaining the original API for existing scripts.
"""

import json
import os
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from faceless.utils.logging import get_logger

logger = get_logger(__name__)

# Issue deprecation warning on import
warnings.warn(
    "pipeline/tts_generator.py is deprecated. "
    "Use faceless.services.tts_service.TTSService instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Import modern implementations
from faceless.clients.azure_openai import AzureOpenAIClient
from faceless.core.enums import Voice  # noqa: E402

# Import legacy config for backward compatibility
from env_config import (  # noqa: E402
    ELEVENLABS_API_KEY,
    PATHS,
    USE_ELEVENLABS,
    VOICE_SETTINGS,
)

# Module-level client (lazy initialization)
_client: AzureOpenAIClient | None = None


def _get_client() -> AzureOpenAIClient:
    """Get or create the AzureOpenAIClient singleton."""
    global _client
    if _client is None:
        _client = AzureOpenAIClient()
    return _client


def _get_voice_enum(voice_name: str) -> Voice:
    """Convert voice name string to Voice enum."""
    # Map OpenAI voice names to enum
    voice_map = {
        "onyx": Voice.ONYX,
        "alloy": Voice.ALLOY,
        "echo": Voice.ECHO,
        "fable": Voice.FABLE,
        "nova": Voice.NOVA,
        "shimmer": Voice.SHIMMER,
        "coral": Voice.CORAL,
        "sage": Voice.SAGE,
        "verse": Voice.VERSE,
        "ballad": Voice.BALLAD,
        "ash": Voice.ASH,
    }
    return voice_map.get(voice_name.lower(), Voice.ONYX)


def generate_azure_openai_tts(
    text: str,
    niche: str,
    output_name: str,
) -> str:
    """
    Generate speech using Azure OpenAI TTS (gpt-4o-mini-tts or similar).

    ⚠️ DEPRECATED: Use TTSService.generate_for_scene() instead.

    Args:
        text: Text to convert to speech
        niche: One of "scary-stories", "finance", "luxury", etc.
        output_name: Filename (without extension)

    Returns:
        Path to the saved audio file
    """
    settings = VOICE_SETTINGS[niche]
    voice_name = settings.get("openai_voice", "onyx")
    speed = settings.get("openai_speed", 1.0)

    # Determine output path early to check for existing file
    output_dir = PATHS[niche]["audio"]
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{output_name}.mp3")

    # Skip generation if file already exists
    if os.path.exists(output_path):
        logger.info("Audio already exists, skipping", output_path=output_path)
        return output_path

    logger.info(
        "Generating audio",
        output_name=output_name,
        voice=voice_name,
        speed=speed,
        text_preview=text[:60],
    )

    try:
        client = _get_client()
        voice_enum = _get_voice_enum(voice_name)

        client.save_audio(
            text=text,
            output_path=Path(output_path),
            voice=voice_enum,
            speed=speed,
        )

        logger.info("Audio saved", output_path=output_path)
        return output_path

    except Exception as e:
        logger.error("TTS generation failed", error=str(e))
        raise


def generate_elevenlabs_tts(
    text: str,
    niche: str,
    output_name: str,
) -> str:
    """
    Generate speech using ElevenLabs API.

    ⚠️ DEPRECATED: ElevenLabs is not supported in modern services.
    Consider migrating to Azure OpenAI TTS.

    Args:
        text: Text to convert to speech
        niche: One of "scary-stories", "finance", "luxury", etc.
        output_name: Filename (without extension)

    Returns:
        Path to the saved audio file
    """
    import requests

    settings = VOICE_SETTINGS[niche]
    voice_id = settings.get("elevenlabs_voice_id")

    if not voice_id:
        raise ValueError(f"No ElevenLabs voice ID configured for {niche}")

    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY not set in config.py")

    # Determine output path early to check for existing file
    output_dir = PATHS[niche]["audio"]
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{output_name}.mp3")

    # Skip generation if file already exists
    if os.path.exists(output_path):
        logger.info("Audio already exists, skipping", output_path=output_path)
        return output_path

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY,
    }

    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
        },
    }

    logger.info(
        "Generating audio with ElevenLabs",
        output_name=output_name,
        voice_id=voice_id,
        text_preview=text[:60],
    )

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(response.content)

        logger.info("Audio saved", output_path=output_path)
        return output_path

    except requests.exceptions.RequestException as e:
        logger.error("ElevenLabs TTS generation failed", error=str(e))
        raise


def generate_tts(
    text: str,
    niche: str,
    output_name: str,
) -> str:
    """
    Generate speech using the configured TTS provider.

    ⚠️ DEPRECATED: Use TTSService.generate_for_scene() instead.

    Uses ElevenLabs if USE_ELEVENLABS is True, otherwise Azure OpenAI TTS.

    Args:
        text: Text to convert to speech
        niche: One of "scary-stories", "finance", "luxury", etc.
        output_name: Filename (without extension)

    Returns:
        Path to the saved audio file
    """
    if USE_ELEVENLABS:
        return generate_elevenlabs_tts(text, niche, output_name)
    else:
        return generate_azure_openai_tts(text, niche, output_name)


def generate_from_script(
    script_path: str,
    niche: str,
    max_workers: int = 5,
) -> list:
    """
    Generate audio for all scenes in a script concurrently.

    ⚠️ DEPRECATED: Use TTSService.generate_for_script() instead.

    Args:
        script_path: Path to script JSON file
        niche: One of "scary-stories", "finance", "luxury", etc.
        max_workers: Maximum number of concurrent TTS generations (default: 5)

    Returns:
        List of paths to generated audio files (in same order as scenes)
    """
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    base_name = os.path.splitext(os.path.basename(script_path))[0]
    scenes = script["scenes"]

    # Pre-allocate results list to preserve order
    paths = [None] * len(scenes)

    def generate_single(index: int, scene: dict) -> tuple:
        """Generate TTS for a single scene and return (index, path)."""
        output_name = f"{base_name}_{index:03d}"
        try:
            path = generate_tts(scene["narration"], niche, output_name)
            return (index, path)
        except Exception as e:
            logger.warning("Skipping scene", scene_index=index, error=str(e))
            return (index, None)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(generate_single, i, scene): i
            for i, scene in enumerate(scenes, 1)
        }
        for future in as_completed(futures):
            index, path = future.result()
            paths[index - 1] = path

    return paths


def generate_full_narration(
    script_path: str,
    niche: str,
) -> str:
    """
    Generate a single audio file for the entire script narration.

    ⚠️ DEPRECATED: Use TTSService instead.

    Args:
        script_path: Path to script JSON file
        niche: One of "scary-stories", "finance", "luxury", etc.

    Returns:
        Path to the generated audio file
    """
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    full_text = " ... ".join(scene["narration"] for scene in script["scenes"])
    base_name = os.path.splitext(os.path.basename(script_path))[0]

    return generate_tts(full_text, niche, f"{base_name}_full")


# =============================================================================
# STANDALONE USAGE
# =============================================================================

if __name__ == "__main__":
    import argparse
    from datetime import datetime

    parser = argparse.ArgumentParser(
        description="Generate TTS audio for faceless content"
    )
    parser.add_argument("text", help="Text to convert to speech")
    parser.add_argument(
        "--niche", "-n", choices=["scary-stories", "finance", "luxury"], required=True
    )
    parser.add_argument(
        "--name", "-o", default=None, help="Output filename (without extension)"
    )
    parser.add_argument(
        "--elevenlabs",
        "-e",
        action="store_true",
        help="Use ElevenLabs instead of Azure",
    )

    args = parser.parse_args()

    use_elevenlabs_override = USE_ELEVENLABS
    if args.elevenlabs:
        use_elevenlabs_override = True  # noqa: F841 - used for reference

    output_name = args.name or f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    generate_tts(args.text, args.niche, output_name)

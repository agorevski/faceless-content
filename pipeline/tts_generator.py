"""
Text-to-Speech Module
Generates voiceovers using Azure OpenAI TTS (gpt-4o-mini-tts) or ElevenLabs
"""

import os
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_TTS_DEPLOYMENT,
    AZURE_OPENAI_TTS_API_VERSION,
    ELEVENLABS_API_KEY,
    VOICE_SETTINGS,
    PATHS,
    USE_ELEVENLABS,
)


def generate_azure_openai_tts(
    text: str,
    niche: str,
    output_name: str,
) -> str:
    """
    Generate speech using Azure OpenAI TTS (gpt-4o-mini-tts or similar).

    Args:
        text: Text to convert to speech
        niche: One of "scary-stories", "finance", "luxury"
        output_name: Filename (without extension)

    Returns:
        Path to the saved audio file
    """

    settings = VOICE_SETTINGS[niche]
    voice = settings.get("openai_voice", "onyx")
    speed = settings.get("openai_speed", 1.0)

    # Determine output path early to check for existing file
    output_dir = PATHS[niche]["audio"]
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{output_name}.mp3")

    # Skip generation if file already exists
    if os.path.exists(output_path):
        print(f"🎙️ Audio already exists, skipping: {output_path}")
        return output_path

    # Azure OpenAI TTS endpoint
    url = f"{AZURE_OPENAI_ENDPOINT}openai/deployments/{AZURE_OPENAI_TTS_DEPLOYMENT}/audio/speech?api-version={AZURE_OPENAI_TTS_API_VERSION}"

    headers = {
        "api-key": AZURE_OPENAI_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "model": AZURE_OPENAI_TTS_DEPLOYMENT,
        "input": text,
        "voice": voice,
        "speed": speed,
        "response_format": "mp3",
    }

    print(f"🎙️ Generating audio: {output_name}")
    print(f"   Voice: {voice} | Speed: {speed}")
    print(f"   Text: {text[:60]}...")

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=180)
        response.raise_for_status()

        # Save the audio
        with open(output_path, "wb") as f:
            f.write(response.content)

        print(f"   ✅ Saved: {output_path}")
        return output_path

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"   Response: {e.response.text}")
        raise


def generate_elevenlabs_tts(
    text: str,
    niche: str,
    output_name: str,
) -> str:
    """
    Generate speech using ElevenLabs API.

    Args:
        text: Text to convert to speech
        niche: One of "scary-stories", "finance", "luxury"
        output_name: Filename (without extension)

    Returns:
        Path to the saved audio file
    """

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
        print(f"🎙️ Audio already exists, skipping: {output_path}")
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

    print(f"🎙️ Generating audio (ElevenLabs): {output_name}")
    print(f"   Voice ID: {voice_id}")
    print(f"   Text: {text[:60]}...")

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()

        # Save the audio
        with open(output_path, "wb") as f:
            f.write(response.content)

        print(f"   ✅ Saved: {output_path}")
        return output_path

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
        raise


def generate_tts(
    text: str,
    niche: str,
    output_name: str,
) -> str:
    """
    Generate speech using the configured TTS provider.

    Uses ElevenLabs if USE_ELEVENLABS is True, otherwise Azure OpenAI TTS.

    Args:
        text: Text to convert to speech
        niche: One of "scary-stories", "finance", "luxury"
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

    Args:
        script_path: Path to script JSON file
        niche: One of "scary-stories", "finance", "luxury"
        max_workers: Maximum number of concurrent TTS generations (default: 5)

    Returns:
        List of paths to generated audio files (in same order as scenes)
    """

    import json

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
            print(f"   ⚠️ Skipping scene {index}: {e}")
            return (index, None)

    # Use ThreadPoolExecutor for concurrent generation
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = {
            executor.submit(generate_single, i, scene): i
            for i, scene in enumerate(scenes, 1)
        }

        # Collect results as they complete
        for future in as_completed(futures):
            index, path = future.result()
            paths[index - 1] = path  # Convert 1-based index to 0-based

    return paths


def generate_full_narration(
    script_path: str,
    niche: str,
) -> str:
    """
    Generate a single audio file for the entire script narration.
    Good for YouTube videos where you want continuous narration.

    Args:
        script_path: Path to script JSON file
        niche: One of "scary-stories", "finance", "luxury"

    Returns:
        Path to the generated audio file
    """

    import json

    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    # Combine all narrations with pauses
    full_text = " ... ".join(scene["narration"] for scene in script["scenes"])

    base_name = os.path.splitext(os.path.basename(script_path))[0]
    return generate_tts(full_text, niche, f"{base_name}_full")


# =============================================================================
# STANDALONE USAGE
# =============================================================================

if __name__ == "__main__":
    import argparse

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

    if args.elevenlabs:
        from config import USE_ELEVENLABS

        USE_ELEVENLABS = True

    output_name = args.name or f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    generate_tts(args.text, args.niche, output_name)

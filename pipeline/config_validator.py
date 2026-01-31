"""
Configuration Validator Module
Validates API keys and settings before running the pipeline
Prevents wasted API calls and provides clear error messages
"""

import os
import sys
import requests
from typing import List, Tuple, Optional

# Add pipeline directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_IMAGE_DEPLOYMENT,
    AZURE_OPENAI_IMAGE_API_VERSION,
    AZURE_OPENAI_CHAT_DEPLOYMENT,
    AZURE_OPENAI_CHAT_API_VERSION,
    AZURE_OPENAI_TTS_DEPLOYMENT,
    AZURE_OPENAI_TTS_API_VERSION,
    ELEVENLABS_API_KEY,
    USE_ELEVENLABS,
    VOICE_SETTINGS,
    IMAGE_SETTINGS,
    PATHS,
)


def check_azure_openai_endpoint() -> Tuple[bool, str]:
    """Check if Azure OpenAI endpoint is configured and reachable."""
    if not AZURE_OPENAI_ENDPOINT:
        return False, "AZURE_OPENAI_ENDPOINT is not set"

    if not AZURE_OPENAI_ENDPOINT.startswith("https://"):
        return False, "AZURE_OPENAI_ENDPOINT should start with 'https://'"

    if not AZURE_OPENAI_ENDPOINT.endswith("/"):
        return False, "AZURE_OPENAI_ENDPOINT should end with '/'"

    return True, "Azure OpenAI endpoint configured"


def check_azure_openai_key() -> Tuple[bool, str]:
    """Check if Azure OpenAI API key is configured."""
    if not AZURE_OPENAI_KEY:
        return False, "AZURE_OPENAI_KEY is not set"

    if len(AZURE_OPENAI_KEY) < 20:
        return False, "AZURE_OPENAI_KEY appears to be invalid (too short)"

    if AZURE_OPENAI_KEY == "your-api-key-here":
        return False, "AZURE_OPENAI_KEY is still set to placeholder value"

    return True, "Azure OpenAI API key configured"


def check_image_deployment(test_connection: bool = False) -> Tuple[bool, str]:
    """Check if image generation deployment is configured."""
    if not AZURE_OPENAI_IMAGE_DEPLOYMENT:
        return False, "AZURE_OPENAI_IMAGE_DEPLOYMENT is not set"

    if test_connection:
        try:
            # Just check if deployment exists by making a minimal request
            url = (
                f"{AZURE_OPENAI_ENDPOINT}openai/deployments/"
                f"{AZURE_OPENAI_IMAGE_DEPLOYMENT}/images/generations"
                f"?api-version={AZURE_OPENAI_IMAGE_API_VERSION}"
            )
            headers = {
                "Content-Type": "application/json",
                "api-key": AZURE_OPENAI_KEY,
            }
            # Send minimal payload - will fail but confirm deployment exists
            response = requests.post(
                url,
                headers=headers,
                json={"prompt": "test", "n": 1, "size": "1024x1024"},
                timeout=10,
            )
            # 400 = bad request but deployment exists
            # 404 = deployment not found
            if response.status_code == 404:
                return (
                    False,
                    f"Image deployment '{AZURE_OPENAI_IMAGE_DEPLOYMENT}' not found",
                )
            return True, f"Image deployment '{AZURE_OPENAI_IMAGE_DEPLOYMENT}' verified"
        except requests.exceptions.RequestException as e:
            return False, f"Could not verify image deployment: {e}"

    return True, f"Image deployment configured: {AZURE_OPENAI_IMAGE_DEPLOYMENT}"


def check_chat_deployment(test_connection: bool = False) -> Tuple[bool, str]:
    """Check if chat/completion deployment is configured."""
    if not AZURE_OPENAI_CHAT_DEPLOYMENT:
        return False, "AZURE_OPENAI_CHAT_DEPLOYMENT is not set"

    if test_connection:
        try:
            url = (
                f"{AZURE_OPENAI_ENDPOINT}openai/deployments/"
                f"{AZURE_OPENAI_CHAT_DEPLOYMENT}/chat/completions"
                f"?api-version={AZURE_OPENAI_CHAT_API_VERSION}"
            )
            headers = {
                "Content-Type": "application/json",
                "api-key": AZURE_OPENAI_KEY,
            }
            response = requests.post(
                url,
                headers=headers,
                json={
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1,
                },
                timeout=10,
            )
            if response.status_code == 404:
                return (
                    False,
                    f"Chat deployment '{AZURE_OPENAI_CHAT_DEPLOYMENT}' not found",
                )
            return True, f"Chat deployment '{AZURE_OPENAI_CHAT_DEPLOYMENT}' verified"
        except requests.exceptions.RequestException as e:
            return False, f"Could not verify chat deployment: {e}"

    return True, f"Chat deployment configured: {AZURE_OPENAI_CHAT_DEPLOYMENT}"


def check_tts_deployment(test_connection: bool = False) -> Tuple[bool, str]:
    """Check if TTS deployment is configured."""
    if not AZURE_OPENAI_TTS_DEPLOYMENT:
        return False, "AZURE_OPENAI_TTS_DEPLOYMENT is not set"

    if test_connection:
        try:
            url = (
                f"{AZURE_OPENAI_ENDPOINT}openai/deployments/"
                f"{AZURE_OPENAI_TTS_DEPLOYMENT}/audio/speech"
                f"?api-version={AZURE_OPENAI_TTS_API_VERSION}"
            )
            headers = {
                "Content-Type": "application/json",
                "api-key": AZURE_OPENAI_KEY,
            }
            response = requests.post(
                url,
                headers=headers,
                json={"input": "test", "voice": "alloy"},
                timeout=10,
            )
            if response.status_code == 404:
                return (
                    False,
                    f"TTS deployment '{AZURE_OPENAI_TTS_DEPLOYMENT}' not found",
                )
            return True, f"TTS deployment '{AZURE_OPENAI_TTS_DEPLOYMENT}' verified"
        except requests.exceptions.RequestException as e:
            return False, f"Could not verify TTS deployment: {e}"

    return True, f"TTS deployment configured: {AZURE_OPENAI_TTS_DEPLOYMENT}"


def check_elevenlabs_config() -> Tuple[bool, str]:
    """Check ElevenLabs configuration if enabled."""
    if not USE_ELEVENLABS:
        return True, "ElevenLabs not enabled (using Azure TTS)"

    if not ELEVENLABS_API_KEY:
        return False, "USE_ELEVENLABS is True but ELEVENLABS_API_KEY is not set"

    # Check that voice IDs are configured for each niche
    missing_voices = []
    for niche, settings in VOICE_SETTINGS.items():
        if not settings.get("elevenlabs_voice_id"):
            missing_voices.append(niche)

    if missing_voices:
        return False, f"ElevenLabs voice IDs missing for: {', '.join(missing_voices)}"

    return True, "ElevenLabs configured"


def check_voice_settings() -> Tuple[bool, str]:
    """Check that voice settings are configured for all niches."""
    required_niches = ["scary-stories", "finance", "luxury"]
    missing = [n for n in required_niches if n not in VOICE_SETTINGS]

    if missing:
        return False, f"Voice settings missing for niches: {', '.join(missing)}"

    return True, "Voice settings configured for all niches"


def check_image_settings() -> Tuple[bool, str]:
    """Check that image settings are configured for all niches."""
    required_niches = ["scary-stories", "finance", "luxury"]
    missing = [n for n in required_niches if n not in IMAGE_SETTINGS]

    if missing:
        return False, f"Image settings missing for niches: {', '.join(missing)}"

    return True, "Image settings configured for all niches"


def check_paths() -> Tuple[bool, str]:
    """Check that all required paths are configured."""
    required_niches = ["scary-stories", "finance", "luxury", "shared"]
    missing = [n for n in required_niches if n not in PATHS]

    if missing:
        return False, f"Paths missing for: {', '.join(missing)}"

    return True, "All paths configured"


def check_ffmpeg() -> Tuple[bool, str]:
    """Check if FFmpeg is installed and accessible."""
    import subprocess

    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            # Extract version from first line
            version_line = result.stdout.split("\n")[0]
            return True, f"FFmpeg installed: {version_line[:50]}..."
        return False, "FFmpeg returned non-zero exit code"
    except FileNotFoundError:
        return False, "FFmpeg not found. Install it and add to PATH."
    except subprocess.TimeoutExpired:
        return False, "FFmpeg check timed out"
    except Exception as e:
        return False, f"Error checking FFmpeg: {e}"


def check_ffprobe() -> Tuple[bool, str]:
    """Check if FFprobe is installed and accessible."""
    import subprocess

    try:
        result = subprocess.run(
            ["ffprobe", "-version"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return True, "FFprobe installed"
        return False, "FFprobe returned non-zero exit code"
    except FileNotFoundError:
        return False, "FFprobe not found (usually installed with FFmpeg)"
    except Exception as e:
        return False, f"Error checking FFprobe: {e}"


def validate_all(
    test_connections: bool = False, verbose: bool = True
) -> Tuple[bool, List[str], List[str]]:
    """
    Run all validation checks.

    Args:
        test_connections: Whether to test actual API connectivity
        verbose: Whether to print results

    Returns:
        Tuple of (all_passed, list_of_errors, list_of_warnings)
    """
    checks = [
        ("Azure OpenAI Endpoint", check_azure_openai_endpoint),
        ("Azure OpenAI Key", check_azure_openai_key),
        ("Image Deployment", lambda: check_image_deployment(test_connections)),
        ("Chat Deployment", lambda: check_chat_deployment(test_connections)),
        ("TTS Deployment", lambda: check_tts_deployment(test_connections)),
        ("ElevenLabs Config", check_elevenlabs_config),
        ("Voice Settings", check_voice_settings),
        ("Image Settings", check_image_settings),
        ("Paths Config", check_paths),
        ("FFmpeg", check_ffmpeg),
        ("FFprobe", check_ffprobe),
    ]

    errors = []
    warnings = []
    all_passed = True

    if verbose:
        print("\n" + "=" * 60)
        print("🔍 CONFIGURATION VALIDATION")
        print("=" * 60 + "\n")

    for name, check_func in checks:
        try:
            passed, message = check_func()

            if verbose:
                status = "✅" if passed else "❌"
                print(f"   {status} {name}: {message}")

            if not passed:
                # FFmpeg/FFprobe are warnings for config check, errors for full pipeline
                if name in ["FFmpeg", "FFprobe"]:
                    warnings.append(f"{name}: {message}")
                else:
                    errors.append(f"{name}: {message}")
                    all_passed = False

        except Exception as e:
            if verbose:
                print(f"   ⚠️ {name}: Exception during check - {e}")
            warnings.append(f"{name}: Check failed with exception - {e}")

    if verbose:
        print("\n" + "-" * 60)
        if all_passed:
            print("✅ All critical checks passed!")
        else:
            print(f"❌ {len(errors)} error(s) found")

        if warnings:
            print(f"⚠️ {len(warnings)} warning(s)")

        print("-" * 60 + "\n")

    return all_passed, errors, warnings


def validate_for_pipeline(niche: str = None) -> bool:
    """
    Validate configuration for running the full pipeline.

    Args:
        niche: Optional specific niche to validate

    Returns:
        True if ready to run, False otherwise
    """
    all_passed, errors, warnings = validate_all(test_connections=False, verbose=True)

    if not all_passed:
        print("❌ Fix the above errors before running the pipeline.")
        return False

    # Check FFmpeg for pipeline (required)
    ffmpeg_ok, ffmpeg_msg = check_ffmpeg()
    if not ffmpeg_ok:
        print(f"❌ FFmpeg is required for video assembly: {ffmpeg_msg}")
        return False

    # Check niche-specific settings if specified
    if niche:
        if niche not in VOICE_SETTINGS:
            print(f"❌ No voice settings for niche: {niche}")
            return False
        if niche not in IMAGE_SETTINGS:
            print(f"❌ No image settings for niche: {niche}")
            return False
        if niche not in PATHS:
            print(f"❌ No paths configured for niche: {niche}")
            return False

    print("✅ Configuration validated. Ready to run pipeline.")
    return True


# =============================================================================
# STANDALONE USAGE
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate pipeline configuration")
    parser.add_argument(
        "--test-connections",
        "-t",
        action="store_true",
        help="Test actual API connectivity (makes API calls)",
    )
    parser.add_argument(
        "--niche",
        "-n",
        choices=["scary-stories", "finance", "luxury"],
        help="Validate for a specific niche",
    )
    parser.add_argument("--quiet", "-q", action="store_true", help="Only output errors")

    args = parser.parse_args()

    if args.niche:
        success = validate_for_pipeline(args.niche)
    else:
        all_passed, errors, warnings = validate_all(
            test_connections=args.test_connections, verbose=not args.quiet
        )
        success = all_passed

    sys.exit(0 if success else 1)

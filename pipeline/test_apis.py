"""
Quick test script to verify API connections
"""

import sys
import os

# Add pipeline to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from faceless.utils.logging import get_logger

logger = get_logger(__name__)

from env_config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_IMAGE_DEPLOYMENT,
    AZURE_OPENAI_IMAGE_API_VERSION,
    AZURE_OPENAI_TTS_DEPLOYMENT,
    AZURE_OPENAI_TTS_API_VERSION,
    PATHS,
)


def test_tts():
    """Test Azure OpenAI TTS"""
    logger.info("Testing Azure OpenAI TTS")

    import requests

    url = f"{AZURE_OPENAI_ENDPOINT}openai/deployments/{AZURE_OPENAI_TTS_DEPLOYMENT}/audio/speech?api-version={AZURE_OPENAI_TTS_API_VERSION}"

    headers = {
        "api-key": AZURE_OPENAI_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "model": AZURE_OPENAI_TTS_DEPLOYMENT,
        "input": "Testing one two three. The voice sounds creepy and perfect for horror stories.",
        "voice": "onyx",
        "speed": 0.9,
        "response_format": "mp3",
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        # Save test audio
        output_dir = PATHS["scary-stories"]["audio"]
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "test_audio.mp3")

        with open(output_path, "wb") as f:
            f.write(response.content)

        logger.info("TTS SUCCESS", output_path=str(output_path), file_size_bytes=len(response.content))
        return True

    except Exception as e:
        error_response = None
        if hasattr(e, "response") and e.response is not None:
            error_response = e.response.text
        logger.error("TTS FAILED", error=str(e), response=error_response)
        return False


def test_image():
    """Test Azure OpenAI Image Generation"""
    logger.info("Testing Azure OpenAI Image Generation")

    import requests
    import base64

    url = f"{AZURE_OPENAI_ENDPOINT}openai/deployments/{AZURE_OPENAI_IMAGE_DEPLOYMENT}/images/generations?api-version={AZURE_OPENAI_IMAGE_API_VERSION}"

    headers = {
        "api-key": AZURE_OPENAI_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "prompt": "A mysterious wooden staircase standing alone in a dark foggy forest at night, horror movie cinematography, eerie atmosphere, volumetric lighting",
        "size": "1536x1024",
        "quality": "high",
        "n": 1,
    }

    try:
        logger.info("Generating image", note="this may take 30-60 seconds")
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()

        if "data" in result and len(result["data"]) > 0:
            image_data = result["data"][0]

            # Get image bytes
            if "url" in image_data:
                img_response = requests.get(image_data["url"], timeout=60)
                img_bytes = img_response.content
            elif "b64_json" in image_data:
                img_bytes = base64.b64decode(image_data["b64_json"])
            else:
                raise ValueError("Unexpected response format")

            # Save test image
            output_dir = PATHS["scary-stories"]["images"]
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, "test_image.png")

            with open(output_path, "wb") as f:
                f.write(img_bytes)

            logger.info("IMAGE SUCCESS", output_path=str(output_path), file_size_bytes=len(img_bytes))
            return True
        else:
            logger.error("No image data in response", response=result)
            return False

    except Exception as e:
        error_response = None
        if hasattr(e, "response") and e.response is not None:
            error_response = e.response.text
        logger.error("IMAGE FAILED", error=str(e), response=error_response)
        return False


def test_ffmpeg():
    """Test FFmpeg"""
    logger.info("Testing FFmpeg")

    import subprocess

    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            version_line = result.stdout.split("\n")[0]
            logger.info("FFMPEG SUCCESS", version=version_line)
            return True
        else:
            logger.error("FFmpeg error", stderr=result.stderr)
            return False
    except Exception as e:
        logger.error("FFmpeg not found", error=str(e))
        return False


if __name__ == "__main__":
    logger.info("FACELESS CONTENT PIPELINE - API TEST")

    results = {
        "FFmpeg": test_ffmpeg(),
        "TTS": test_tts(),
        "Image": test_image(),
    }

    logger.info("TEST SUMMARY")

    all_passed = True
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        logger.info("Test result", test=name, status=status)
        if not passed:
            all_passed = False

    if all_passed:
        logger.info("All tests passed! Ready to produce content!")
    else:
        logger.warning("Some tests failed. Check the errors above.")

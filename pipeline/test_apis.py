"""
Quick test script to verify API connections
"""

import sys
import os

# Add pipeline to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
    print("\n" + "=" * 50)
    print("🎙️ Testing Azure OpenAI TTS...")
    print("=" * 50)

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

        print(f"✅ TTS SUCCESS! Saved to: {output_path}")
        print(f"   File size: {len(response.content):,} bytes")
        return True

    except Exception as e:
        print(f"❌ TTS FAILED: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"   Response: {e.response.text}")
        return False


def test_image():
    """Test Azure OpenAI Image Generation"""
    print("\n" + "=" * 50)
    print("🎨 Testing Azure OpenAI Image Generation...")
    print("=" * 50)

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
        print("   Generating image (this may take 30-60 seconds)...")
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

            print(f"✅ IMAGE SUCCESS! Saved to: {output_path}")
            print(f"   File size: {len(img_bytes):,} bytes")
            return True
        else:
            print(f"❌ No image data in response: {result}")
            return False

    except Exception as e:
        print(f"❌ IMAGE FAILED: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"   Response: {e.response.text}")
        return False


def test_ffmpeg():
    """Test FFmpeg"""
    print("\n" + "=" * 50)
    print("🎬 Testing FFmpeg...")
    print("=" * 50)

    import subprocess

    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            version_line = result.stdout.split("\n")[0]
            print(f"✅ FFMPEG SUCCESS! {version_line}")
            return True
        else:
            print(f"❌ FFmpeg error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ FFmpeg not found: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🧪 FACELESS CONTENT PIPELINE - API TEST")
    print("=" * 50)

    results = {
        "FFmpeg": test_ffmpeg(),
        "TTS": test_tts(),
        "Image": test_image(),
    }

    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {name}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n🎉 All tests passed! Ready to produce content!")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")

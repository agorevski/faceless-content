"""
Image Generator Module
Generates images using Azure OpenAI (GPT-Image-1)
Enhanced with cinematographic prompt engineering for high-quality outputs
"""

import os
import json
import base64
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from env_config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_IMAGE_DEPLOYMENT,
    AZURE_OPENAI_IMAGE_API_VERSION,
    IMAGE_SETTINGS,
    PATHS,
    build_enhanced_prompt,
)

# Note: build_enhanced_prompt is imported from env_config (shared/prompts/image_prompts.py)


def generate_image(
    prompt: str,
    niche: str,
    output_name: str,
    platform: str = "youtube",
    save_prompt: bool = True,
    visual_style: dict = None,
) -> str:
    """
    Generate an image using Azure OpenAI GPT-Image-1.

    Args:
        prompt: Description of the image to generate
        niche: One of "scary-stories", "finance", "luxury"
        output_name: Filename (without extension)
        platform: "youtube" (16:9) or "tiktok" (9:16)
        save_prompt: Whether to save the prompt alongside the image
        visual_style: Optional story-level visual style for continuity

    Returns:
        Path to the saved image
    """

    settings = IMAGE_SETTINGS[niche]
    size = settings["size"] if platform == "youtube" else settings["size_tiktok"]

    # Determine output path early to check for existing file
    output_dir = PATHS[niche]["images"]
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{output_name}.png")

    # Skip generation if file already exists
    if os.path.exists(output_path):
        print(f"🎨 Image already exists, skipping: {output_path}")
        return output_path

    # Build enhanced prompt using the new cinematographic system
    enhanced_prompt = build_enhanced_prompt(prompt, niche, visual_style)

    # Prepare the API request
    url = f"{AZURE_OPENAI_ENDPOINT}openai/deployments/{AZURE_OPENAI_IMAGE_DEPLOYMENT}/images/generations?api-version={AZURE_OPENAI_IMAGE_API_VERSION}"

    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_OPENAI_KEY,
    }

    payload = {
        "prompt": enhanced_prompt,
        "size": size,
        "quality": settings.get("quality", "high"),
        "n": 1,
    }

    print(f"🎨 Generating image: {output_name}")
    print(f"   Prompt: {prompt[:80]}...")

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()

        # Handle different response formats
        if "data" in result and len(result["data"]) > 0:
            image_data = result["data"][0]

            # Check if we got a URL or base64 data
            if "url" in image_data:
                # Download from URL
                img_response = requests.get(image_data["url"], timeout=60)
                img_bytes = img_response.content
            elif "b64_json" in image_data:
                # Decode base64
                img_bytes = base64.b64decode(image_data["b64_json"])
            else:
                raise ValueError("Unexpected response format from API")

            # Save the image
            with open(output_path, "wb") as f:
                f.write(img_bytes)

            print(f"   ✅ Saved: {output_path}")

            # Optionally save the prompt for reference
            if save_prompt:
                prompt_path = os.path.join(output_dir, f"{output_name}_prompt.txt")
                with open(prompt_path, "w", encoding="utf-8") as f:
                    f.write(f"Original: {prompt}\n\nEnhanced: {enhanced_prompt}")

            return output_path
        else:
            raise ValueError(f"No image data in response: {result}")

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"   Response: {e.response.text}")
        raise


def generate_batch(
    prompts: list,
    niche: str,
    base_name: str,
    platform: str = "youtube",
    visual_style: dict = None,
    max_workers: int = 5,
) -> list:
    """
    Generate multiple images from a list of prompts concurrently.

    Args:
        prompts: List of image descriptions
        niche: One of "scary-stories", "finance", "luxury"
        base_name: Base filename (will be numbered)
        platform: "youtube" or "tiktok"
        visual_style: Optional story-level visual style for continuity
        max_workers: Maximum number of concurrent image generations (default: 5)

    Returns:
        List of paths to saved images (in same order as prompts)
    """

    # Pre-allocate results list to preserve order
    paths = [None] * len(prompts)

    def generate_single(index: int, prompt: str) -> tuple:
        """Generate a single image and return (index, path)."""
        output_name = f"{base_name}_{index:03d}"
        try:
            path = generate_image(
                prompt,
                niche,
                output_name,
                platform,
                save_prompt=True,
                visual_style=visual_style,
            )
            return (index, path)
        except Exception as e:
            print(f"   ⚠️ Skipping image {index}: {e}")
            return (index, None)

    # Use ThreadPoolExecutor for concurrent generation
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = {
            executor.submit(generate_single, i, prompt): i
            for i, prompt in enumerate(prompts, 1)
        }

        # Collect results as they complete
        for future in as_completed(futures):
            index, path = future.result()
            paths[index - 1] = path  # Convert 1-based index to 0-based

    return paths


def generate_from_script(
    script_path: str,
    niche: str,
    platform: str = "youtube",
) -> list:
    """
    Generate images based on a script JSON file.

    The script JSON should have:
    - "scenes": Array with objects containing:
      - "image_prompt": Description for image generation
      - "narration": Text to be spoken (used for TTS separately)
    - "visual_style" (optional): Object for artistic continuity:
      - "environment": Consistent setting description
      - "color_mood": Color grading guidelines
      - "texture": Texture and material details
      - "recurring_elements": Dict of named elements with descriptions

    Args:
        script_path: Path to the script JSON file
        niche: One of "scary-stories", "finance", "luxury"
        platform: "youtube" or "tiktok"

    Returns:
        List of paths to generated images
    """

    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    base_name = os.path.splitext(os.path.basename(script_path))[0]
    prompts = [scene["image_prompt"] for scene in script["scenes"]]

    # Extract visual_style from script for artistic continuity
    visual_style = script.get("visual_style", None)

    print(f"📖 Generating {len(prompts)} images for: {base_name}")
    if visual_style:
        print("   🎨 Using custom visual style for artistic continuity")

    return generate_batch(prompts, niche, base_name, platform, visual_style)


# =============================================================================
# STANDALONE USAGE
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate images for faceless content")
    parser.add_argument("prompt", help="Image description")
    parser.add_argument(
        "--niche", "-n", choices=["scary-stories", "finance", "luxury"], required=True
    )
    parser.add_argument(
        "--name", "-o", default=None, help="Output filename (without extension)"
    )
    parser.add_argument(
        "--platform", "-p", choices=["youtube", "tiktok"], default="youtube"
    )

    args = parser.parse_args()

    output_name = args.name or f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    generate_image(args.prompt, args.niche, output_name, args.platform)

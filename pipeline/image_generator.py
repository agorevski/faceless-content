"""
Image Generator Module - LEGACY WRAPPER.

⚠️ DEPRECATED: This module is a backward-compatibility wrapper.
Please use faceless.services.image_service.ImageService for new code.

This wrapper delegates to the modern implementation in src/faceless/services/
while maintaining the original API for existing scripts.
"""

import json
import os
import warnings
from pathlib import Path

from faceless.utils.logging import get_logger

# Issue deprecation warning on import
warnings.warn(
    "pipeline/image_generator.py is deprecated. "
    "Use faceless.services.image_service.ImageService instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Import modern implementations
from faceless.clients.azure_openai import AzureOpenAIClient
from faceless.core.enums import Niche, Platform
from faceless.services.image_service import ImageService  # noqa: F401

# Import legacy config for backward compatibility
from env_config import PATHS, build_enhanced_prompt  # noqa: E402

# Module-level service instance (lazy initialization)
_service: ImageService | None = None
_client: AzureOpenAIClient | None = None


def _get_service() -> ImageService:
    """Get or create the ImageService singleton."""
    global _service, _client
    if _service is None:
        _client = AzureOpenAIClient()
        _service = ImageService(client=_client)
    return _service


def _niche_str_to_enum(niche: str) -> Niche:
    """Convert niche string to Niche enum."""
    return Niche(niche)


def _platform_str_to_enum(platform: str) -> Platform:
    """Convert platform string to Platform enum."""
    return Platform(platform)


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

    ⚠️ DEPRECATED: Use ImageService.generate_for_scene() instead.

    Args:
        prompt: Description of the image to generate
        niche: One of "scary-stories", "finance", "luxury", etc.
        output_name: Filename (without extension)
        platform: "youtube" (16:9) or "tiktok" (9:16)
        save_prompt: Whether to save the prompt alongside the image
        visual_style: Optional story-level visual style for continuity

    Returns:
        Path to the saved image
    """
    # Determine output path early to check for existing file
    output_dir = PATHS[niche]["images"]
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{output_name}.png")

    # Skip generation if file already exists
    if os.path.exists(output_path):
        logger.info("Image already exists, skipping", path=output_path)
        return output_path

    # Build enhanced prompt using the cinematographic system
    enhanced_prompt = build_enhanced_prompt(prompt, niche, visual_style)

    logger.info("Generating image", name=output_name, prompt_preview=prompt[:80])

    # Use modern client directly for single image generation
    client = AzureOpenAIClient()
    platform_enum = _platform_str_to_enum(platform)

    try:
        client.save_image(
            prompt=enhanced_prompt,
            output_path=Path(output_path),
            platform=platform_enum,
        )
        logger.info("Image saved", path=output_path)

        # Optionally save the prompt for reference
        if save_prompt:
            prompt_path = os.path.join(output_dir, f"{output_name}_prompt.txt")
            with open(prompt_path, "w", encoding="utf-8") as f:
                f.write(f"Original: {prompt}\n\nEnhanced: {enhanced_prompt}")

        return output_path

    except Exception as e:
        logger.error("Image generation failed", name=output_name, error=str(e))
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

    ⚠️ DEPRECATED: Use ImageService.generate_for_script() instead.

    Args:
        prompts: List of image descriptions
        niche: One of "scary-stories", "finance", "luxury", etc.
        base_name: Base filename (will be numbered)
        platform: "youtube" or "tiktok"
        visual_style: Optional story-level visual style for continuity
        max_workers: Maximum number of concurrent image generations (default: 5)

    Returns:
        List of paths to saved images (in same order as prompts)
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

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
            logger.warning("Skipping image", index=index, error=str(e))
            return (index, None)

    # Use ThreadPoolExecutor for concurrent generation
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(generate_single, i, prompt): i
            for i, prompt in enumerate(prompts, 1)
        }
        for future in as_completed(futures):
            index, path = future.result()
            paths[index - 1] = path

    return paths


def generate_from_script(
    script_path: str,
    niche: str,
    platform: str = "youtube",
) -> list:
    """
    Generate images based on a script JSON file.

    ⚠️ DEPRECATED: Use ImageService.generate_for_script() instead.

    Args:
        script_path: Path to the script JSON file
        niche: One of "scary-stories", "finance", "luxury", etc.
        platform: "youtube" or "tiktok"

    Returns:
        List of paths to generated images
    """
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    base_name = os.path.splitext(os.path.basename(script_path))[0]
    prompts = [scene["image_prompt"] for scene in script["scenes"]]
    visual_style = script.get("visual_style", None)

    logger.info("Generating images from script", base_name=base_name, count=len(prompts))
    if visual_style:
        logger.info("Using custom visual style for artistic continuity")

    return generate_batch(prompts, niche, base_name, platform, visual_style)


# =============================================================================
# STANDALONE USAGE
# =============================================================================

if __name__ == "__main__":
    import argparse
    from datetime import datetime

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

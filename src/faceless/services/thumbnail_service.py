"""
Thumbnail Service

Creates click-worthy thumbnails using AI image generation
Thumbnails are 80% of click-through rate - this is critical for views
"""

import base64
from pathlib import Path
from typing import Any

import httpx

from faceless.config import get_settings
from faceless.utils.logging import get_logger

logger = get_logger(__name__)

# =============================================================================
# THUMBNAIL TEMPLATES BY NICHE
# =============================================================================

THUMBNAIL_TEMPLATES: dict[str, dict[str, Any]] = {
    "scary-stories": {
        "style": "Dark, atmospheric horror with high contrast",
        "colors": "Deep blacks, blood reds, sickly greens, cold blues",
        "elements": [
            "Shadowy figure in background",
            "Frightened face in foreground",
            "Eerie lighting (backlit, rim light)",
            "Fog or mist effects",
            "Abandoned or liminal spaces",
        ],
        "text_style": "Bold red or white text with glow effect",
        "prompt_template": (
            "YouTube thumbnail for horror content, "
            "{subject}, "
            "dramatic lighting with deep shadows, "
            "unsettling atmosphere, "
            "cinematic composition, "
            "dark color palette with accent colors, "
            "high contrast, "
            "4K quality, professional photography"
        ),
    },
    "finance": {
        "style": "Clean, professional, aspirational",
        "colors": "Green (money), gold, white, navy blue",
        "elements": [
            "Money imagery (bills, coins, stacks)",
            "Upward trending graphs",
            "Shocked or excited expressions",
            "Before/after comparisons",
            "Numbers with dollar signs",
        ],
        "text_style": "Bold sans-serif, green or gold on dark",
        "prompt_template": (
            "YouTube thumbnail for finance content, "
            "{subject}, "
            "clean professional aesthetic, "
            "money and wealth imagery, "
            "green and gold color scheme, "
            "aspirational mood, "
            "high quality, sharp details"
        ),
    },
    "luxury": {
        "style": "Elegant, cinematic, aspirational",
        "colors": "Gold, black, white, champagne tones",
        "elements": [
            "Luxury items (watches, cars, yachts)",
            "Rich textures (leather, marble, velvet)",
            "Dramatic lighting",
            "Price tags or exclusive labels",
            "Celebrity or wealth imagery",
        ],
        "text_style": "Elegant serif or modern sans-serif, gold on black",
        "prompt_template": (
            "YouTube thumbnail for luxury content, "
            "{subject}, "
            "ultra-premium aesthetic, "
            "elegant composition, "
            "gold and black color scheme, "
            "cinematic lighting, "
            "high-end magazine quality"
        ),
    },
}

# Common thumbnail concepts that work across niches
THUMBNAIL_CONCEPTS: dict[str, str] = {
    "reaction": "Person with shocked/amazed expression looking at subject",
    "reveal": "Subject partially hidden, being unveiled or discovered",
    "versus": "Two items/concepts side by side for comparison",
    "before_after": "Dramatic transformation or change visualization",
    "countdown": "Number with dramatic emphasis (TOP 5, #1, etc.)",
    "mystery": "Obscured subject with question marks or intrigue",
    "warning": "Alert/danger symbolism with cautionary imagery",
    "secret": "Hidden or exclusive information being revealed",
}


def generate_thumbnail_prompt(
    title: str,
    niche: str,
    concept: str = "reveal",
    custom_subject: str | None = None,
) -> str:
    """
    Generate an optimized prompt for thumbnail creation.

    Args:
        title: Video title to base thumbnail on
        niche: Content niche
        concept: Thumbnail concept type
        custom_subject: Optional custom subject override

    Returns:
        Optimized prompt for image generation
    """
    template = THUMBNAIL_TEMPLATES.get(niche, THUMBNAIL_TEMPLATES["finance"])

    # Extract key subject from title or use custom
    if custom_subject:
        subject = custom_subject
    else:
        # Simple extraction - take meaningful words from title
        subject = title.replace("Why", "").replace("How", "")
        subject = subject.replace("The", "").strip()

    # Get concept description
    concept_desc = THUMBNAIL_CONCEPTS.get(concept, THUMBNAIL_CONCEPTS["reveal"])

    # Build the prompt
    prompt = template["prompt_template"].format(subject=subject)
    prompt += f", {concept_desc}"
    prompt += f", {template['style']}"

    # Add composition guidance for thumbnails
    prompt += (
        ", extreme close-up or medium shot, "
        "rule of thirds composition, "
        "space for text overlay on left or right third, "
        "16:9 aspect ratio optimized"
    )

    return prompt


def generate_thumbnail(
    prompt: str,
    niche: str,
    output_name: str,
    output_dir: Path | None = None,
    size: str = "1792x1024",
) -> Path:
    """
    Generate a thumbnail image using Azure OpenAI.

    Args:
        prompt: Image generation prompt
        niche: Content niche for output path
        output_name: Output filename (without extension)
        output_dir: Optional output directory
        size: Image size (default optimized for YouTube)

    Returns:
        Path to generated thumbnail
    """
    settings = get_settings()

    if output_dir is None:
        output_dir = settings.output.base_dir / niche / "images" / "thumbnails"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{output_name}.png"

    # Skip if already exists
    if output_path.exists():
        logger.info("Thumbnail already exists", path=str(output_path))
        return output_path

    url = (
        f"{settings.azure_openai.endpoint}openai/deployments/"
        f"{settings.azure_openai.image_deployment}/images/generations"
        f"?api-version={settings.azure_openai.image_api_version}"
    )

    headers = {
        "Content-Type": "application/json",
        "api-key": settings.azure_openai.api_key,
    }

    payload = {
        "prompt": prompt,
        "size": size,
        "quality": "high",
        "n": 1,
    }

    logger.info(
        "Generating thumbnail",
        name=output_name,
        prompt_preview=prompt[:80],
    )

    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()

        if "data" in result and len(result["data"]) > 0:
            image_data = result["data"][0]

            if "url" in image_data:
                with httpx.Client(timeout=60.0) as client:
                    img_response = client.get(image_data["url"])
                    img_bytes = img_response.content
            elif "b64_json" in image_data:
                img_bytes = base64.b64decode(image_data["b64_json"])
            else:
                raise ValueError("Unexpected response format")

            output_path.write_bytes(img_bytes)

            # Save prompt for reference
            prompt_path = output_path.with_suffix(".txt")
            prompt_path.write_text(prompt, encoding="utf-8")

            logger.info("Thumbnail saved", path=str(output_path))
            return output_path
        else:
            raise ValueError(f"No image data in response: {result}")

    except httpx.HTTPStatusError as e:
        logger.error("Thumbnail generation failed", error=str(e))
        raise


def generate_thumbnail_variants(
    title: str,
    niche: str,
    base_name: str,
    output_dir: Path | None = None,
    num_variants: int = 3,
    concepts: list[str] | None = None,
) -> list[Path | None]:
    """
    Generate multiple thumbnail variants for A/B testing.

    Args:
        title: Video title
        niche: Content niche
        base_name: Base filename for outputs
        output_dir: Optional output directory
        num_variants: Number of variants to generate
        concepts: List of concepts to use (defaults to auto-selection)

    Returns:
        List of paths to generated thumbnails
    """
    if concepts is None:
        # Default concept selection based on niche
        if niche == "scary-stories":
            concepts = ["mystery", "reveal", "warning"]
        elif niche == "finance":
            concepts = ["reaction", "before_after", "countdown"]
        else:
            concepts = ["reveal", "versus", "secret"]

    # Limit to requested number
    concepts = concepts[:num_variants]

    logger.info(
        "Generating thumbnail variants",
        count=len(concepts),
        title=title,
    )

    paths: list[Path | None] = []
    for i, concept in enumerate(concepts, 1):
        prompt = generate_thumbnail_prompt(title, niche, concept)
        output_name = f"{base_name}_thumb_v{i}_{concept}"

        try:
            path = generate_thumbnail(prompt, niche, output_name, output_dir)
            paths.append(path)
        except Exception as e:
            logger.warning("Failed to generate variant", variant=i, error=str(e))
            paths.append(None)

    return paths


def create_text_overlay_instructions(
    title: str,
    niche: str,
) -> dict[str, Any]:
    """
    Generate text overlay instructions for manual editing.

    Since we can't directly add text to AI images reliably,
    this provides instructions for adding text in an editor.

    Args:
        title: Video title
        niche: Content niche

    Returns:
        Dict with text overlay specifications
    """
    # Extract key words for thumbnail text (shorter than full title)
    words = title.split()
    thumb_text = " ".join(words[:5]) + "..." if len(words) > 5 else title

    # Generate color recommendations based on niche
    if niche == "scary-stories":
        text_color = "#FF0000"  # Red
        outline_color = "#000000"  # Black
        font_style = "Impact or Bebas Neue"
    elif niche == "finance":
        text_color = "#00FF00"  # Green
        outline_color = "#FFFFFF"  # White
        font_style = "Montserrat Bold or Arial Black"
    else:  # luxury
        text_color = "#FFD700"  # Gold
        outline_color = "#000000"  # Black
        font_style = "Playfair Display or Times New Roman Bold"

    return {
        "recommended_text": thumb_text,
        "text_color": text_color,
        "outline_color": outline_color,
        "font_style": font_style,
        "placement": "Left third or bottom third",
        "size": "Fill 30-40% of thumbnail width",
        "effects": "Drop shadow, 3-4px outline stroke",
        "tips": [
            "Use ALL CAPS for impact",
            "Maximum 4-5 words visible",
            "Contrast with background",
            "Don't cover face if person is in image",
        ],
    }

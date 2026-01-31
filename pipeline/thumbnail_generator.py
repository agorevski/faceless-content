"""
Thumbnail Generator Module
Creates click-worthy thumbnails using AI image generation
Thumbnails are 80% of click-through rate - this is critical for views
"""

import os
import sys
import json
import base64
import requests
from datetime import datetime
from typing import Optional, List, Dict

# Add pipeline directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_IMAGE_DEPLOYMENT,
    AZURE_OPENAI_IMAGE_API_VERSION,
    PATHS,
)

# =============================================================================
# THUMBNAIL TEMPLATES BY NICHE
# =============================================================================

THUMBNAIL_TEMPLATES = {
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
THUMBNAIL_CONCEPTS = {
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
    custom_subject: str = None,
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
    size: str = "1792x1024",
) -> str:
    """
    Generate a thumbnail image using Azure OpenAI.

    Args:
        prompt: Image generation prompt
        niche: Content niche for output path
        output_name: Output filename (without extension)
        size: Image size (default optimized for YouTube)

    Returns:
        Path to generated thumbnail
    """
    output_dir = os.path.join(PATHS[niche]["images"], "thumbnails")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{output_name}.png")

    # Skip if already exists
    if os.path.exists(output_path):
        print(f"🖼️ Thumbnail already exists: {output_path}")
        return output_path

    url = (
        f"{AZURE_OPENAI_ENDPOINT}openai/deployments/"
        f"{AZURE_OPENAI_IMAGE_DEPLOYMENT}/images/generations"
        f"?api-version={AZURE_OPENAI_IMAGE_API_VERSION}"
    )

    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_OPENAI_KEY,
    }

    payload = {
        "prompt": prompt,
        "size": size,
        "quality": "high",
        "n": 1,
    }

    print(f"🖼️ Generating thumbnail: {output_name}")
    print(f"   Prompt: {prompt[:80]}...")

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()

        if "data" in result and len(result["data"]) > 0:
            image_data = result["data"][0]

            if "url" in image_data:
                img_response = requests.get(image_data["url"], timeout=60)
                img_bytes = img_response.content
            elif "b64_json" in image_data:
                img_bytes = base64.b64decode(image_data["b64_json"])
            else:
                raise ValueError("Unexpected response format")

            with open(output_path, "wb") as f:
                f.write(img_bytes)

            # Save prompt for reference
            prompt_path = output_path.replace(".png", "_prompt.txt")
            with open(prompt_path, "w", encoding="utf-8") as f:
                f.write(prompt)

            print(f"   ✅ Saved: {output_path}")
            return output_path
        else:
            raise ValueError(f"No image data in response: {result}")

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
        raise


def generate_thumbnail_variants(
    title: str,
    niche: str,
    base_name: str,
    num_variants: int = 3,
    concepts: List[str] = None,
) -> List[str]:
    """
    Generate multiple thumbnail variants for A/B testing.

    Args:
        title: Video title
        niche: Content niche
        base_name: Base filename for outputs
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

    print(f"\n🎨 Generating {len(concepts)} thumbnail variants for: {title}")

    paths = []
    for i, concept in enumerate(concepts, 1):
        prompt = generate_thumbnail_prompt(title, niche, concept)
        output_name = f"{base_name}_thumb_v{i}_{concept}"

        try:
            path = generate_thumbnail(prompt, niche, output_name)
            paths.append(path)
        except Exception as e:
            print(f"   ⚠️ Failed variant {i}: {e}")
            paths.append(None)

    return paths


def generate_from_script(
    script_path: str,
    niche: str,
    num_variants: int = 2,
) -> List[str]:
    """
    Generate thumbnails based on a script file.

    Args:
        script_path: Path to script JSON
        niche: Content niche
        num_variants: Number of thumbnail variants

    Returns:
        List of thumbnail paths
    """
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    title = script.get("title", "Untitled")
    base_name = os.path.splitext(os.path.basename(script_path))[0]

    return generate_thumbnail_variants(title, niche, base_name, num_variants)


def create_text_overlay_instructions(
    title: str,
    niche: str,
) -> Dict:
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
    template = THUMBNAIL_TEMPLATES.get(niche, THUMBNAIL_TEMPLATES["finance"])

    # Extract key words for thumbnail text (shorter than full title)
    words = title.split()
    if len(words) > 5:
        # Keep most impactful words
        thumb_text = " ".join(words[:5]) + "..."
    else:
        thumb_text = title

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


# =============================================================================
# STANDALONE USAGE
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate thumbnails for faceless content"
    )
    parser.add_argument("title", help="Video title to generate thumbnail for")
    parser.add_argument(
        "--niche",
        "-n",
        choices=["scary-stories", "finance", "luxury"],
        required=True,
        help="Content niche",
    )
    parser.add_argument("--name", "-o", default=None, help="Output filename base")
    parser.add_argument(
        "--variants", "-v", type=int, default=2, help="Number of variants to generate"
    )
    parser.add_argument(
        "--concept",
        "-c",
        choices=list(THUMBNAIL_CONCEPTS.keys()),
        help="Specific concept to use",
    )

    args = parser.parse_args()

    if args.name:
        base_name = args.name
    else:
        safe_title = args.title.lower().replace(" ", "-")[:30]
        base_name = f"{safe_title}_{datetime.now().strftime('%Y%m%d')}"

    if args.concept:
        concepts = [args.concept]
        paths = generate_thumbnail_variants(
            args.title, args.niche, base_name, 1, concepts
        )
    else:
        paths = generate_thumbnail_variants(
            args.title, args.niche, base_name, args.variants
        )

    print(f"\n📊 Text Overlay Instructions:")
    instructions = create_text_overlay_instructions(args.title, args.niche)
    for key, value in instructions.items():
        print(f"   {key}: {value}")

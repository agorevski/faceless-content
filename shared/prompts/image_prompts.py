"""
Image Generation Prompt Templates and Settings.

This module contains per-niche image generation settings including:
- Image sizes for different platforms
- Visual style configurations
- Cinematographic prompt engineering templates
- Default visual continuity elements
"""

from typing import Any

# =============================================================================
# SCARY STORIES - Cinematic Horror Style
# =============================================================================

SCARY_STORIES_IMAGE_SETTINGS: dict[str, Any] = {
    "style": "dark cinematic horror",
    "color_palette": "dark blue, black, deep red, shadows",
    "quality": "high",
    "size": "1536x1024",  # Landscape for YouTube (closest to 16:9)
    "size_tiktok": "1024x1536",  # Portrait for TikTok (9:16)
    # Enhanced prompt engineering for high-quality horror imagery
    "prompt_template": {
        "prefix": "Cinematic still from a prestige A24-style horror film, shot on 35mm film with anamorphic lens.",
        "photography": "Shallow depth of field, masterful composition following rule of thirds, atmospheric perspective.",
        "lighting": "Diffused volumetric lighting, deep shadows with subtle rim lighting, god rays through fog or canopy.",
        "color_grading": "Desaturated color palette with deep teal shadows and muted amber/sepia highlights, film grain texture.",
        "mood": "Overwhelming sense of dread, liminal space aesthetic, uncanny valley atmosphere, isolated and oppressive.",
        "quality_suffix": "Photorealistic, 8K resolution, hyperdetailed, award-winning cinematography, Denis Villeneuve meets Ari Aster visual style.",
        "artistic_references": "Visual style inspired by Roger Deakins cinematography, Zdzisław Beksiński surrealist horror, and Simon Stålenhag's eerie atmosphere.",
    },
    # Default visual continuity elements (can be overridden in script JSON)
    "default_visual_style": {
        "environment": "Dense old-growth forest with towering ancient trees, thick atmospheric fog, perpetual twilight or overcast.",
        "color_mood": "Cold, desaturated blues and teals dominating shadows, with occasional warm amber highlights creating unease.",
        "texture": "Weathered wood, moss-covered surfaces, mist-dampened everything, organic decay meeting unnatural perfection.",
    },
}

# =============================================================================
# FINANCE - Clean Professional Modern Style
# =============================================================================

FINANCE_IMAGE_SETTINGS: dict[str, Any] = {
    "style": "clean professional modern",
    "color_palette": "green, gold, white, navy blue",
    "quality": "high",
    "size": "1536x1024",
    "size_tiktok": "1024x1536",
    # Prompt engineering for finance content
    "prompt_template": {
        "prefix": "Professional stock photography style, clean modern aesthetic.",
        "photography": "Sharp focus, even lighting, clean composition.",
        "lighting": "Bright, professional studio lighting or natural daylight.",
        "color_grading": "Clean, vibrant colors with professional color balance.",
        "mood": "Trustworthy, authoritative, aspirational yet accessible.",
        "quality_suffix": "High resolution, professional photography, corporate quality.",
        "artistic_references": "Bloomberg, Forbes, modern fintech marketing style.",
    },
    "default_visual_style": {
        "environment": "Modern office spaces, clean data visualizations, urban professional settings.",
        "color_mood": "Trust-inspiring greens, gold accents for wealth, clean whites and navy blues.",
        "texture": "Polished surfaces, modern materials, clean lines.",
    },
}

# =============================================================================
# LUXURY - Cinematic Elegance Style
# =============================================================================

LUXURY_IMAGE_SETTINGS: dict[str, Any] = {
    "style": "cinematic luxury elegant",
    "color_palette": "gold, black, white, champagne",
    "quality": "high",
    "size": "1536x1024",
    "size_tiktok": "1024x1536",
    # Prompt engineering for luxury content
    "prompt_template": {
        "prefix": "Ultra-luxury lifestyle photography, magazine-quality editorial style.",
        "photography": "Perfect composition, elegant framing, aspirational perspective.",
        "lighting": "Soft, flattering lighting with golden hour warmth, dramatic shadows.",
        "color_grading": "Rich, warm tones with gold and champagne highlights, deep blacks.",
        "mood": "Exclusive, sophisticated, aspirational, refined elegance.",
        "quality_suffix": "Ultra high resolution, magazine editorial quality, luxury brand aesthetic.",
        "artistic_references": "Vogue, Architectural Digest, luxury brand campaigns, yacht lifestyle.",
    },
    "default_visual_style": {
        "environment": "Exclusive venues, yacht interiors, private jets, luxury estates, five-star settings.",
        "color_mood": "Gold and champagne warmth, rich blacks, pristine whites, jewel tone accents.",
        "texture": "Fine leather, polished marble, crystal, silk, precious metals.",
    },
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_image_settings(niche: str) -> dict[str, Any]:
    """
    Get image settings for a specific niche.

    Args:
        niche: One of "scary-stories", "finance", "luxury"

    Returns:
        Dictionary containing image settings for the niche

    Raises:
        ValueError: If niche is not recognized
    """
    settings_map = {
        "scary-stories": SCARY_STORIES_IMAGE_SETTINGS,
        "finance": FINANCE_IMAGE_SETTINGS,
        "luxury": LUXURY_IMAGE_SETTINGS,
    }

    if niche not in settings_map:
        raise ValueError(
            f"Unknown niche: {niche}. Must be one of: {list(settings_map.keys())}"
        )

    return settings_map[niche]


def build_enhanced_prompt(
    base_prompt: str,
    niche: str,
    visual_style: dict[str, Any] | None = None,
) -> str:
    """
    Build a cinematically-enhanced prompt for high-quality image generation.

    Args:
        base_prompt: The original scene description
        niche: One of "scary-stories", "finance", "luxury"
        visual_style: Optional story-level visual style overrides from script

    Returns:
        Enhanced prompt string optimized for image generation
    """
    settings = get_image_settings(niche)

    # Check if this niche has enhanced prompt templates
    if "prompt_template" not in settings:
        # Fall back to legacy simple enhancement
        return (
            f"{base_prompt}. Style: {settings['style']}. "
            f"Color palette: {settings['color_palette']}. "
            f"High quality, detailed, professional."
        )

    template = settings["prompt_template"]
    default_style = settings.get("default_visual_style", {})

    # Merge default visual style with any script-specific overrides
    effective_style = {**default_style}
    if visual_style:
        effective_style.update(visual_style)

    # Build the enhanced prompt in a structured way
    prompt_parts = []

    # 1. Cinematic prefix
    prompt_parts.append(template.get("prefix", ""))

    # 2. Core scene description (the original prompt, enhanced)
    prompt_parts.append(base_prompt)

    # 3. Visual continuity elements from story style
    if effective_style:
        style_elements = []
        if "environment" in effective_style:
            style_elements.append(f"Setting: {effective_style['environment']}")
        if "recurring_elements" in effective_style:
            for element_name, element_desc in effective_style[
                "recurring_elements"
            ].items():
                style_elements.append(f"{element_name}: {element_desc}")
        if style_elements:
            prompt_parts.append(" | ".join(style_elements))

    # 4. Technical photography details
    prompt_parts.append(template.get("photography", ""))

    # 5. Lighting direction
    prompt_parts.append(template.get("lighting", ""))

    # 6. Color grading
    if "color_mood" in effective_style:
        prompt_parts.append(f"Color grading: {effective_style['color_mood']}")
    else:
        prompt_parts.append(template.get("color_grading", ""))

    # 7. Mood and atmosphere
    prompt_parts.append(template.get("mood", ""))

    # 8. Texture details
    if "texture" in effective_style:
        prompt_parts.append(f"Textures: {effective_style['texture']}")

    # 9. Quality and artistic reference suffix
    prompt_parts.append(template.get("quality_suffix", ""))
    prompt_parts.append(template.get("artistic_references", ""))

    # Filter out empty parts and join
    enhanced_prompt = " ".join(part for part in prompt_parts if part.strip())

    return enhanced_prompt

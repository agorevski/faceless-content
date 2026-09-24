"""
Thumbnail Service

Creates 16:9 thumbnail variants from AI imagery and title text.
"""

import hashlib
import re
import subprocess
import unicodedata
from pathlib import Path
from typing import Any
from uuid import uuid4

from faceless.clients.azure_openai import AzureOpenAIClient
from faceless.config import get_settings
from faceless.core.exceptions import (
    FacelessError,
    FFmpegError,
    ImageGenerationError,
    InputValidationError,
)
from faceless.utils.logging import get_logger

logger = get_logger(__name__)

# =============================================================================
# THUMBNAIL TEMPLATES BY NICHE
# =============================================================================

DEFAULT_THUMBNAIL_TEMPLATE: dict[str, Any] = {
    "style": "High-contrast editorial composition grounded in the provided subject",
    "colors": "Natural colors appropriate to the subject",
    "elements": ["Only objects and settings supported by the provided subject"],
    "text_style": "Bold white type over a dark panel with a neutral accent",
    "prompt_template": (
        "YouTube thumbnail about {subject}, "
        "depict the supplied subject faithfully without implying extra claims, "
        "use an abstract background if the subject has no literal depiction, "
        "natural topic-appropriate colors, cinematic lighting, "
        "clear focal point, polished professional visual quality"
    ),
}

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
            "visual metaphor relevant to the subject, "
            "green and gold color scheme, "
            "confident mood, "
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
    "reaction": "Dramatic visual reaction through lighting and composition, no face needed",
    "reveal": "Subject partially hidden, being unveiled or discovered",
    "versus": "Two relevant subjects side by side only if the title compares them",
    "before_after": "Contrasting visual states only if the title describes a change",
    "countdown": "Bold visual focal point, without inventing a ranking or number",
    "mystery": "Obscured subject with question marks or intrigue",
    "warning": "Alert/danger symbolism with cautionary imagery",
    "secret": "Hidden or exclusive information being revealed",
}

THUMBNAIL_ACCENTS: dict[str, str] = {
    "scary-stories": "E64545",
    "finance": "53D88C",
    "luxury": "E8BD67",
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
    template = THUMBNAIL_TEMPLATES.get(niche, DEFAULT_THUMBNAIL_TEMPLATE)

    subject = custom_subject or title.strip()

    # Get concept description
    concept_desc = THUMBNAIL_CONCEPTS.get(concept, THUMBNAIL_CONCEPTS["reveal"])

    # Build the prompt
    prompt_template: str = str(template["prompt_template"])
    prompt = prompt_template.format(subject=subject)
    prompt += f", {concept_desc}"
    prompt += f", {template['style']}"

    # Add composition guidance for thumbnails
    prompt += (
        ", extreme close-up or medium shot, "
        "rule of thirds composition, visual focal point on the right half, "
        "left half dark and uncluttered for a text overlay, "
        "no words, letters or numbers in the image, no face required, "
        "do not depict facts or results not supported by the title, "
        "16:9 aspect ratio optimized"
    )

    return prompt


def generate_thumbnail(
    prompt: str,
    niche: str,
    output_name: str,
    output_dir: Path | None = None,
    size: str = "1536x1024",
    client: AzureOpenAIClient | None = None,
) -> Path:
    """
    Generate a thumbnail image using Azure OpenAI.

    Args:
        prompt: Image generation prompt
        niche: Content niche for output path
        output_name: Output filename (without extension)
        output_dir: Optional output directory
        size: Azure gpt-image-1 landscape size (default 1536x1024)
        client: Optional shared Azure client; owned by the caller

    Returns:
        Path to generated thumbnail
    """
    if output_dir is None:
        settings = get_settings()
        output_dir = settings.output_base_dir / niche / "images" / "thumbnails"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{output_name}.png"

    if output_path.is_file() and output_path.stat().st_size > 0:
        logger.info("Thumbnail already exists", path=str(output_path))
        return output_path

    logger.info(
        "Generating thumbnail",
        name=output_name,
        prompt_preview=prompt[:80],
    )

    if client is None:
        owned_client = AzureOpenAIClient()
        with owned_client:
            image_bytes = owned_client.generate_image(prompt, size=size)
    else:
        image_bytes = client.generate_image(prompt, size=size)
    if not image_bytes:
        raise ImageGenerationError("Thumbnail response contained no image bytes")

    output_path.write_bytes(image_bytes)
    output_path.with_suffix(".txt").write_text(prompt, encoding="utf-8")
    logger.info("Thumbnail saved", path=str(output_path))
    return output_path


def _thumbnail_copy(title: str) -> list[str]:
    """Select title words only, then wrap them for the thumbnail's text area."""
    words = title.split()
    if not words:
        raise InputValidationError("Thumbnail title must not be empty", field="title")

    copy: list[str] = []
    for word in words[:5]:
        if _text_width(word) <= 8.0:
            copy.append(word)
            continue
        shortened = ""
        for char in word:
            if _text_width(shortened + char + "…") > 8.0:
                break
            shortened += char
        copy.append(shortened + "…")

    lines: list[str] = []
    line = ""
    for word in copy:
        candidate = f"{line} {word}".strip()
        if line and _text_width(candidate) > 6.0:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines


def _text_width(text: str) -> float:
    """Conservative glyph-width estimate in font-size units for bold sans-serif."""
    width = 0.0
    for char in text:
        if char.isspace():
            width += 0.35
        elif unicodedata.east_asian_width(char) in {"W", "F"}:
            width += 1.0
        elif char in "MW@#%":
            width += 0.95
        elif char in "ilI.,!|:;'`":
            width += 0.36
        elif char.isupper():
            width += 0.75
        else:
            width += 0.65
    return width


def _safe_filename_component(value: str) -> str:
    """Keep user-supplied names within the output directory."""
    return (
        re.sub(r"[^\w-]+", "_", value, flags=re.UNICODE).strip("_")[:80] or "thumbnail"
    )


def _compose_thumbnail(source: Path, output: Path, title: str, niche: str) -> Path:
    """Render an actual 1280x720 PNG with an image, dark text panel and title."""
    lines = _thumbnail_copy(title)
    # Keep long words and multi-line copy inside the 500px-wide, 540px-tall safe area.
    font_size = min(78, int(490 / max(_text_width(line) for line in lines)))
    font_size = min(font_size, int(480 / (1.3 * len(lines))))
    accent = THUMBNAIL_ACCENTS.get(niche, "72CAE3")
    output.parent.mkdir(parents=True, exist_ok=True)
    token = uuid4().hex
    caption = output.parent / f".thumbnail-caption-{token}.txt"
    rendered = output.parent / f".thumbnail-render-{token}.png"
    filters = (
        "scale=1280:720:force_original_aspect_ratio=increase:flags=lanczos,"
        "crop=1280:720,setsar=1,"
        "drawbox=x=0:y=0:w=655:h=720:color=black@0.78:t=fill,"
        f"drawbox=x=64:y=192:w=9:h=336:color=0x{accent}:t=fill,"
        f"drawbox=x=96:y=174:w=84:h=7:color=0x{accent}:t=fill,"
        f"drawtext=font=DejaVu Sans:fontcolor=white:fontsize={font_size}:"
        f"textfile={caption.name}:expansion=none:line_spacing=12:"
        "borderw=2:bordercolor=black@0.9:shadowx=3:shadowy=3:"
        "shadowcolor=black@0.8:x=96:y=(h-text_h)/2"
    )
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source.resolve()),
        "-vf",
        filters,
        "-frames:v",
        "1",
        "-update",
        "1",
        "-c:v",
        "png",
        "-pix_fmt",
        "rgb24",
        str(rendered.resolve()),
    ]
    try:
        caption.write_text("\n".join(lines), encoding="utf-8")
        subprocess.run(
            command,
            cwd=output.parent.resolve(),
            capture_output=True,
            text=True,
            check=True,
            timeout=120,
        )
        if not rendered.is_file() or rendered.stat().st_size < 24:
            raise FFmpegError("FFmpeg did not produce a thumbnail", command=command)
        with rendered.open("rb") as image:
            header = image.read(24)
        if header[:16] != b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" or (
            int.from_bytes(header[16:20], "big"),
            int.from_bytes(header[20:24], "big"),
        ) != (1280, 720):
            raise FFmpegError(
                "FFmpeg produced an invalid thumbnail PNG", command=command
            )
        rendered.replace(output)
        return output
    except subprocess.CalledProcessError as exc:
        raise FFmpegError(
            "Thumbnail composition failed",
            command=command,
            return_code=exc.returncode,
            stderr=exc.stderr,
        ) from exc
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise FFmpegError(
            "FFmpeg is required to compose thumbnails",
            command=command,
            stderr=str(exc),
        ) from exc
    except OSError as exc:
        raise FFmpegError(
            "Could not write the composed thumbnail",
            command=command,
            stderr=str(exc),
        ) from exc
    finally:
        caption.unlink(missing_ok=True)
        rendered.unlink(missing_ok=True)


def generate_thumbnail_variants(
    title: str,
    niche: str,
    base_name: str,
    output_dir: Path | None = None,
    num_variants: int = 3,
    concepts: list[str] | None = None,
    client: AzureOpenAIClient | None = None,
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
        client: Optional shared Azure client; owned by the caller

    Returns:
        Paths to composed 1280x720 PNG thumbnails, or None for failed images.

    Raises:
        InputValidationError: If no variants can be generated.
        FFmpegError: If composition fails for any variant.
    """
    if num_variants <= 0:
        raise InputValidationError(
            "num_variants must be greater than zero",
            field="num_variants",
            value=num_variants,
        )

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
    if not concepts:
        raise InputValidationError(
            "At least one thumbnail concept is required", field="concepts"
        )

    logger.info(
        "Generating thumbnail variants",
        count=len(concepts),
        title=title,
    )

    paths: list[Path | None] = []
    for i, concept in enumerate(concepts, 1):
        prompt = generate_thumbnail_prompt(title, niche, concept)
        output_name = (
            f"{_safe_filename_component(base_name)}_thumb_v{i}_"
            f"{_safe_filename_component(concept)}"
        )
        source_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]

        try:
            source = generate_thumbnail(
                prompt,
                niche,
                f"{output_name}_source_{source_hash}",
                output_dir,
                client=client,
            )
            if source is None:
                raise ImageGenerationError("Image generation returned no thumbnail")
        except (FacelessError, OSError, ValueError) as exc:
            logger.warning(
                "Failed to generate thumbnail image",
                variant=i,
                concept=concept,
                niche=niche,
                error=str(exc),
            )
            paths.append(None)
            continue

        path = _compose_thumbnail(
            source, source.with_name(f"{output_name}.png"), title, niche
        )
        paths.append(path)
        logger.info(
            "Thumbnail variant composed", variant=i, concept=concept, path=str(path)
        )

    return paths


def create_text_overlay_instructions(
    title: str,
    niche: str,
) -> dict[str, Any]:
    """
    Generate text overlay instructions for manual editing.

    Optional guidance for manually adjusting the automatically composed overlay.

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

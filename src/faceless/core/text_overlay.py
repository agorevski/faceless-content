"""
Text Overlay Module



Generates text overlay configurations for hooks, CTAs, and engagement elements
and renders them through FFmpeg drawtext filters.
"""

import re
import textwrap
from dataclasses import dataclass, field
from enum import Enum

from faceless.utils.logging import get_logger

logger = get_logger(__name__)


class TextPosition(Enum):
    """Text overlay position presets."""

    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"


class TextAnimation(Enum):
    """Text animation types."""

    NONE = "none"
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    FADE_IN_OUT = "fade_in_out"
    TYPEWRITER = "typewriter"
    SCALE_IN = "scale_in"
    SLIDE_UP = "slide_up"
    SLIDE_DOWN = "slide_down"


@dataclass
class TextStyle:
    """Text styling configuration."""

    font_size: int = 48
    font_color: str = "white"
    font_family: str = "Arial"
    bold: bool = True
    italic: bool = False
    outline_color: str = "black"
    outline_width: int = 3
    shadow: bool = True
    shadow_color: str = "black"
    shadow_offset: tuple = (2, 2)
    background_color: str | None = None
    background_padding: int = 10


@dataclass
class TextOverlay:
    """Represents a text overlay to be rendered on video."""

    text: str
    position: TextPosition = TextPosition.CENTER
    start_time: float = 0.0
    end_time: float = 3.0
    style: TextStyle = field(default_factory=TextStyle)
    animation: TextAnimation = TextAnimation.FADE_IN_OUT
    layer: int = 1  # For z-ordering multiple overlays
    x: str | None = None
    y: str | None = None


# =============================================================================
# PRESET STYLES
# =============================================================================

PRESET_STYLES = {
    "hook_primary": TextStyle(
        font_size=64,
        font_color="white",
        bold=True,
        outline_color="black",
        outline_width=4,
        shadow=True,
    ),
    "hook_secondary": TextStyle(
        font_size=48,
        font_color="#FFD700",  # Gold
        bold=True,
        outline_color="black",
        outline_width=3,
    ),
    "cta": TextStyle(
        font_size=42,
        font_color="white",
        bold=True,
        outline_color="#FF0000",  # Red outline
        outline_width=3,
        background_color="rgba(0,0,0,0.7)",
        background_padding=15,
    ),
    "countdown": TextStyle(
        font_size=72,
        font_color="#FF4444",
        bold=True,
        outline_color="white",
        outline_width=4,
    ),
    "subtle": TextStyle(
        font_size=36,
        font_color="rgba(255,255,255,0.9)",
        bold=False,
        outline_color="black",
        outline_width=2,
    ),
    "scary": TextStyle(
        font_size=56,
        font_color="#CC0000",
        bold=True,
        outline_color="black",
        outline_width=4,
        shadow=True,
        shadow_color="#330000",
    ),
    "finance": TextStyle(
        font_size=52,
        font_color="#00CC00",  # Money green
        bold=True,
        outline_color="black",
        outline_width=3,
    ),
    "luxury": TextStyle(
        font_size=52,
        font_color="#FFD700",  # Gold
        bold=True,
        outline_color="#1a1a1a",
        outline_width=3,
    ),
}


# =============================================================================
# OVERLAY GENERATION FUNCTIONS
# =============================================================================


def create_hook_overlay(
    text: str,
    niche: str = "scary-stories",
    duration: float = 3.0,
    position: TextPosition = TextPosition.CENTER,
) -> TextOverlay:
    """
    Create a first-frame hook text overlay.

    Args:
        text: Hook text to display
        niche: Content niche for styling
        duration: How long to display (seconds)
        position: Where to place the text

    Returns:
        TextOverlay configured for hook display
    """
    style_map = {
        "scary-stories": PRESET_STYLES["scary"],
        "finance": PRESET_STYLES["finance"],
        "luxury": PRESET_STYLES["luxury"],
    }

    style = style_map.get(niche, PRESET_STYLES["hook_primary"])

    return TextOverlay(
        text=text,
        position=position,
        start_time=0.0,
        end_time=duration,
        style=style,
        animation=TextAnimation.FADE_IN_OUT,
    )


def create_opening_hook_overlays(
    narration: str,
    duration: float,
    video_width: int,
    video_height: int,
) -> list[TextOverlay]:
    """Lay out the first spoken words above the caption area.

    The first line is larger than the remaining lines. For portrait videos the
    text also stays left of the platform's right-hand interaction controls.
    """
    opening_words: list[str] = []
    for word in narration.split()[:10]:
        if opening_words and len(" ".join(opening_words)) + len(word) + 1 > 80:
            break
        opening_words.append(word[:80] if not opening_words else word)
        if re.search(r"[!?][\"')\]]?$", word) or (
            len(opening_words) >= 3 and re.search(r"\.[\"')\]]?$", word)
        ):
            break
    opening = " ".join(opening_words)
    if not opening or duration <= 0:
        return []

    portrait = video_height > video_width
    left_margin = round(video_width * (0.15 if portrait else 0.10))
    right_margin = round(video_width * (0.20 if portrait else 0.10))
    safe_width = video_width - left_margin - right_margin
    first_width, rest_width = (12, 17) if portrait else (24, 30)
    lines = textwrap.wrap(
        opening,
        width=first_width,
        break_long_words=True,
        break_on_hyphens=False,
    )
    if len(lines) > 1:
        lines = [lines[0]] + textwrap.wrap(
            opening[len(lines[0]) :].strip(),
            width=rest_width,
            break_long_words=True,
            break_on_hyphens=False,
        )

    primary_size, secondary_size = (60, 46) if portrait else (80, 58)
    line_step = round(primary_size * 1.45)
    top = round(video_height * (0.16 if portrait else 0.12))
    x = f"({safe_width}-text_w)/2+{left_margin}"
    return [
        TextOverlay(
            text=line,
            position=TextPosition.TOP_CENTER,
            start_time=0.0,
            end_time=min(3.0, duration),
            style=TextStyle(
                font_size=min(
                    primary_size if index == 0 else secondary_size,
                    max(24, (safe_width - 32) // len(line)),
                ),
                font_color="white" if index == 0 else "#FFE6A0",
                outline_width=3,
                shadow=True,
                background_color="black@0.7",
                background_padding=12,
            ),
            animation=TextAnimation.NONE,
            layer=index,
            x=x,
            y=str(top + index * line_step),
        )
        for index, line in enumerate(lines)
    ]


def create_mid_video_overlay(
    text: str,
    insert_at_seconds: float,
    duration: float = 2.0,
) -> TextOverlay:
    """
    Create a mid-video retention text overlay.

    Args:
        text: Text to display (e.g., "WAIT FOR IT")
        insert_at_seconds: When to start showing
        duration: How long to display

    Returns:
        TextOverlay for mid-video retention
    """
    return TextOverlay(
        text=text,
        position=TextPosition.CENTER,
        start_time=insert_at_seconds,
        end_time=insert_at_seconds + duration,
        style=PRESET_STYLES["hook_secondary"],
        animation=TextAnimation.SCALE_IN,
    )


def create_cta_overlay(
    text: str,
    video_duration: float,
    display_duration: float = 4.0,
) -> TextOverlay:
    """
    Create an end-of-video CTA overlay.

    Args:
        text: CTA text (e.g., "Follow for Part 2!")
        video_duration: Total video length in seconds
        display_duration: How long to show CTA

    Returns:
        TextOverlay for CTA display
    """
    start_time = max(0, video_duration - display_duration)

    return TextOverlay(
        text=text,
        position=TextPosition.BOTTOM_CENTER,
        start_time=start_time,
        end_time=video_duration,
        style=PRESET_STYLES["cta"],
        animation=TextAnimation.SLIDE_UP,
    )


def create_countdown_overlays(
    start_at_seconds: float,
    count_from: int = 3,
) -> list:
    """
    Create countdown text overlays (3... 2... 1...).

    Args:
        start_at_seconds: When to start countdown
        count_from: Number to count from

    Returns:
        List of TextOverlay objects for countdown
    """
    overlays = []

    for i in range(count_from, 0, -1):
        overlays.append(
            TextOverlay(
                text=str(i),
                position=TextPosition.CENTER,
                start_time=start_at_seconds + (count_from - i),
                end_time=start_at_seconds + (count_from - i) + 0.9,
                style=PRESET_STYLES["countdown"],
                animation=TextAnimation.SCALE_IN,
            )
        )

    return overlays


def create_pov_overlay(
    situation: str,
    duration: float = 3.0,
) -> TextOverlay:
    """
    Create a POV-style hook overlay.

    Args:
        situation: The POV situation (e.g., "You hear a noise downstairs")
        duration: How long to display

    Returns:
        TextOverlay with POV formatting
    """
    text = f"POV: {situation}"

    return TextOverlay(
        text=text,
        position=TextPosition.TOP_CENTER,
        start_time=0.0,
        end_time=duration,
        style=TextStyle(
            font_size=44,
            font_color="white",
            bold=True,
            outline_color="black",
            outline_width=3,
            background_color="rgba(0,0,0,0.5)",
            background_padding=12,
        ),
        animation=TextAnimation.FADE_IN,
    )


# =============================================================================
# FFMPEG FILTER GENERATION
# =============================================================================


def _escape_drawtext_text(text: str) -> str:
    """Escape the drawtext option parser, then the outer filtergraph parser."""
    option_escaped = "".join(f"\\{ch}" if ch in "\\:'" else ch for ch in text)
    return "".join(f"\\{ch}" if ch in "\\,;[]'" else ch for ch in option_escaped)


def position_to_xy(
    position: TextPosition, video_width: int = 1080, video_height: int = 1920
) -> tuple:
    """
    Convert position enum to x, y coordinates for FFmpeg.

    Args:
        position: TextPosition enum value
        video_width: Video width in pixels
        video_height: Video height in pixels

    Returns:
        Tuple of (x_expr, y_expr) for FFmpeg drawtext filter
    """
    positions = {
        TextPosition.TOP_LEFT: ("10", "10"),
        TextPosition.TOP_CENTER: ("(w-text_w)/2", "50"),
        TextPosition.TOP_RIGHT: ("w-text_w-10", "10"),
        TextPosition.CENTER_LEFT: ("10", "(h-text_h)/2"),
        TextPosition.CENTER: ("(w-text_w)/2", "(h-text_h)/2"),
        TextPosition.CENTER_RIGHT: ("w-text_w-10", "(h-text_h)/2"),
        TextPosition.BOTTOM_LEFT: ("10", "h-text_h-100"),
        TextPosition.BOTTOM_CENTER: ("(w-text_w)/2", "h-text_h-100"),
        TextPosition.BOTTOM_RIGHT: ("w-text_w-10", "h-text_h-100"),
    }

    return positions.get(position, ("(w-text_w)/2", "(h-text_h)/2"))


def overlay_to_ffmpeg_filter(
    overlay: TextOverlay, video_width: int = 1080, video_height: int = 1920
) -> str:
    """
    Convert a TextOverlay to FFmpeg drawtext filter string.

    Args:
        overlay: TextOverlay object
        video_width: Video width
        video_height: Video height

    Returns:
        FFmpeg filter string for drawtext
    """
    default_x, default_y = position_to_xy(overlay.position, video_width, video_height)
    x_expr = overlay.x if overlay.x is not None else default_x
    y_expr = overlay.y if overlay.y is not None else default_y

    # Build filter components
    filter_parts = [
        f"drawtext=text={_escape_drawtext_text(overlay.text)}",
        "expansion=none",
        f"fontsize={overlay.style.font_size}",
        f"fontcolor={overlay.style.font_color}",
        f"x={x_expr}",
        f"y={y_expr}",
        "fix_bounds=1",
    ]

    if overlay.style.background_color:
        filter_parts.extend(
            (
                "box=1",
                f"boxcolor={overlay.style.background_color}",
                f"boxborderw={overlay.style.background_padding}",
            )
        )

    # Add outline/border
    if overlay.style.outline_width > 0:
        filter_parts.append(f"borderw={overlay.style.outline_width}")
        filter_parts.append(f"bordercolor={overlay.style.outline_color}")

    # Add shadow
    if overlay.style.shadow:
        filter_parts.append(f"shadowcolor={overlay.style.shadow_color}")
        filter_parts.append(f"shadowx={overlay.style.shadow_offset[0]}")
        filter_parts.append(f"shadowy={overlay.style.shadow_offset[1]}")

    # Add timing
    filter_parts.append(f"enable='between(t,{overlay.start_time},{overlay.end_time})'")

    # Note: Fade animations would require complex filter graphs with alpha channels
    # This is a placeholder for future implementation
    _ = overlay.animation  # Acknowledge animation parameter for future use

    return ":".join(filter_parts)


def generate_overlay_filter_chain(
    overlays: list, video_width: int = 1080, video_height: int = 1920
) -> str:
    """
    Generate a complete FFmpeg filter chain for multiple overlays.

    Args:
        overlays: List of TextOverlay objects
        video_width: Video width
        video_height: Video height

    Returns:
        Complete FFmpeg filter string
    """
    if not overlays:
        return ""

    # Sort by layer for proper z-ordering
    sorted_overlays = sorted(overlays, key=lambda o: o.layer)

    filters = [
        overlay_to_ffmpeg_filter(o, video_width, video_height) for o in sorted_overlays
    ]

    return ",".join(filters)


# =============================================================================
# STANDALONE USAGE
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate text overlays for video content"
    )
    parser.add_argument(
        "--type",
        "-t",
        choices=["hook", "mid", "cta", "pov", "countdown"],
        default="hook",
        help="Type of overlay to create",
    )
    parser.add_argument(
        "--text",
        default="Would you enter this door?",
        help="Text to display",
    )
    parser.add_argument(
        "--niche",
        "-n",
        choices=["scary-stories", "finance", "luxury"],
        default="scary-stories",
    )
    parser.add_argument(
        "--ffmpeg",
        "-f",
        action="store_true",
        help="Output FFmpeg filter string",
    )

    args = parser.parse_args()

    if args.type == "hook":
        overlay = create_hook_overlay(args.text, args.niche)
    elif args.type == "mid":
        overlay = create_mid_video_overlay(args.text, 15.0)
    elif args.type == "cta":
        overlay = create_cta_overlay(args.text, 60.0)
    elif args.type == "pov":
        overlay = create_pov_overlay(args.text)
    elif args.type == "countdown":
        overlays = create_countdown_overlays(10.0)
        for o in overlays:
            logger.info(
                "Countdown overlay",
                text=o.text,
                start_time=o.start_time,
                end_time=o.end_time,
            )
        exit()

    if args.ffmpeg:
        logger.info("FFmpeg filter", filter=overlay_to_ffmpeg_filter(overlay))
    else:
        logger.info(
            "Overlay created",
            text=overlay.text,
            position=overlay.position.value,
            start_time=overlay.start_time,
            end_time=overlay.end_time,
            animation=overlay.animation.value,
        )

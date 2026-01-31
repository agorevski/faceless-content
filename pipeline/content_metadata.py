"""
Content Metadata Module
Generates complete posting metadata for videos including captions,
hashtags, posting times, and engagement recommendations
"""

import json
import os
from datetime import datetime

from hashtags import (
    generate_hashtag_set,
    get_format_specific_hashtags,
)
from hooks import generate_engagement_package
from posting_schedule import get_next_optimal_slot
from tiktok_formats import format_to_prompt_guidance, get_format

# =============================================================================
# METADATA STRUCTURE
# =============================================================================


def generate_content_metadata(
    niche: str,
    title: str,
    video_duration: float,
    format_name: str = None,
    series_name: str = None,
    part_number: int = None,
    custom_caption: str = None,
) -> dict:
    """
    Generate complete posting metadata for a video.

    Args:
        niche: One of "scary-stories", "finance", "luxury"
        title: Video title
        video_duration: Duration in seconds
        format_name: Optional TikTok format name
        series_name: Optional series name for recurring content
        part_number: Optional part number in series
        custom_caption: Optional custom caption override

    Returns:
        Dict with all posting metadata
    """
    # Get engagement elements
    engagement = generate_engagement_package(niche)

    # Generate hashtags
    series_tag = f"#{series_name.replace(' ', '')}" if series_name else None
    hashtags = generate_hashtag_set(niche, series_tag=series_tag)

    # Add format-specific hashtags if applicable
    if format_name:
        format_hashtags = get_format_specific_hashtags(niche, format_name)
        # Insert format hashtags before the last (series) tag
        if format_hashtags:
            hashtags = hashtags[:-1] + format_hashtags[:2] + hashtags[-1:]

    # Get optimal posting time
    posting_slot = get_next_optimal_slot(niche)

    # Build caption
    if custom_caption:
        caption = custom_caption
    else:
        caption = _build_caption(
            title=title,
            hook=engagement["first_frame_hook"]["text"],
            comment_trigger=engagement["comment_trigger"]["content"],
            series_name=series_name,
            part_number=part_number,
        )

    # Build metadata
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "niche": niche,
        "title": title,
        "video_duration_seconds": video_duration,
        # Caption and hashtags
        "caption": caption,
        "hashtags": hashtags,
        "hashtag_string": " ".join(hashtags),
        "full_post_text": f"{caption}\n\n{' '.join(hashtags)}",
        # Engagement elements
        "first_frame_hook": engagement["first_frame_hook"],
        "mid_video_hook": engagement["mid_video_hook"],
        "comment_trigger": engagement["comment_trigger"],
        "pinned_comment_suggestion": engagement["pinned_comment"],
        "loop_structure": engagement["loop_structure"],
        # Posting schedule
        "optimal_posting": {
            "datetime": posting_slot["datetime"].isoformat(),
            "formatted": posting_slot["formatted"],
            "day_rating": posting_slot["day_rating"]["performance"],
            "window_priority": posting_slot["window_priority"],
        },
        # Series info
        "series": {
            "name": series_name,
            "part_number": part_number,
            "series_hashtag": series_tag,
        }
        if series_name
        else None,
        # Format info
        "format": {
            "name": format_name,
            "guidance": format_to_prompt_guidance(get_format(niche, format_name))
            if format_name and get_format(niche, format_name)
            else None,
        }
        if format_name
        else None,
        # Analytics targets
        "target_metrics": {
            "first_3_sec_retention": "70%+",
            "mid_video_retention": "50%+",
            "full_watch_rate": "40%+",
            "replay_rate": "1.2x+",
            "comment_rate": "1%+",
        },
    }

    return metadata


def _build_caption(
    title: str,
    hook: str,
    comment_trigger: str,
    series_name: str = None,
    part_number: int = None,
) -> str:
    """
    Build an engaging caption for the video.

    Args:
        title: Video title
        hook: First-frame hook text
        comment_trigger: Comment engagement text
        series_name: Optional series name
        part_number: Optional part number

    Returns:
        Formatted caption string
    """
    parts = []

    # Add series prefix if applicable
    if series_name and part_number:
        parts.append(f"📺 {series_name} - Part {part_number}")

    # Add hook or title
    if hook and len(hook) < 100:
        parts.append(hook)
    else:
        parts.append(title)

    # Add comment trigger
    parts.append("")
    parts.append(comment_trigger)

    return "\n".join(parts)


def save_metadata(
    metadata: dict,
    output_path: str,
) -> str:
    """
    Save metadata to JSON file.

    Args:
        metadata: Metadata dict
        output_path: Path to save JSON

    Returns:
        Path to saved file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)

    return output_path


def load_metadata(metadata_path: str) -> dict:
    """
    Load metadata from JSON file.

    Args:
        metadata_path: Path to metadata JSON

    Returns:
        Metadata dict
    """
    with open(metadata_path, encoding="utf-8") as f:
        return json.load(f)


# =============================================================================
# BATCH METADATA GENERATION
# =============================================================================


def generate_series_metadata(
    niche: str,
    series_name: str,
    titles: list,
    video_durations: list = None,
    format_name: str = None,
) -> list:
    """
    Generate metadata for a series of videos.

    Args:
        niche: Content niche
        series_name: Series name
        titles: List of video titles
        video_durations: Optional list of durations (defaults to 60s each)
        format_name: Optional format name

    Returns:
        List of metadata dicts
    """
    if video_durations is None:
        video_durations = [60.0] * len(titles)

    metadata_list = []

    for i, (title, duration) in enumerate(
        zip(titles, video_durations, strict=False), 1
    ):
        metadata = generate_content_metadata(
            niche=niche,
            title=title,
            video_duration=duration,
            format_name=format_name,
            series_name=series_name,
            part_number=i,
        )
        metadata_list.append(metadata)

    return metadata_list


# =============================================================================
# DISPLAY UTILITIES
# =============================================================================


def format_metadata_for_display(metadata: dict) -> str:
    """
    Format metadata for human-readable display.

    Args:
        metadata: Metadata dict

    Returns:
        Formatted string
    """
    lines = [
        "=" * 60,
        "📱 TIKTOK POSTING METADATA",
        "=" * 60,
        "",
        f"📌 Title: {metadata['title']}",
        f"⏱️ Duration: {metadata['video_duration_seconds']}s",
        f"🎯 Niche: {metadata['niche']}",
        "",
        "📝 CAPTION:",
        "-" * 40,
        metadata["caption"],
        "",
        "🏷️ HASHTAGS:",
        "-" * 40,
        metadata["hashtag_string"],
        "",
        "🪝 FIRST FRAME HOOK:",
        "-" * 40,
        f"  \"{metadata['first_frame_hook']['text']}\"",
        f"  Type: {metadata['first_frame_hook']['type']}",
        "",
        "💬 PINNED COMMENT:",
        "-" * 40,
        f"  \"{metadata['pinned_comment_suggestion']}\"",
        "",
        "⏰ OPTIMAL POSTING:",
        "-" * 40,
        f"  {metadata['optimal_posting']['formatted']}",
        f"  Priority: {metadata['optimal_posting']['window_priority']}",
        "",
        "🔄 LOOP STRUCTURE:",
        "-" * 40,
        f"  Type: {metadata['loop_structure']['type']}",
        f"  {metadata['loop_structure']['description']}",
        "",
        "=" * 60,
    ]

    return "\n".join(lines)


# =============================================================================
# STANDALONE USAGE
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate content metadata for TikTok videos"
    )
    parser.add_argument(
        "--niche",
        "-n",
        choices=["scary-stories", "finance", "luxury"],
        default="scary-stories",
        help="Content niche",
    )
    parser.add_argument(
        "--title",
        "-t",
        default="The House at the End of the Street",
        help="Video title",
    )
    parser.add_argument(
        "--duration",
        "-d",
        type=float,
        default=60.0,
        help="Video duration in seconds",
    )
    parser.add_argument(
        "--series",
        "-s",
        help="Series name",
    )
    parser.add_argument(
        "--part",
        "-p",
        type=int,
        help="Part number in series",
    )
    parser.add_argument(
        "--format",
        "-f",
        help="TikTok format name",
    )
    parser.add_argument(
        "--json",
        "-j",
        action="store_true",
        help="Output as JSON instead of formatted",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Save to file",
    )

    args = parser.parse_args()

    metadata = generate_content_metadata(
        niche=args.niche,
        title=args.title,
        video_duration=args.duration,
        format_name=args.format,
        series_name=args.series,
        part_number=args.part,
    )

    if args.output:
        save_metadata(metadata, args.output)
        print(f"Saved to: {args.output}")
    elif args.json:
        print(json.dumps(metadata, indent=2, default=str))
    else:
        print(format_metadata_for_display(metadata))

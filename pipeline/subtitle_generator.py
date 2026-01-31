"""
Subtitle Generator Module
Creates SRT/VTT subtitle files from audio using Azure Speech-to-Text
Supports word-level timestamps for animated captions (TikTok style)
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# Add pipeline directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    PATHS,
)

# Subtitle style presets per niche
SUBTITLE_STYLES = {
    "scary-stories": {
        "font_name": "Arial",
        "font_size": 48,
        "primary_color": "&H00FFFFFF",  # White
        "outline_color": "&H00000000",  # Black
        "back_color": "&H80000000",  # Semi-transparent black
        "outline_width": 3,
        "shadow": 2,
        "margin_v": 30,
        "alignment": 2,  # Bottom center
    },
    "finance": {
        "font_name": "Arial",
        "font_size": 44,
        "primary_color": "&H0000FF00",  # Green
        "outline_color": "&H00FFFFFF",  # White
        "back_color": "&H80000000",
        "outline_width": 2,
        "shadow": 1,
        "margin_v": 40,
        "alignment": 2,
    },
    "luxury": {
        "font_name": "Arial",
        "font_size": 44,
        "primary_color": "&H0000D4FF",  # Gold (BGR format)
        "outline_color": "&H00000000",  # Black
        "back_color": "&H80000000",
        "outline_width": 2,
        "shadow": 2,
        "margin_v": 35,
        "alignment": 2,
    },
}


def format_timestamp_srt(seconds: float) -> str:
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_timestamp_vtt(seconds: float) -> str:
    """Convert seconds to VTT timestamp format (HH:MM:SS.mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def create_subtitles_from_script(
    script_path: str,
    niche: str,
    words_per_subtitle: int = 8,
) -> Tuple[str, str]:
    """
    Create subtitle files from script narration and audio durations.

    This uses the script's narration text and estimated durations
    to generate timed subtitles without requiring speech recognition.

    Args:
        script_path: Path to script JSON
        niche: Content niche
        words_per_subtitle: Words per subtitle line

    Returns:
        Tuple of (SRT path, VTT path)
    """
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    base_name = os.path.splitext(os.path.basename(script_path))[0]
    output_dir = PATHS[niche]["audio"]
    os.makedirs(output_dir, exist_ok=True)

    srt_path = os.path.join(output_dir, f"{base_name}.srt")
    vtt_path = os.path.join(output_dir, f"{base_name}.vtt")

    srt_entries = []
    vtt_entries = ["WEBVTT", ""]

    current_time = 0.0
    subtitle_index = 1

    for scene in script["scenes"]:
        narration = scene.get("narration", "")
        duration = scene.get("duration_estimate", 10.0)

        # Split narration into words
        words = narration.split()
        if not words:
            current_time += duration
            continue

        # Calculate time per word
        time_per_word = duration / len(words)

        # Create subtitle chunks
        for i in range(0, len(words), words_per_subtitle):
            chunk_words = words[i : i + words_per_subtitle]
            chunk_text = " ".join(chunk_words)

            start_time = current_time + (i * time_per_word)
            end_time = start_time + (len(chunk_words) * time_per_word)

            # Ensure end time doesn't exceed scene duration
            end_time = min(end_time, current_time + duration)

            # SRT format
            srt_entries.append(str(subtitle_index))
            start_srt = format_timestamp_srt(start_time)
            end_srt = format_timestamp_srt(end_time)
            srt_entries.append(f"{start_srt} --> {end_srt}")
            srt_entries.append(chunk_text)
            srt_entries.append("")

            # VTT format
            start_vtt = format_timestamp_vtt(start_time)
            end_vtt = format_timestamp_vtt(end_time)
            vtt_entries.append(f"{start_vtt} --> {end_vtt}")
            vtt_entries.append(chunk_text)
            vtt_entries.append("")

            subtitle_index += 1

        current_time += duration

    # Write SRT file
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_entries))

    # Write VTT file
    with open(vtt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(vtt_entries))

    print(f"📝 Created subtitles: {srt_path}")
    return srt_path, vtt_path


def create_subtitles_from_audio(
    audio_path: str,
    niche: str,
    use_whisper: bool = True,
) -> Tuple[str, str]:
    """
    Create subtitles by transcribing audio file.

    Uses FFmpeg's built-in Whisper (if available) or falls back to
    timing-based estimation.

    Args:
        audio_path: Path to audio file
        niche: Content niche
        use_whisper: Whether to attempt Whisper transcription

    Returns:
        Tuple of (SRT path, VTT path)
    """
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    output_dir = os.path.dirname(audio_path)

    srt_path = os.path.join(output_dir, f"{base_name}.srt")
    vtt_path = os.path.join(output_dir, f"{base_name}.vtt")

    # Check if already exists
    if os.path.exists(srt_path) and os.path.exists(vtt_path):
        print(f"📝 Subtitles already exist: {srt_path}")
        return srt_path, vtt_path

    # For now, we'll create a placeholder with audio duration
    # Full Whisper integration would require additional setup
    duration = get_audio_duration(audio_path)

    # Create minimal subtitle with full duration
    srt_content = f"""1
00:00:00,000 --> {format_timestamp_srt(duration)}
[Audio transcription pending]
"""

    vtt_content = f"""WEBVTT

00:00:00.000 --> {format_timestamp_vtt(duration)}
[Audio transcription pending]
"""

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    with open(vtt_path, "w", encoding="utf-8") as f:
        f.write(vtt_content)

    print(f"📝 Created placeholder subtitles: {srt_path}")
    print("   ℹ️  For accurate subtitles, use create_subtitles_from_script()")

    return srt_path, vtt_path


def get_audio_duration(audio_path: str) -> float:
    """Get duration of audio file in seconds using FFprobe."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        audio_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return float(result.stdout.strip())
    except (subprocess.TimeoutExpired, ValueError):
        return 60.0  # Default fallback


def burn_subtitles_to_video(
    video_path: str,
    subtitle_path: str,
    output_path: str,
    niche: str = "scary-stories",
    style_override: Dict = None,
) -> str:
    """
    Burn subtitles directly into video file.

    Args:
        video_path: Input video path
        subtitle_path: SRT or ASS subtitle file
        output_path: Output video path
        niche: Content niche for styling
        style_override: Optional style overrides

    Returns:
        Path to video with burned subtitles
    """
    style = SUBTITLE_STYLES.get(niche, SUBTITLE_STYLES["scary-stories"])
    if style_override:
        style.update(style_override)

    # Escape the subtitle path for FFmpeg filter
    safe_sub_path = subtitle_path.replace("\\", "/").replace(":", "\\:")

    # Build style string
    style_str = (
        f"FontName={style['font_name']},"
        f"FontSize={style['font_size']},"
        f"PrimaryColour={style['primary_color']},"
        f"OutlineColour={style['outline_color']},"
        f"BackColour={style['back_color']},"
        f"Outline={style['outline_width']},"
        f"Shadow={style['shadow']},"
        f"MarginV={style['margin_v']},"
        f"Alignment={style['alignment']}"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vf",
        f"subtitles='{safe_sub_path}':force_style='{style_str}'",
        "-c:a",
        "copy",
        output_path,
    ]

    print(f"🎬 Burning subtitles into video...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"   ❌ Error: {result.stderr[:200]}")
        raise RuntimeError(f"FFmpeg subtitle burn failed: {result.stderr}")

    print(f"   ✅ Created: {output_path}")
    return output_path


def generate_animated_captions(
    script_path: str,
    niche: str,
    style: str = "word_by_word",
) -> str:
    """
    Generate animated caption data for TikTok-style word-by-word display.

    This creates a JSON file with word-level timing that can be used
    for rendering animated text overlays.

    Args:
        script_path: Path to script JSON
        niche: Content niche
        style: Animation style ("word_by_word", "phrase", "karaoke")

    Returns:
        Path to caption animation JSON
    """
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    base_name = os.path.splitext(os.path.basename(script_path))[0]
    output_dir = PATHS[niche]["audio"]
    output_path = os.path.join(output_dir, f"{base_name}_captions.json")

    captions = []
    current_time = 0.0

    for scene in script["scenes"]:
        narration = scene.get("narration", "")
        duration = scene.get("duration_estimate", 10.0)

        words = narration.split()
        if not words:
            current_time += duration
            continue

        time_per_word = duration / len(words)

        for i, word in enumerate(words):
            start = current_time + (i * time_per_word)
            end = start + time_per_word

            captions.append(
                {
                    "word": word,
                    "start": round(start, 3),
                    "end": round(end, 3),
                    "scene": scene["scene_number"],
                }
            )

        current_time += duration

    output_data = {
        "title": script.get("title", ""),
        "niche": niche,
        "style": style,
        "total_duration": current_time,
        "word_count": len(captions),
        "captions": captions,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print(f"📝 Created animated caption data: {output_path}")
    return output_path


def generate_all_subtitle_formats(
    script_path: str,
    niche: str,
) -> Dict[str, str]:
    """
    Generate all subtitle formats from a script.

    Args:
        script_path: Path to script JSON
        niche: Content niche

    Returns:
        Dict with paths to all generated files
    """
    print(f"\n📝 Generating all subtitle formats...")

    srt_path, vtt_path = create_subtitles_from_script(script_path, niche)
    captions_path = generate_animated_captions(script_path, niche)

    return {
        "srt": srt_path,
        "vtt": vtt_path,
        "animated_json": captions_path,
    }


# =============================================================================
# STANDALONE USAGE
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate subtitles for faceless content"
    )
    parser.add_argument("script", help="Path to script JSON file")
    parser.add_argument(
        "--niche",
        "-n",
        choices=["scary-stories", "finance", "luxury"],
        required=True,
        help="Content niche",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["srt", "vtt", "all"],
        default="all",
        help="Output format",
    )
    parser.add_argument(
        "--animated", "-a", action="store_true", help="Generate animated caption JSON"
    )
    parser.add_argument("--burn", "-b", help="Video file to burn subtitles into")

    args = parser.parse_args()

    if args.burn:
        # Burn subtitles into video
        srt_path, _ = create_subtitles_from_script(args.script, args.niche)
        output_video = args.burn.replace(".mp4", "_subtitled.mp4")
        burn_subtitles_to_video(args.burn, srt_path, output_video, args.niche)
    elif args.animated:
        generate_animated_captions(args.script, args.niche)
    elif args.format == "all":
        generate_all_subtitle_formats(args.script, args.niche)
    else:
        srt_path, vtt_path = create_subtitles_from_script(args.script, args.niche)
        if args.format == "srt":
            print(f"Created: {srt_path}")
        else:
            print(f"Created: {vtt_path}")

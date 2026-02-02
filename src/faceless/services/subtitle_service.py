"""
Subtitle Service

Creates SRT/VTT subtitle files from audio using Azure Speech-to-Text
Supports word-level timestamps for animated captions (TikTok style)
"""

import json
import subprocess
from pathlib import Path
from typing import Any

from faceless.config import get_settings
from faceless.utils.logging import get_logger

logger = get_logger(__name__)

# Subtitle style presets per niche
SUBTITLE_STYLES: dict[str, dict[str, Any]] = {
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


def get_audio_duration(audio_path: str | Path) -> float:
    """Get duration of audio file in seconds using FFprobe."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(audio_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return float(result.stdout.strip())
    except (subprocess.TimeoutExpired, ValueError):
        return 60.0  # Default fallback


def create_subtitles_from_script(
    script_path: str | Path,
    niche: str,
    output_dir: Path | None = None,
    words_per_subtitle: int = 8,
) -> tuple[Path, Path]:
    """
    Create subtitle files from script narration and audio durations.

    This uses the script's narration text and estimated durations
    to generate timed subtitles without requiring speech recognition.

    Args:
        script_path: Path to script JSON
        niche: Content niche
        output_dir: Output directory (defaults to script directory)
        words_per_subtitle: Words per subtitle line

    Returns:
        Tuple of (SRT path, VTT path)
    """
    script_path = Path(script_path)
    with open(script_path, encoding="utf-8") as f:
        script = json.load(f)

    base_name = script_path.stem
    if output_dir is None:
        settings = get_settings()
        output_dir = settings.output.base_dir / niche / "audio"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    srt_path = output_dir / f"{base_name}.srt"
    vtt_path = output_dir / f"{base_name}.vtt"

    srt_entries: list[str] = []
    vtt_entries: list[str] = ["WEBVTT", ""]

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

    logger.info("Created subtitles", path=str(srt_path))
    return srt_path, vtt_path


def create_subtitles_from_audio(
    audio_path: str | Path,
    niche: str,
) -> tuple[Path, Path]:
    """
    Create subtitles by transcribing audio file.

    Uses FFmpeg's built-in Whisper (if available) or falls back to
    timing-based estimation.

    Args:
        audio_path: Path to audio file
        niche: Content niche

    Returns:
        Tuple of (SRT path, VTT path)
    """
    audio_path = Path(audio_path)
    base_name = audio_path.stem
    output_dir = audio_path.parent

    srt_path = output_dir / f"{base_name}.srt"
    vtt_path = output_dir / f"{base_name}.vtt"

    # Check if already exists
    if srt_path.exists() and vtt_path.exists():
        logger.info("Subtitles already exist", path=str(srt_path))
        return srt_path, vtt_path

    # For now, create a placeholder with audio duration
    duration = get_audio_duration(audio_path)

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

    logger.info("Created placeholder subtitles", path=str(srt_path))
    logger.info("For accurate subtitles, use create_subtitles_from_script()")

    return srt_path, vtt_path


def burn_subtitles_to_video(
    video_path: str | Path,
    subtitle_path: str | Path,
    output_path: str | Path,
    niche: str = "scary-stories",
    style_override: dict[str, Any] | None = None,
) -> Path:
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
    style = SUBTITLE_STYLES.get(niche, SUBTITLE_STYLES["scary-stories"]).copy()
    if style_override:
        style.update(style_override)

    # Escape the subtitle path for FFmpeg filter
    safe_sub_path = str(subtitle_path).replace("\\", "/").replace(":", "\\:")

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
        str(video_path),
        "-vf",
        f"subtitles='{safe_sub_path}':force_style='{style_str}'",
        "-c:a",
        "copy",
        str(output_path),
    ]

    logger.info(
        "Burning subtitles into video",
        video=str(video_path),
        subtitle=str(subtitle_path),
    )
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error("FFmpeg subtitle burn failed", error=result.stderr[:200])
        raise RuntimeError(f"FFmpeg subtitle burn failed: {result.stderr}")

    logger.info("Created video with subtitles", path=str(output_path))
    return Path(output_path)


def generate_animated_captions(
    script_path: str | Path,
    niche: str,
    output_dir: Path | None = None,
    style: str = "word_by_word",
) -> Path:
    """
    Generate animated caption data for TikTok-style word-by-word display.

    This creates a JSON file with word-level timing that can be used
    for rendering animated text overlays.

    Args:
        script_path: Path to script JSON
        niche: Content niche
        output_dir: Output directory (defaults to audio dir)
        style: Animation style ("word_by_word", "phrase", "karaoke")

    Returns:
        Path to caption animation JSON
    """
    script_path = Path(script_path)
    with open(script_path, encoding="utf-8") as f:
        script = json.load(f)

    base_name = script_path.stem
    if output_dir is None:
        settings = get_settings()
        output_dir = settings.output.base_dir / niche / "audio"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{base_name}_captions.json"

    captions: list[dict[str, Any]] = []
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

    logger.info(
        "Created animated caption data",
        path=str(output_path),
        word_count=len(captions),
    )
    return output_path


def generate_all_subtitle_formats(
    script_path: str | Path,
    niche: str,
    output_dir: Path | None = None,
) -> dict[str, Path]:
    """
    Generate all subtitle formats from a script.

    Args:
        script_path: Path to script JSON
        niche: Content niche
        output_dir: Optional output directory

    Returns:
        Dict with paths to all generated files
    """
    logger.info(
        "Generating all subtitle formats",
        script=str(script_path),
        niche=niche,
    )

    srt_path, vtt_path = create_subtitles_from_script(
        script_path, niche, output_dir=output_dir
    )
    captions_path = generate_animated_captions(
        script_path, niche, output_dir=output_dir
    )

    return {
        "srt": srt_path,
        "vtt": vtt_path,
        "animated_json": captions_path,
    }

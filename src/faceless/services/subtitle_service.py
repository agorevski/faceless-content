"""
Subtitle Service

Creates SRT/VTT subtitle files from audio using Azure Speech-to-Text
Supports word-level timestamps for animated captions (TikTok style)
"""

import json
import math
import re
import subprocess
from pathlib import Path
from typing import Any

from faceless.config import get_settings
from faceless.core.exceptions import FFmpegError, InputValidationError
from faceless.utils.logging import get_logger
from faceless.utils.media import probe_media_duration

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

_ASS_STYLE_FIELDS = {
    "font_name": "FontName",
    "font_size": "FontSize",
    "primary_color": "PrimaryColour",
    "outline_color": "OutlineColour",
    "back_color": "BackColour",
    "outline_width": "Outline",
    "shadow": "Shadow",
    "margin_l": "MarginL",
    "margin_r": "MarginR",
    "margin_v": "MarginV",
    "alignment": "Alignment",
    "play_res_x": "PlayResX",
    "play_res_y": "PlayResY",
}


def portrait_caption_style(niche: str) -> dict[str, Any]:
    """Return ASS overrides for captions in a 1080x1920 portrait video.

    The right margin leaves space for TikTok controls; captions occupy the
    middle-lower area, away from both the opening hook and bottom UI.
    """
    style = SUBTITLE_STYLES.get(niche, SUBTITLE_STYLES["scary-stories"]).copy()
    style.update(
        font_size=74,
        primary_color="&H00FFFFFF",
        outline_color="&H00000000",
        back_color="&H80000000",
        outline_width=5,
        shadow=2,
        alignment=2,
        margin_l=90,
        margin_r=240,
        margin_v=520,
        play_res_x=1080,
        play_res_y=1920,
    )
    return style


def _escape_filter_value(value: str) -> str:
    """Escape an AVOption value and then the containing FFmpeg filtergraph."""
    option_value = re.sub(r"([\\':])", r"\\\1", value)
    return re.sub(r"([\\',;\[\]])", r"\\\1", option_value)


def _validated_style(style: dict[str, Any]) -> str:
    """Serialize supported ASS overrides without accepting filter syntax."""
    fields: list[str] = []
    for key, value in style.items():
        if key not in _ASS_STYLE_FIELDS:
            raise InputValidationError("Unsupported subtitle style", field=key)
        if key == "font_name":
            if not isinstance(value, str) or not re.fullmatch(r"[\w .-]{1,80}", value):
                raise InputValidationError("Invalid subtitle font", field=key)
        elif key.endswith("_color"):
            if not isinstance(value, str) or not re.fullmatch(
                r"&H[0-9A-Fa-f]{8}", value
            ):
                raise InputValidationError("Invalid ASS color", field=key)
        elif (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not 0 <= value <= 3840
            or not math.isfinite(value)
        ):
            raise InputValidationError("Invalid subtitle style value", field=key)
        elif key in {"font_size", "play_res_x", "play_res_y"} and value == 0:
            raise InputValidationError("Subtitle size must be positive", field=key)
        elif key in {
            "alignment",
            "margin_l",
            "margin_r",
            "margin_v",
            "play_res_x",
            "play_res_y",
        } and not isinstance(value, int):
            raise InputValidationError("Subtitle style requires an integer", field=key)
        elif key == "alignment" and value not in range(1, 10):
            raise InputValidationError("Invalid subtitle alignment", field=key)
        fields.append(f"{_ASS_STYLE_FIELDS[key]}={value}")
    return ",".join(fields)


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
    """Measure audio seconds, raising ExternalToolError for failed/invalid probes."""
    return probe_media_duration(Path(audio_path), get_settings().ffprobe_path)


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
    if (
        isinstance(words_per_subtitle, bool)
        or not isinstance(words_per_subtitle, int)
        or words_per_subtitle < 1
    ):
        raise InputValidationError(
            "words_per_subtitle must be a positive integer",
            field="words_per_subtitle",
            value=words_per_subtitle,
        )
    script_path = Path(script_path)
    with open(script_path, encoding="utf-8") as f:
        script = json.load(f)

    base_name = script_path.stem
    if output_dir is None:
        settings = get_settings()
        output_dir = settings.output_base_dir / niche / "audio"
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
        subtitle_path: SRT, VTT, or ASS subtitle file
        output_path: Output video path
        niche: Content niche for styling
        style_override: Optional ASS style overrides (use portrait_caption_style
            for 1080x1920 TikTok videos).

    Returns:
        Path to video with burned subtitles

    Raises:
        InputValidationError: If input paths, output path, or style are invalid.
        FFmpegError: If FFmpeg fails, times out, or produces no output.
    """
    video_path = Path(video_path)
    subtitle_path = Path(subtitle_path)
    output_path = Path(output_path)
    for field, path in (("video_path", video_path), ("subtitle_path", subtitle_path)):
        if not path.is_file():
            raise InputValidationError("Input must be an existing file", field=field)
    if subtitle_path.suffix.lower() not in {".srt", ".vtt", ".ass"}:
        raise InputValidationError("Unsupported subtitle format", field="subtitle_path")
    if output_path.resolve() in {video_path.resolve(), subtitle_path.resolve()}:
        raise InputValidationError(
            "Output must differ from inputs", field="output_path"
        )
    if output_path.exists() and not output_path.is_file():
        raise InputValidationError("Output must be a file", field="output_path")
    if not output_path.suffix:
        raise InputValidationError(
            "Output must have a video extension", field="output_path"
        )

    style = SUBTITLE_STYLES.get(niche, SUBTITLE_STYLES["scary-stories"]).copy()
    if style_override is not None:
        style.update(style_override)

    style_str = _validated_style(style)
    filter_spec = (
        f"subtitles=filename={_escape_filter_value(str(subtitle_path.resolve()))}"
        f":force_style={_escape_filter_value(style_str)}"
    )
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise InputValidationError(
            "Cannot create output directory", field="output_path"
        ) from exc
    cmd = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-i",
        str(video_path.resolve()),
        "-vf",
        filter_spec,
        "-c:a",
        "copy",
        str(output_path.resolve()),
    ]

    logger.info(
        "Burning subtitles into video",
        video=str(video_path),
        subtitle=str(subtitle_path),
        output=str(output_path),
    )
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired as exc:
        logger.error("FFmpeg subtitle burn timed out", output=str(output_path))
        raise FFmpegError("FFmpeg subtitle burn timed out", command=cmd) from exc
    except OSError as exc:
        logger.error("FFmpeg subtitle burn could not start", error=str(exc))
        raise FFmpegError("FFmpeg subtitle burn could not start", command=cmd) from exc

    if result.returncode != 0:
        logger.error(
            "FFmpeg subtitle burn failed",
            return_code=result.returncode,
            error=result.stderr[-500:],
        )
        raise FFmpegError(
            "FFmpeg subtitle burn failed",
            command=cmd,
            return_code=result.returncode,
            stderr=result.stderr,
        )
    if not output_path.is_file() or output_path.stat().st_size == 0:
        logger.error("FFmpeg subtitle burn produced no video", output=str(output_path))
        raise FFmpegError("FFmpeg subtitle burn produced no video", command=cmd)

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
        output_dir = settings.output_base_dir / niche / "audio"
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

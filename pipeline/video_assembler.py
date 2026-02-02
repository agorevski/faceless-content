"""
Video Assembler Module - LEGACY WRAPPER.

⚠️ DEPRECATED: This module is a backward-compatibility wrapper.
Please use faceless.services.video_service.VideoService for new code.

This wrapper delegates to the modern implementation in src/faceless/services/
while maintaining the original API for existing scripts.
"""

import json
import os
import random
import subprocess
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed

# Issue deprecation warning on import
warnings.warn(
    "pipeline/video_assembler.py is deprecated. "
    "Use faceless.services.video_service.VideoService instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Import legacy config for backward compatibility
from env_config import OUTPUT_SETTINGS, PATHS
from faceless.utils.logging import get_logger

logger = get_logger(__name__)


def get_audio_duration(audio_path: str) -> float:
    """Get duration of an audio file in seconds using FFprobe."""
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
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def get_image_dimensions(image_path: str) -> tuple:
    """Get width and height of an image using FFprobe."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=p=0:s=x",
        image_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    width, height = result.stdout.strip().split("x")
    return int(width), int(height)


def create_video_from_image_and_audio(
    image_path: str,
    audio_path: str,
    output_path: str,
    platform: str = "youtube",
    zoom_effect: bool = True,
    pan_direction: str = None,
) -> str:
    """
    Create a video from a single image and audio file.

    ⚠️ DEPRECATED: Use VideoService.create_scene_video() instead.

    Args:
        image_path: Path to the image
        audio_path: Path to the audio
        output_path: Path for the output video
        platform: "youtube" (16:9) or "tiktok" (9:16)
        zoom_effect: Whether to apply Ken Burns zoom effect
        pan_direction: For TikTok, direction of pan: "left", "right", "center", or None for random

    Returns:
        Path to the created video
    """

    settings = OUTPUT_SETTINGS[platform]
    duration = get_audio_duration(audio_path)
    total_frames = int(duration * settings["fps"])

    # Get source image dimensions
    src_width, src_height = get_image_dimensions(image_path)
    src_aspect = src_width / src_height

    # Target dimensions
    target_width, target_height = map(int, settings["resolution"].split("x"))
    target_aspect = target_width / target_height

    # Build FFmpeg command
    if zoom_effect:
        if platform == "tiktok" and src_aspect > 1.0:
            # TikTok with landscape source image: CROP + PAN + ZOOM
            # Instead of squeezing, we crop to 9:16 and pan across the image

            # Choose pan direction
            if pan_direction is None:
                pan_direction = random.choice(["left", "right", "center"])

            # Calculate crop dimensions for 9:16 from landscape source
            # Crop height = full source height, crop width = height * 9/16
            crop_h = src_height
            crop_w = int(src_height * (9 / 16))

            # Calculate how much horizontal space we have to pan
            pan_range = src_width - crop_w

            # Scale factor for headroom (allow slight zoom during pan)
            # We'll work at a slightly larger scale, then zoom in slightly
            scale_factor = 1.15  # 15% larger than needed
            scaled_w = int(target_width * scale_factor)
            scaled_h = int(target_height * scale_factor)

            # Zoom: start at 1.0, end at ~1.08 (subtle zoom during pan)
            zoom_start = 1.0
            zoom_end = 1.08
            zoom_expr = f"zoom+{(zoom_end - zoom_start) / total_frames}"

            # Pan expressions based on direction
            # Note: FFmpeg crop filter x/y are evaluated per-frame, but they don't support 'on'
            # We need to use zoompan for animated movement instead
            # So we'll do a static crop first, then use zoompan for the pan+zoom effect

            if pan_direction == "left":
                # Start from right side, pan to left
                crop_x = pan_range  # Start at right side
                # zoompan x expression: start at right edge, move to left
                zp_x_expr = f"(iw-ow)*(1-on/{total_frames})"
            elif pan_direction == "right":
                # Start from left side, pan to right
                crop_x = 0  # Start at left side
                # zoompan x expression: start at left edge, move to right
                zp_x_expr = f"(iw-ow)*(on/{total_frames})"
            else:  # center - gentle zoom only, no pan
                crop_x = pan_range // 2  # Center
                zp_x_expr = "(iw-ow)/2"

            # Build the filter:
            # 1. Scale source image up to provide pan headroom
            # 2. Use zoompan with animated x for panning + zoom effect
            # We scale to larger than needed, then zoompan crops/pans within that

            # Calculate the scale needed: we want the height to match target after zoom
            # and have extra width for panning
            base_scale_h = int(target_height * scale_factor)
            # Maintain aspect ratio for width based on source
            base_scale_w = int(base_scale_h * src_aspect)

            filter_complex = (
                f"[0:v]scale={base_scale_w}:{base_scale_h},"
                f"zoompan=z='{zoom_expr}':"
                f"x='{zp_x_expr}':y='(ih-oh)/2':"
                f"d={total_frames}:s={target_width}x{target_height}:fps={settings['fps']}[v]"
            )

            logger.debug("TikTok crop+pan mode", pan_direction=pan_direction)

        else:
            # YouTube or TikTok with portrait source: Ken Burns zoom from center
            filter_complex = (
                f"[0:v]scale=8000:-1,zoompan=z='min(zoom+0.0005,1.1)':x='iw/2-(iw/zoom/2)':"
                f"y='ih/2-(ih/zoom/2)':d={total_frames}:s={settings['resolution']}:fps={settings['fps']}[v]"
            )
    else:
        # Static image with scaling
        filter_complex = f"[0:v]scale={settings['resolution']}:force_original_aspect_ratio=decrease,pad={settings['resolution']}:(ow-iw)/2:(oh-ih)/2[v]"

    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output
        "-loop",
        "1",
        "-i",
        image_path,
        "-i",
        audio_path,
        "-filter_complex",
        filter_complex,
        "-map",
        "[v]",
        "-map",
        "1:a",
        "-c:v",
        settings["codec"],
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-pix_fmt",
        "yuv420p",
        output_path,
    ]

    logger.info(
        "Creating video segment",
        image=os.path.basename(image_path),
        audio=os.path.basename(audio_path),
    )

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error("FFmpeg error creating video segment", error=result.stderr)
        raise RuntimeError(f"FFmpeg error: {result.stderr}")

    logger.info("Video segment created", output=output_path)
    return output_path


def concatenate_videos(
    video_paths: list,
    output_path: str,
) -> str:
    """
    Concatenate multiple videos into one.

    ⚠️ DEPRECATED: Use VideoService.concatenate_scenes() instead.

    Args:
        video_paths: List of paths to video files
        output_path: Path for the output video

    Returns:
        Path to the concatenated video
    """

    # Create a temporary file list
    list_path = output_path + ".txt"
    with open(list_path, "w", encoding="utf-8") as f:
        for path in video_paths:
            # Escape single quotes and use forward slashes
            safe_path = path.replace("\\", "/").replace("'", "'\\''")
            f.write(f"file '{safe_path}'\n")

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        list_path,
        "-c",
        "copy",
        output_path,
    ]

    logger.info("Concatenating videos", count=len(video_paths))

    result = subprocess.run(cmd, capture_output=True, text=True)

    # Clean up temp file
    os.remove(list_path)

    if result.returncode != 0:
        logger.error("FFmpeg error concatenating videos", error=result.stderr)
        raise RuntimeError(f"FFmpeg error: {result.stderr}")

    logger.info("Concatenated video created", output=output_path)
    return output_path


def add_background_music(
    video_path: str,
    music_path: str,
    output_path: str,
    music_volume: float = 0.15,
) -> str:
    """
    Add background music to a video, mixed with existing audio.

    ⚠️ DEPRECATED: Use VideoService.add_background_music() instead.

    Args:
        video_path: Path to the video
        music_path: Path to the background music
        output_path: Path for the output video
        music_volume: Volume level for music (0.0 to 1.0)

    Returns:
        Path to the video with music
    """

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-i",
        music_path,
        "-filter_complex",
        f"[1:a]volume={music_volume}[music];[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[aout]",
        "-map",
        "0:v",
        "-map",
        "[aout]",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        output_path,
    ]

    logger.info("Adding background music", music_volume=music_volume)

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error("FFmpeg error adding background music", error=result.stderr)
        raise RuntimeError(f"FFmpeg error: {result.stderr}")

    logger.info("Video with music created", output=output_path)
    return output_path


def add_subtitles(
    video_path: str,
    subtitle_path: str,
    output_path: str,
    font_size: int = 24,
    font_color: str = "white",
    outline_color: str = "black",
) -> str:
    """
    Burn subtitles into a video.

    Args:
        video_path: Path to the video
        subtitle_path: Path to SRT subtitle file
        output_path: Path for the output video
        font_size: Size of subtitle font
        font_color: Color of subtitle text
        outline_color: Color of text outline

    Returns:
        Path to the video with subtitles
    """

    # Escape the subtitle path for FFmpeg filter
    safe_subtitle_path = subtitle_path.replace("\\", "/").replace(":", "\\:")

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vf",
        f"subtitles='{safe_subtitle_path}':force_style='FontSize={font_size},PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,Outline=2'",
        "-c:a",
        "copy",
        output_path,
    ]

    logger.info("Adding subtitles", subtitle_path=subtitle_path)

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error("FFmpeg error adding subtitles", error=result.stderr)
        raise RuntimeError(f"FFmpeg error: {result.stderr}")

    logger.info("Video with subtitles created", output=output_path)
    return output_path


def _create_segment_task(args: tuple) -> tuple:
    """
    Worker function for parallel video segment creation.

    Args:
        args: Tuple of (scene_index, image_path, audio_path, segment_path, platform)

    Returns:
        Tuple of (scene_index, segment_path, success, error_message, skipped)
    """
    scene_index, image_path, audio_path, segment_path, platform = args

    # Skip if segment already exists
    if os.path.exists(segment_path):
        return (scene_index, segment_path, True, None, True)

    if not os.path.exists(image_path) or not os.path.exists(audio_path):
        return (
            scene_index,
            segment_path,
            False,
            f"Missing assets for scene {scene_index}",
            False,
        )

    try:
        create_video_from_image_and_audio(
            image_path, audio_path, segment_path, platform
        )
        return (scene_index, segment_path, True, None, False)
    except Exception as e:
        return (scene_index, segment_path, False, str(e), False)


def assemble_from_script(
    script_path: str,
    niche: str,
    platform: str = "youtube",
    add_music: bool = False,
    music_path: str = None,
    max_workers: int = None,
) -> str:
    """
    Assemble a complete video from a script with generated assets.

    ⚠️ DEPRECATED: Use VideoService.assemble_video() instead.

    Assumes images and audio have already been generated using the
    image_generator and tts_generator modules.

    Uses parallel processing to create video segments concurrently.

    Args:
        script_path: Path to the script JSON file
        niche: One of "scary-stories", "finance", "luxury"
        platform: "youtube" or "tiktok"
        add_music: Whether to add background music
        music_path: Path to background music file
        max_workers: Maximum number of parallel FFmpeg processes (default: min(cpu_count, 4))

    Returns:
        Path to the final video
    """

    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    base_name = os.path.splitext(os.path.basename(script_path))[0]
    paths = PATHS[niche]

    # Determine number of workers
    if max_workers is None:
        max_workers = min(os.cpu_count() or 4, 4)  # Default to min of CPU count or 4

    # Prepare tasks for parallel execution
    tasks = []
    for i, scene in enumerate(script["scenes"], 1):
        image_path = os.path.join(paths["images"], f"{base_name}_{i:03d}.png")
        audio_path = os.path.join(paths["audio"], f"{base_name}_{i:03d}.mp3")
        segment_path = os.path.join(paths["videos"], f"{base_name}_{i:03d}.mp4")
        tasks.append((i, image_path, audio_path, segment_path, platform))

    logger.info(
        "Creating video segments in parallel",
        segment_count=len(tasks),
        max_workers=max_workers,
    )

    # Execute tasks in parallel
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_create_segment_task, task): task for task in tasks}

        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            scene_index, segment_path, success, error, skipped = result
            if skipped:
                logger.debug("Scene already exists, skipping", scene_index=scene_index)
            elif not success:
                logger.warning("Scene processing failed", scene_index=scene_index, error=error)

    # Sort results by scene index to maintain order
    results.sort(key=lambda x: x[0])

    # Collect successful segment paths in order
    segment_paths = [
        segment_path
        for scene_index, segment_path, success, error, skipped in results
        if success
    ]

    if not segment_paths:
        raise RuntimeError("No video segments were created successfully")

    created_count = sum(1 for r in results if r[2] and not r[4])
    skipped_count = sum(1 for r in results if r[4])
    logger.info(
        "Video segments processed",
        created=created_count,
        skipped=skipped_count,
        total=len(segment_paths),
    )

    # Concatenate all segments
    output_path = os.path.join(paths["output"], f"{base_name}_{platform}.mp4")
    concatenate_videos(segment_paths, output_path)

    # Optionally add background music
    if add_music and music_path and os.path.exists(music_path):
        music_output = os.path.join(
            paths["output"], f"{base_name}_{platform}_music.mp4"
        )
        add_background_music(output_path, music_path, music_output)
        output_path = music_output

    # Clean up segment files (optional)
    # for path in segment_paths:
    #     os.remove(path)

    return output_path


def create_tiktok_cuts(
    long_video_path: str,
    output_dir: str,
    segment_duration: int = 60,
    overlap: int = 2,
) -> list:
    """
    Split a long video into TikTok-length segments.

    Args:
        long_video_path: Path to the source video
        output_dir: Directory for output segments
        segment_duration: Length of each segment in seconds
        overlap: Seconds of overlap between segments for continuity

    Returns:
        List of paths to the created segments
    """

    # Get total duration
    duration = get_audio_duration(long_video_path)

    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(long_video_path))[0]

    segment_paths = []
    start_time = 0
    part = 1

    while start_time < duration:
        output_path = os.path.join(output_dir, f"{base_name}_part{part}.mp4")

        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            str(start_time),
            "-i",
            long_video_path,
            "-t",
            str(segment_duration),
            "-c",
            "copy",
            output_path,
        ]

        subprocess.run(cmd, capture_output=True)
        segment_paths.append(output_path)

        start_time += segment_duration - overlap
        part += 1

    logger.info("TikTok segments created", count=len(segment_paths))
    return segment_paths


# =============================================================================
# STANDALONE USAGE
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Assemble videos from assets")
    parser.add_argument("script", help="Path to script JSON file")
    parser.add_argument(
        "--niche", "-n", choices=["scary-stories", "finance", "luxury"], required=True
    )
    parser.add_argument(
        "--platform", "-p", choices=["youtube", "tiktok"], default="youtube"
    )
    parser.add_argument("--music", "-m", help="Path to background music file")
    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=None,
        help="Max parallel FFmpeg processes (default: min(cpu_count, 4))",
    )

    args = parser.parse_args()

    assemble_from_script(
        args.script,
        args.niche,
        args.platform,
        add_music=bool(args.music),
        music_path=args.music,
        max_workers=args.workers,
    )

"""
Video assembly service for the Faceless Content Pipeline.

This service handles assembling final videos from generated images and audio,
using FFmpeg for video processing.
"""

import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from faceless.config import get_settings
from faceless.core.enums import Platform
from faceless.core.exceptions import FFmpegError, VideoAssemblyError
from faceless.core.models import Checkpoint, Scene, Script
from faceless.utils.logging import LoggerMixin


class VideoService(LoggerMixin):
    """
    Service for assembling videos from images and audio.

    Handles:
    - Scene video creation (image + audio)
    - Scene concatenation into final video
    - Platform-specific formatting
    - Background music mixing
    - Ken Burns effect (zoom/pan)

    Example:
        >>> service = VideoService()
        >>> service.assemble_video(script, Platform.YOUTUBE)
    """

    def __init__(self) -> None:
        """Initialize video service."""
        self._settings = get_settings()
        # Resolve full path to ffmpeg/ffprobe on Windows
        self._ffmpeg = self._resolve_executable(self._settings.ffmpeg_path)
        self._ffprobe = self._resolve_executable(self._settings.ffprobe_path)

    def _resolve_executable(self, path: str) -> str:
        """
        Resolve executable path, using shutil.which() if needed.

        On Windows, subprocess.run with shell=False needs the full path
        to executables, or they won't be found in PATH.

        Args:
            path: Path or command name (e.g., 'ffmpeg' or 'C:\\path\\to\\ffmpeg.exe')

        Returns:
            Full path to executable, or original path if not found
        """
        # If it's already a full path, use it
        if Path(path).is_absolute() or "/" in path or "\\" in path:
            return path

        # Try to find in PATH
        resolved = shutil.which(path)
        if resolved:
            return resolved

        # Fall back to original (will likely fail, but error will be clearer)
        return path

    def _run_ffmpeg(
        self,
        args: list[str],
        description: str = "FFmpeg command",
    ) -> subprocess.CompletedProcess[str]:
        """
        Run an FFmpeg command.

        Args:
            args: FFmpeg command arguments (without 'ffmpeg')
            description: Description for logging

        Returns:
            CompletedProcess result

        Raises:
            FFmpegError: On FFmpeg failure
        """
        # Build command - use shell=True on Windows if executable not resolved
        use_shell = self._ffmpeg == "ffmpeg"  # Not resolved to full path

        if use_shell:
            # Build command string for shell execution
            cmd_str = "ffmpeg " + " ".join(
                f'"{arg}"' if " " in arg else arg for arg in args
            )
            cmd = cmd_str
        else:
            cmd = [self._ffmpeg] + args

        self.logger.debug(
            "Running FFmpeg",
            description=description,
            command=str(cmd)[:100] + "...",
            use_shell=use_shell,
        )

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
                shell=use_shell,
            )

            if result.returncode != 0:
                self.logger.error(
                    "FFmpeg command failed",
                    description=description,
                    return_code=result.returncode,
                    stderr=result.stderr[:500] if result.stderr else None,
                )
                raise FFmpegError(
                    message=f"{description} failed",
                    command=[cmd] if isinstance(cmd, str) else cmd,
                    return_code=result.returncode,
                    stderr=result.stderr,
                )

            return result

        except subprocess.TimeoutExpired as e:
            raise FFmpegError(
                message=f"{description} timed out",
                command=[cmd] if isinstance(cmd, str) else cmd,
            ) from e
        except FileNotFoundError as e:
            raise FFmpegError(
                message="FFmpeg not found. Ensure it is installed and in PATH.",
                command=[cmd] if isinstance(cmd, str) else cmd,
            ) from e
        except OSError as e:
            # Catch Windows-specific errors like WinError 87
            self.logger.error(
                "FFmpeg OS error",
                description=description,
                error=str(e),
                command_preview=str(cmd)[:50],
            )
            raise FFmpegError(
                message=f"{description} failed with OS error: {e}",
                command=[cmd] if isinstance(cmd, str) else cmd,
            ) from e

    def create_scene_video(
        self,
        scene: Scene,
        platform: Platform,
        output_path: Path,
        enable_ken_burns: bool = True,
    ) -> Path:
        """
        Create a video for a single scene (image + audio).

        Args:
            scene: Scene with image_path and audio_path set
            platform: Target platform for resolution
            output_path: Path for output video
            enable_ken_burns: Enable zoom/pan effect

        Returns:
            Path to created video

        Raises:
            VideoAssemblyError: On assembly failure
        """
        if not scene.image_path or not scene.image_path.exists():
            raise VideoAssemblyError(
                message=f"Image not found for scene {scene.scene_number}",
                stage="scene_video",
            )

        if not scene.audio_path or not scene.audio_path.exists():
            raise VideoAssemblyError(
                message=f"Audio not found for scene {scene.scene_number}",
                stage="scene_video",
            )

        width, height = platform.resolution
        duration = scene.duration_estimate

        # Build filter for Ken Burns effect
        if enable_ken_burns:
            # Subtle zoom effect (1.0 to 1.05 scale over duration)
            filter_complex = (
                f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
                f"zoompan=z='min(zoom+0.0005,1.05)':d={int(duration*25)}:s={width}x{height}:fps=25"
                f"[v]"
            )
        else:
            filter_complex = (
                f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
                f"loop=loop=-1:size=1:start=0[v]"
            )

        args = [
            "-y",  # Overwrite output
            "-loop",
            "1",  # Loop image
            "-i",
            str(scene.image_path),  # Image input
            "-i",
            str(scene.audio_path),  # Audio input
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
            "-map",
            "1:a",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",  # Match shortest input (audio)
            "-pix_fmt",
            "yuv420p",
            str(output_path),
        ]

        self._run_ffmpeg(args, f"Creating scene {scene.scene_number} video")
        scene.video_path = output_path

        self.logger.info(
            "Created scene video",
            scene_number=scene.scene_number,
            output=str(output_path),
        )

        return output_path

    def concatenate_scenes(
        self,
        scene_videos: list[Path],
        output_path: Path,
    ) -> Path:
        """
        Concatenate scene videos into a single video.

        Args:
            scene_videos: List of scene video paths in order
            output_path: Path for final output

        Returns:
            Path to concatenated video

        Raises:
            VideoAssemblyError: On concatenation failure
        """
        if not scene_videos:
            raise VideoAssemblyError(
                message="No scene videos to concatenate",
                stage="concatenation",
            )

        # Create concat file
        concat_file = output_path.parent / ".concat_list.txt"
        with open(concat_file, "w") as f:
            for video in scene_videos:
                f.write(f"file '{video.absolute()}'\n")

        try:
            args = [
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-c",
                "copy",
                str(output_path),
            ]

            self._run_ffmpeg(args, "Concatenating scene videos")

            self.logger.info(
                "Concatenated videos",
                scene_count=len(scene_videos),
                output=str(output_path),
            )

            return output_path

        finally:
            # Clean up concat file
            if concat_file.exists():
                concat_file.unlink()

    def add_background_music(
        self,
        video_path: Path,
        music_path: Path,
        output_path: Path,
        music_volume: float = 0.15,
    ) -> Path:
        """
        Add background music to a video.

        Args:
            video_path: Path to input video
            music_path: Path to music file
            output_path: Path for output video
            music_volume: Volume level for music (0.0 to 1.0)

        Returns:
            Path to video with music

        Raises:
            VideoAssemblyError: On failure
        """
        if not video_path.exists():
            raise VideoAssemblyError(
                message="Input video not found",
                stage="music_mixing",
                input_files=[str(video_path)],
            )

        if not music_path.exists():
            raise VideoAssemblyError(
                message="Music file not found",
                stage="music_mixing",
                input_files=[str(music_path)],
            )

        # Mix audio: keep original audio and add music at lower volume
        filter_complex = (
            f"[1:a]volume={music_volume}[music];"
            f"[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )

        args = [
            "-y",
            "-i",
            str(video_path),
            "-stream_loop",
            "-1",  # Loop music
            "-i",
            str(music_path),
            "-filter_complex",
            filter_complex,
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
            "-shortest",
            str(output_path),
        ]

        self._run_ffmpeg(args, "Adding background music")

        self.logger.info(
            "Added background music",
            output=str(output_path),
            music_volume=music_volume,
        )

        return output_path

    def assemble_video(
        self,
        script: Script,
        platform: Platform,
        checkpoint: Checkpoint | None = None,
        music_path: Path | None = None,
        enable_ken_burns: bool = True,
    ) -> Path:
        """
        Assemble a complete video from a script using parallel scene processing.

        Args:
            script: Script with generated images and audio
            platform: Target platform
            checkpoint: Optional checkpoint for resume support
            music_path: Optional background music
            enable_ken_burns: Enable zoom/pan effect

        Returns:
            Path to final video

        Raises:
            VideoAssemblyError: On assembly failure
        """
        videos_dir = self._settings.get_videos_dir(script.niche) / script.safe_title
        videos_dir.mkdir(parents=True, exist_ok=True)

        output_dir = self._settings.get_final_output_dir(script.niche)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Collect scenes that need processing
        scenes_to_process: list[tuple[Scene, Path]] = []
        scene_video_paths: dict[int, Path] = {}  # scene_number -> path

        for scene in script.scenes:
            scene_video_path = (
                videos_dir / f"scene_{scene.scene_number:02d}_{platform.value}.mp4"
            )

            # Skip if already done
            if checkpoint and checkpoint.is_video_done(
                platform.value, scene.scene_number
            ):
                if scene_video_path.exists():
                    self.logger.info(
                        "Skipping existing scene video",
                        scene_number=scene.scene_number,
                    )
                    scene_video_paths[scene.scene_number] = scene_video_path
                    continue

            scenes_to_process.append((scene, scene_video_path))

        # Process scenes in parallel
        if scenes_to_process:
            max_concurrent = self._settings.max_concurrent_videos
            errors: list[str] = []

            self.logger.info(
                "Starting parallel video scene creation",
                scenes_to_process=len(scenes_to_process),
                max_concurrent=max_concurrent,
            )

            # Helper function for thread pool
            def create_single_scene(
                scene: Scene,
                output_path: Path,
            ) -> tuple[int, Path | None, str | None]:
                """Create video for a single scene."""
                try:
                    width, height = platform.resolution
                    duration = scene.duration_estimate

                    # Build filter for Ken Burns effect
                    if enable_ken_burns:
                        filter_complex = (
                            f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
                            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
                            f"zoompan=z='min(zoom+0.0005,1.05)':d={int(duration*25)}:s={width}x{height}:fps=25"
                            f"[v]"
                        )
                    else:
                        filter_complex = (
                            f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
                            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
                            f"loop=loop=-1:size=1:start=0[v]"
                        )

                    args = [
                        "-y",
                        "-loop",
                        "1",
                        "-i",
                        str(scene.image_path),
                        "-i",
                        str(scene.audio_path),
                        "-filter_complex",
                        filter_complex,
                        "-map",
                        "[v]",
                        "-map",
                        "1:a",
                        "-c:v",
                        "libx264",
                        "-preset",
                        "medium",
                        "-crf",
                        "23",
                        "-c:a",
                        "aac",
                        "-b:a",
                        "192k",
                        "-shortest",
                        "-pix_fmt",
                        "yuv420p",
                        str(output_path),
                    ]

                    self._run_ffmpeg(args, f"Creating scene {scene.scene_number} video")
                    return (scene.scene_number, output_path, None)
                except Exception as e:
                    return (scene.scene_number, None, str(e))

            with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                future_to_scene = {
                    executor.submit(create_single_scene, scene, output_path): (
                        scene,
                        output_path,
                    )
                    for scene, output_path in scenes_to_process
                }

                for future in as_completed(future_to_scene):
                    scene, output_path = future_to_scene[future]
                    scene_number, path, error = future.result()

                    if path:
                        scene.video_path = path
                        scene_video_paths[scene_number] = path
                        if checkpoint:
                            checkpoint.mark_video_done(platform.value, scene_number)
                        self.logger.info(
                            "Created scene video",
                            scene_number=scene_number,
                            output=str(path),
                        )
                    else:
                        self.logger.error(
                            "Scene video creation failed",
                            scene_number=scene_number,
                            error=error,
                        )
                        errors.append(f"Scene {scene_number}: {error}")

            if errors:
                raise VideoAssemblyError(
                    message=f"Failed to create {len(errors)} scene video(s)",
                    stage="scene_video",
                )

        # Build ordered list of scene videos
        scene_videos = [
            scene_video_paths[scene.scene_number]
            for scene in script.scenes
            if scene.scene_number in scene_video_paths
        ]

        if not scene_videos:
            raise VideoAssemblyError(
                message="No scene videos to concatenate",
                stage="concatenation",
            )

        # Concatenate all scenes
        concat_output = videos_dir / f"concat_{platform.value}.mp4"
        self.concatenate_scenes(scene_videos, concat_output)

        # Add background music if provided
        final_filename = (
            f"{script.niche.value}_{script.safe_title}_{platform.value}.mp4"
        )
        final_output = output_dir / final_filename

        if music_path:
            self.add_background_music(
                video_path=concat_output,
                music_path=music_path,
                output_path=final_output,
            )
        else:
            # Just copy to final location
            shutil.copy2(concat_output, final_output)

        self.logger.info(
            "Video assembly complete",
            platform=platform.value,
            output=str(final_output),
        )

        return final_output

    def assemble_for_all_platforms(
        self,
        script: Script,
        platforms: list[Platform],
        checkpoint: Checkpoint | None = None,
        music_path: Path | None = None,
    ) -> dict[Platform, Path]:
        """
        Assemble videos for all platforms.

        Args:
            script: Script with generated images and audio
            platforms: List of target platforms
            checkpoint: Optional checkpoint for resume
            music_path: Optional background music

        Returns:
            Dict mapping platform to final video path
        """
        results: dict[Platform, Path] = {}

        for platform in platforms:
            self.logger.info(
                "Assembling video for platform",
                platform=platform.value,
            )

            try:
                path = self.assemble_video(
                    script=script,
                    platform=platform,
                    checkpoint=checkpoint,
                    music_path=music_path,
                )
                results[platform] = path
            except VideoAssemblyError as e:
                self.logger.error(
                    "Video assembly failed",
                    platform=platform.value,
                    error=str(e),
                )

        return results

    def get_video_duration(self, video_path: Path) -> float:
        """
        Get duration of a video file.

        Args:
            video_path: Path to video file

        Returns:
            Duration in seconds
        """
        try:
            # Use shell=True if ffprobe path wasn't resolved
            use_shell = self._ffprobe == "ffprobe"

            if use_shell:
                cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{video_path}"'
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    shell=True,
                )
            else:
                result = subprocess.run(
                    [
                        self._ffprobe,
                        "-v",
                        "error",
                        "-show_entries",
                        "format=duration",
                        "-of",
                        "default=noprint_wrappers=1:nokey=1",
                        str(video_path),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

            stdout = result.stdout.strip()
            if not stdout:
                return 0.0
            return float(stdout)
        except Exception as e:
            self.logger.warning(
                "Could not get video duration",
                path=str(video_path),
                error=str(e),
            )
            return 0.0

"""
Video assembly service for the Faceless Content Pipeline.

This service handles assembling final videos from generated images and audio,
using FFmpeg for video processing.
"""

import subprocess
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
        self._ffmpeg = self._settings.ffmpeg_path
        self._ffprobe = self._settings.ffprobe_path

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
        cmd = [self._ffmpeg] + args

        self.logger.debug(
            "Running FFmpeg",
            description=description,
            args_preview=" ".join(args[:5]),
        )

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
            )

            if result.returncode != 0:
                raise FFmpegError(
                    message=f"{description} failed",
                    command=cmd,
                    return_code=result.returncode,
                    stderr=result.stderr,
                )

            return result

        except subprocess.TimeoutExpired as e:
            raise FFmpegError(
                message=f"{description} timed out",
                command=cmd,
            ) from e
        except FileNotFoundError as e:
            raise FFmpegError(
                message="FFmpeg not found. Ensure it is installed and in PATH.",
                command=cmd,
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
        Assemble a complete video from a script.

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

        scene_videos: list[Path] = []

        # Create scene videos
        for scene in script.scenes:
            # Skip if already done
            if checkpoint and checkpoint.is_video_done(
                platform.value, scene.scene_number
            ):
                scene_video_path = (
                    videos_dir / f"scene_{scene.scene_number:02d}_{platform.value}.mp4"
                )
                if scene_video_path.exists():
                    self.logger.info(
                        "Skipping existing scene video",
                        scene_number=scene.scene_number,
                    )
                    scene_videos.append(scene_video_path)
                    continue

            scene_video_path = (
                videos_dir / f"scene_{scene.scene_number:02d}_{platform.value}.mp4"
            )

            self.create_scene_video(
                scene=scene,
                platform=platform,
                output_path=scene_video_path,
                enable_ken_burns=enable_ken_burns,
            )
            scene_videos.append(scene_video_path)

            if checkpoint:
                checkpoint.mark_video_done(platform.value, scene.scene_number)

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
            import shutil

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
            return float(result.stdout.strip())
        except Exception as e:
            self.logger.warning(
                "Could not get video duration",
                path=str(video_path),
                error=str(e),
            )
            return 0.0

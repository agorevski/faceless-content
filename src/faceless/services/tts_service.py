"""
Text-to-Speech service for the Faceless Content Pipeline.

This service handles generating audio narration for each scene in a script,
managing voice settings per niche and saving audio files.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from faceless.clients.azure_openai import AzureOpenAIClient
from faceless.config import get_settings
from faceless.core.enums import Niche, Voice
from faceless.core.exceptions import TTSGenerationError
from faceless.core.models import Checkpoint, Scene, Script
from faceless.utils.logging import LoggerMixin



class TTSService(LoggerMixin):
    """
    Service for generating text-to-speech audio.

    Handles:
    - Audio generation for each scene
    - Niche-specific voice settings
    - Checkpointing for resume support
    - Audio file management

    Example:
        >>> service = TTSService()
        >>> service.generate_for_script(script)
    """

    def __init__(self, client: AzureOpenAIClient | None = None) -> None:
        """
        Initialize TTS service.

        Args:
            client: Optional Azure OpenAI client (creates one if not provided)
        """
        self._client = client or AzureOpenAIClient()
        self._settings = get_settings()

    def generate_for_scene(
        self,
        scene: Scene,
        niche: Niche,
        output_dir: Path,
        voice: Voice | None = None,
        speed: float | None = None,
    ) -> Path:
        """
        Generate audio for a single scene.

        Args:
            scene: Scene with narration text
            niche: Content niche for voice settings
            output_dir: Directory to save audio
            voice: Optional voice override
            speed: Optional speed override

        Returns:
            Path to the generated audio file

        Raises:
            TTSGenerationError: On generation failure
        """
        # Get voice settings
        if voice is None or speed is None:
            default_voice, default_speed = self._settings.get_voice_settings(niche)
            voice = voice or default_voice
            speed = speed or default_speed

        # Generate filename
        filename = f"scene_{scene.scene_number:02d}.mp3"
        output_path = output_dir / filename

        self.logger.info(
            "Generating audio",
            scene_number=scene.scene_number,
            voice=voice.value,
            speed=speed,
            text_length=len(scene.narration),
        )

        try:
            self._client.save_audio(
                text=scene.narration,
                output_path=output_path,
                voice=voice,
                speed=speed,
            )
            scene.audio_path = output_path
            return output_path

        except Exception as e:
            raise TTSGenerationError(
                message=f"Failed to generate audio for scene {scene.scene_number}",
                text=scene.narration,
                voice=voice.value,
                api_error=str(e),
            ) from e

    def generate_for_script(
        self,
        script: Script,
        checkpoint: Checkpoint | None = None,
        voice: Voice | None = None,
        speed: float | None = None,
    ) -> list[Path]:
        """
        Generate audio for all scenes in a script using parallel processing.

        Generates up to MAX_CONCURRENT_TTS (5) audio files simultaneously.

        Args:
            script: Script with scenes
            checkpoint: Optional checkpoint for resume support
            voice: Optional voice override for all scenes
            speed: Optional speed override for all scenes

        Returns:
            List of paths to generated audio files

        Raises:
            TTSGenerationError: If any scene fails
        """
        output_dir = self._settings.get_audio_dir(script.niche) / script.safe_title
        output_dir.mkdir(parents=True, exist_ok=True)

        # Get voice settings
        if voice is None or speed is None:
            default_voice, default_speed = self._settings.get_voice_settings(script.niche)
            voice = voice or default_voice
            speed = speed or default_speed

        generated_paths: list[Path] = []
        errors: list[str] = []
        scenes_to_generate: list[Scene] = []

        # First pass: identify which scenes need generation
        for scene in script.scenes:
            # Skip if already done (checkpoint support)
            if checkpoint and checkpoint.is_audio_done(scene.scene_number):
                existing_path = output_dir / f"scene_{scene.scene_number:02d}.mp3"
                if existing_path.exists():
                    self.logger.info(
                        "Skipping existing audio",
                        scene_number=scene.scene_number,
                    )
                    scene.audio_path = existing_path
                    generated_paths.append(existing_path)
                    continue
            scenes_to_generate.append(scene)

        if not scenes_to_generate:
            self.logger.info("All audio already generated")
            return generated_paths

        max_concurrent = self._settings.max_concurrent_tts

        self.logger.info(
            "Starting parallel audio generation",
            scenes_to_generate=len(scenes_to_generate),
            max_concurrent=max_concurrent,
            voice=voice.value,
            speed=speed,
        )

        # Helper function for thread pool
        def generate_single_audio(
            scene_number: int,
            narration: str,
        ) -> tuple[int, Path | None, str | None]:
            """Generate audio for a single scene."""
            filename = f"scene_{scene_number:02d}.mp3"
            output_path = output_dir / filename

            self.logger.info(
                "Generating audio",
                scene_number=scene_number,
                voice=voice.value,
                speed=speed,
                text_length=len(narration),
            )

            try:
                self._client.save_audio(
                    text=narration,
                    output_path=output_path,
                    voice=voice,
                    speed=speed,
                )
                return (scene_number, output_path, None)
            except Exception as e:
                return (scene_number, None, str(e))

        # Generate audio in parallel
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            future_to_scene = {
                executor.submit(
                    generate_single_audio,
                    scene.scene_number,
                    scene.narration,
                ): scene
                for scene in scenes_to_generate
            }

            for future in as_completed(future_to_scene):
                original_scene = future_to_scene[future]
                scene_number, path, error = future.result()

                if path:
                    original_scene.audio_path = path
                    generated_paths.append(path)
                    if checkpoint:
                        checkpoint.mark_audio_done(scene_number)
                    self.logger.info(
                        "Audio generated",
                        scene_number=scene_number,
                        path=str(path),
                    )
                else:
                    self.logger.error(
                        "Scene audio generation failed",
                        scene_number=scene_number,
                        error=error,
                    )
                    errors.append(f"Scene {scene_number}: {error}")

        if errors:
            self.logger.warning(
                "Some audio failed to generate",
                failed_count=len(errors),
                total_scenes=len(script.scenes),
            )
        else:
            self.logger.info(
                "All audio generated successfully",
                total_generated=len(generated_paths),
            )

        return generated_paths

    def get_audio_duration(self, audio_path: Path) -> float:
        """
        Get duration of an audio file using ffprobe.

        Args:
            audio_path: Path to audio file

        Returns:
            Duration in seconds
        """
        import shutil
        import subprocess

        # Resolve ffprobe path (find in PATH if needed)
        ffprobe = self._settings.ffprobe_path
        use_shell = False
        
        if not (Path(ffprobe).is_absolute() or "/" in ffprobe or "\\" in ffprobe):
            resolved = shutil.which(ffprobe)
            if resolved:
                ffprobe = resolved
            else:
                # Fall back to shell=True on Windows
                use_shell = True

        try:
            if use_shell:
                # Use shell command for Windows compatibility
                cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{audio_path}"'
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
                        ffprobe,
                        "-v",
                        "error",
                        "-show_entries",
                        "format=duration",
                        "-of",
                        "default=noprint_wrappers=1:nokey=1",
                        str(audio_path),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            
            if result.returncode != 0:
                self.logger.warning(
                    "ffprobe failed",
                    path=str(audio_path),
                    stderr=result.stderr[:200] if result.stderr else None,
                )
                return 0.0
            
            stdout = result.stdout.strip()
            if not stdout:
                return 0.0
            return float(stdout)
        except Exception as e:
            self.logger.warning(
                "Could not get audio duration",
                path=str(audio_path),
                error=str(e),
            )
            return 0.0

    def update_scene_durations(self, script: Script) -> None:
        """
        Update scene duration estimates based on actual audio durations.

        Args:
            script: Script with audio_path set on scenes
        """
        for scene in script.scenes:
            if scene.audio_path and scene.audio_path.exists():
                duration = self.get_audio_duration(scene.audio_path)
                if duration > 0:
                    scene.duration_estimate = duration
                    self.logger.debug(
                        "Updated scene duration",
                        scene_number=scene.scene_number,
                        duration=duration,
                    )

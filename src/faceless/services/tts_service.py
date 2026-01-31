"""
Text-to-Speech service for the Faceless Content Pipeline.

This service handles generating audio narration for each scene in a script,
managing voice settings per niche and saving audio files.
"""

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
        Generate audio for all scenes in a script.

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

        generated_paths: list[Path] = []
        errors: list[str] = []

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

            try:
                path = self.generate_for_scene(
                    scene=scene,
                    niche=script.niche,
                    output_dir=output_dir,
                    voice=voice,
                    speed=speed,
                )
                generated_paths.append(path)

                # Update checkpoint
                if checkpoint:
                    checkpoint.mark_audio_done(scene.scene_number)

            except TTSGenerationError as e:
                self.logger.error(
                    "Scene audio generation failed",
                    scene_number=scene.scene_number,
                    error=str(e),
                )
                errors.append(f"Scene {scene.scene_number}: {e}")
                # Continue with remaining scenes

        if errors:
            self.logger.warning(
                "Some audio failed to generate",
                failed_count=len(errors),
                total_scenes=len(script.scenes),
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
        import subprocess

        try:
            result = subprocess.run(
                [
                    self._settings.ffprobe_path,
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
            return float(result.stdout.strip())
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

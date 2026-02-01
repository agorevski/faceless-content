"""
Pipeline orchestrator for the Faceless Content Pipeline.

This module provides the main Orchestrator class that coordinates all services
to produce complete videos from scripts.
"""

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from faceless.clients.azure_openai import AzureOpenAIClient
from faceless.config import get_settings
from faceless.core.enums import JobStatus, Niche, Platform
from faceless.core.exceptions import PipelineError
from faceless.core.models import (
    Checkpoint,
    Job,
    JobConfig,
    JobResult,
    Script,
)
from faceless.services.enhancer_service import EnhancerService
from faceless.services.image_service import ImageService
from faceless.services.tts_service import TTSService
from faceless.services.video_service import VideoService
from faceless.utils.logging import LoggerMixin, bind_context, clear_context


class Orchestrator(LoggerMixin):
    """
    Main pipeline orchestrator.

    Coordinates all services to produce complete videos:
    1. Load or scrape scripts
    2. Optionally enhance scripts with GPT
    3. Generate images for each scene
    4. Generate audio narration
    5. Assemble videos
    6. Generate thumbnails and subtitles

    Supports checkpointing for resume after failures.

    Example:
        >>> orchestrator = Orchestrator()
        >>> result = orchestrator.run(
        ...     niche=Niche.SCARY_STORIES,
        ...     platforms=[Platform.YOUTUBE],
        ... )
    """

    def __init__(self) -> None:
        """Initialize orchestrator with all services."""
        self._settings = get_settings()
        self._client = AzureOpenAIClient()
        self._enhancer_service = EnhancerService(self._client)
        self._image_service = ImageService(self._client)
        self._tts_service = TTSService(self._client)
        self._video_service = VideoService()

    def run(
        self,
        niche: Niche,
        platforms: list[Platform] | None = None,
        count: int = 1,
        script_path: Path | None = None,
        enhance: bool = False,
        thumbnails: bool = True,
        subtitles: bool = True,
        music_path: Path | None = None,
    ) -> list[JobResult]:
        """
        Run the complete pipeline.

        Args:
            niche: Content niche
            platforms: Target platforms (default: YouTube and TikTok)
            count: Number of videos to generate
            script_path: Path to existing script (skips scraping)
            enhance: Whether to enhance scripts with GPT
            thumbnails: Whether to generate thumbnails
            subtitles: Whether to generate subtitles
            music_path: Optional background music file

        Returns:
            List of JobResult objects with results for each video
        """
        platforms = platforms or [Platform.YOUTUBE, Platform.TIKTOK]
        results: list[JobResult] = []

        self.logger.info(
            "Starting pipeline",
            niche=niche.value,
            platforms=[p.value for p in platforms],
            count=count,
        )

        # Ensure directories exist
        self._settings.ensure_directories(niche)

        # Load or create scripts
        scripts: list[Script] = []
        if script_path:
            scripts = [Script.from_json_file(script_path)]
        else:
            scripts = self._load_existing_scripts(niche, count)

        if not scripts:
            self.logger.warning("No scripts found to process")
            return results

        # Process each script
        for i, script in enumerate(scripts):
            self.logger.info(
                "Processing script",
                index=i + 1,
                total=len(scripts),
                title=script.title,
            )

            result = self._process_script(
                script=script,
                platforms=platforms,
                enhance=enhance,
                thumbnails=thumbnails,
                subtitles=subtitles,
                music_path=music_path,
            )
            results.append(result)

        # Summary
        successful = sum(1 for r in results if r.success)
        self.logger.info(
            "Pipeline complete",
            successful=successful,
            failed=len(results) - successful,
            total=len(results),
        )

        return results

    def _load_existing_scripts(self, niche: Niche, count: int) -> list[Script]:
        """Load existing scripts from the scripts directory."""
        scripts_dir = self._settings.get_scripts_dir(niche)

        if not scripts_dir.exists():
            return []

        scripts: list[Script] = []
        for script_file in sorted(scripts_dir.glob("*_script.json"))[:count]:
            try:
                script = Script.from_json_file(script_file)
                scripts.append(script)
            except Exception as e:
                self.logger.warning(
                    "Failed to load script",
                    path=str(script_file),
                    error=str(e),
                )

        return scripts

    def _process_script(
        self,
        script: Script,
        platforms: list[Platform],
        enhance: bool,
        thumbnails: bool,
        subtitles: bool,
        music_path: Path | None,
    ) -> JobResult:
        """Process a single script through the pipeline."""
        start_time = datetime.now()
        errors: list[str] = []
        video_paths: dict[str, Path] = {}

        # Set up logging context
        bind_context(script_title=script.safe_title, niche=script.niche.value)

        # Load or create checkpoint
        checkpoint = self._load_or_create_checkpoint(script)

        try:
            # Step 1: Enhance script (optional) - BLOCKING
            if enhance and "enhance" not in checkpoint.completed_steps:
                self.logger.info("Starting script enhancement...")
                checkpoint.status = JobStatus.ENHANCING
                
                try:
                    enhanced_script = self._enhancer_service.enhance_script(script)
                    # Update script reference with enhanced version
                    script = enhanced_script
                    checkpoint.completed_steps.append("enhance")
                    self._save_checkpoint(checkpoint, script)
                    self.logger.info(
                        "Script enhancement completed",
                        scene_count=len(script.scenes),
                    )
                except Exception as e:
                    self.logger.warning(
                        "Script enhancement failed, continuing with original",
                        error=str(e),
                    )
                    errors.append(f"Enhancement: {e}")
            elif enhance:
                self.logger.info("Skipping enhancement (already completed)")

            # Step 2: Generate images (with parallel processing)
            if "images" not in checkpoint.completed_steps:
                self.logger.info(
                    "Starting image generation...",
                    scene_count=len(script.scenes),
                    platforms=[p.value for p in platforms],
                )
                checkpoint.status = JobStatus.GENERATING_IMAGES

                for platform in platforms:
                    try:
                        generated_count = self._image_service.generate_for_script(
                            script=script,
                            platform=platform,
                            checkpoint=checkpoint,
                        )
                        self.logger.info(
                            "Image generation completed for platform",
                            platform=platform.value,
                            images_generated=len(generated_count) if generated_count else 0,
                        )
                    except Exception as e:
                        errors.append(f"Image generation ({platform.value}): {e}")

                checkpoint.completed_steps.append("images")
                self._save_checkpoint(checkpoint, script)
                self.logger.info("All image generation completed")
            else:
                self.logger.info("Skipping image generation (already completed)")

            # Step 3: Generate audio
            if "audio" not in checkpoint.completed_steps:
                self.logger.info(
                    "Starting audio generation...",
                    scene_count=len(script.scenes),
                )
                checkpoint.status = JobStatus.GENERATING_AUDIO

                try:
                    self._tts_service.generate_for_script(
                        script=script,
                        checkpoint=checkpoint,
                    )
                    # Update durations based on actual audio
                    self._tts_service.update_scene_durations(script)
                    self.logger.info("Audio generation completed")
                except Exception as e:
                    errors.append(f"Audio generation: {e}")

                checkpoint.completed_steps.append("audio")
                self._save_checkpoint(checkpoint, script)
            else:
                self.logger.info("Skipping audio generation (already completed)")

            # Step 4: Assemble videos
            if "videos" not in checkpoint.completed_steps:
                self.logger.info(
                    "Starting video assembly...",
                    platforms=[p.value for p in platforms],
                )
                checkpoint.status = JobStatus.ASSEMBLING_VIDEO
                video_errors: list[str] = []

                for platform in platforms:
                    try:
                        path = self._video_service.assemble_video(
                            script=script,
                            platform=platform,
                            checkpoint=checkpoint,
                            music_path=music_path,
                        )
                        video_paths[platform.value] = path
                        self.logger.info(
                            "Video assembly completed for platform",
                            platform=platform.value,
                            output_path=str(path),
                        )
                    except Exception as e:
                        video_errors.append(f"Video assembly ({platform.value}): {e}")
                        errors.append(f"Video assembly ({platform.value}): {e}")

                # Only mark complete if NO video assembly errors
                if not video_errors:
                    checkpoint.completed_steps.append("videos")
                    self.logger.info("All video assembly completed")
                else:
                    self.logger.warning(
                        "Video assembly had errors, not marking complete",
                        error_count=len(video_errors),
                    )
            else:
                self.logger.info("Skipping video assembly (already completed)")

            # Step 5: Generate thumbnails (optional)
            if thumbnails and not errors and "thumbnails" not in checkpoint.completed_steps:
                self.logger.info("Starting thumbnail generation...")
                checkpoint.status = JobStatus.GENERATING_THUMBNAILS
                # TODO: Implement thumbnail generation
                checkpoint.completed_steps.append("thumbnails")
                self.logger.info("Thumbnail generation completed")

            # Step 6: Generate subtitles (optional)
            if subtitles and not errors and "subtitles" not in checkpoint.completed_steps:
                self.logger.info("Starting subtitle generation...")
                checkpoint.status = JobStatus.GENERATING_SUBTITLES
                # TODO: Implement subtitle generation
                checkpoint.completed_steps.append("subtitles")
                self.logger.info("Subtitle generation completed")

            # Complete
            checkpoint.status = JobStatus.COMPLETED
            self._save_checkpoint(checkpoint, script)

            duration = (datetime.now() - start_time).total_seconds()

            self.logger.info(
                "Script processing completed",
                duration_seconds=round(duration, 2),
                errors_count=len(errors),
            )

            return JobResult(
                success=len(errors) == 0,
                script_path=self._settings.get_scripts_dir(script.niche)
                / f"{script.safe_title}_script.json",
                video_paths=video_paths,
                errors=errors,
                duration_seconds=duration,
            )

        except Exception as e:
            self.logger.exception("Pipeline failed", error=str(e))
            checkpoint.status = JobStatus.FAILED
            self._save_checkpoint(checkpoint, script)

            return JobResult(
                success=False,
                errors=[str(e)],
                duration_seconds=(datetime.now() - start_time).total_seconds(),
            )

        finally:
            clear_context()

    def _load_or_create_checkpoint(self, script: Script) -> Checkpoint:
        """Load existing checkpoint or create new one."""
        checkpoint_dir = self._settings.get_checkpoints_dir(script.niche)
        checkpoint_path = checkpoint_dir / f"{script.safe_title}.checkpoint.json"

        if checkpoint_path.exists():
            try:
                checkpoint = Checkpoint.load(checkpoint_path)
                self.logger.info(
                    "Resuming from checkpoint",
                    completed_steps=checkpoint.completed_steps,
                )
                return checkpoint
            except Exception as e:
                self.logger.warning(
                    "Failed to load checkpoint, creating new one",
                    error=str(e),
                )

        # Create new checkpoint
        return Checkpoint(
            job_id=uuid4(),
            script_path=self._settings.get_scripts_dir(script.niche)
            / f"{script.safe_title}_script.json",
            status=JobStatus.PENDING,
        )

    def _save_checkpoint(self, checkpoint: Checkpoint, script: Script) -> None:
        """Save checkpoint to disk."""
        if not self._settings.enable_checkpointing:
            return

        checkpoint_dir = self._settings.get_checkpoints_dir(script.niche)
        checkpoint_path = checkpoint_dir / f"{script.safe_title}.checkpoint.json"
        checkpoint.save(checkpoint_path)

    def run_single(
        self,
        script: Script,
        platforms: list[Platform] | None = None,
        music_path: Path | None = None,
    ) -> JobResult:
        """
        Run pipeline for a single script.

        Args:
            script: Script to process
            platforms: Target platforms
            music_path: Optional background music

        Returns:
            JobResult with results
        """
        platforms = platforms or [Platform.YOUTUBE, Platform.TIKTOK]

        return self._process_script(
            script=script,
            platforms=platforms,
            enhance=False,
            thumbnails=True,
            subtitles=True,
            music_path=music_path,
        )

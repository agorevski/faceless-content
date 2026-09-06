"""
Pipeline orchestrator for the Faceless Content Pipeline.

This module provides the main Orchestrator class that coordinates all services
to produce complete videos from scripts.
"""

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from faceless.clients.azure_openai import AzureOpenAIClient
from faceless.config import get_settings
from faceless.core.enums import JobStatus, Niche, Platform
from faceless.core.exceptions import CheckpointError, FacelessError, PipelineError
from faceless.core.models import (
    Checkpoint,
    JobResult,
    Script,
)
from faceless.services.enhancer_service import EnhancerService
from faceless.services.image_service import ImageService
from faceless.services.subtitle_service import create_subtitles_from_script
from faceless.services.thumbnail_service import generate_thumbnail_variants
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
        thumbnail_paths: list[Path] = []
        subtitle_paths: dict[str, Path] = {}
        production_path: Path | None = None

        # Set up logging context
        bind_context(script_title=script.safe_title, niche=script.niche.value)

        checkpoint: Checkpoint | None = None

        try:
            checkpoint = self._load_or_create_checkpoint(script)
            # Step 1: Enhance script (optional) - BLOCKING
            if "enhance" in checkpoint.completed_steps:
                if checkpoint.enhanced_script is None:
                    raise CheckpointError(
                        "Completed enhancement has no script snapshot; "
                        "cannot safely resume existing assets"
                    )
                if checkpoint.enhanced_script.niche != script.niche:
                    raise CheckpointError("Enhanced script snapshot has a different niche")
                script = checkpoint.enhanced_script.model_copy(deep=True)
                self.logger.info("Restored enhanced script from checkpoint")
            elif checkpoint.enhanced_script is not None:
                raise CheckpointError("Enhanced script snapshot has no completion marker")
            elif enhance:
                self.logger.info("Starting script enhancement...")
                checkpoint.status = JobStatus.ENHANCING

                enhanced_script = self._enhancer_service.enhance_script(
                    script.model_copy(deep=True)
                )
                if enhanced_script.niche != script.niche:
                    raise PipelineError("Enhancement cannot change the script niche")
                script = Script.model_validate(enhanced_script.model_dump())
                # A newly enhanced script must not reuse the original script's assets.
                checkpoint.completed_steps = ["enhance"]
                checkpoint.images_generated.clear()
                checkpoint.audio_generated.clear()
                checkpoint.videos_generated.clear()
                checkpoint.enhanced_script = script.model_copy(deep=True)
                self._save_checkpoint(checkpoint, script)
                self.logger.info(
                    "Script enhancement completed",
                    scene_count=len(script.scenes),
                )
            bind_context(script_title=script.safe_title)

            # Services restore scene paths from cached files and retry missing assets.
            checkpoint.status = JobStatus.GENERATING_IMAGES
            if "images" in checkpoint.completed_steps:
                checkpoint.completed_steps.remove("images")
            platform_images: dict[Platform, list[Path | None]] = {}

            for platform in platforms:
                try:
                    generated_paths = self._image_service.generate_for_script(
                        script=script,
                        platform=platform,
                        checkpoint=checkpoint,
                    )
                    if len(generated_paths) != len(script.scenes):
                        raise PipelineError(
                            f"Expected {len(script.scenes)} images, "
                            f"received {len(generated_paths)}"
                        )
                    platform_images[platform] = [
                        scene.image_path for scene in script.scenes
                    ]
                    self.logger.info(
                        "Image generation completed for platform",
                        platform=platform.value,
                        images_generated=len(generated_paths),
                    )
                except Exception as e:
                    errors.append(f"Image generation ({platform.value}): {e}")

            if len(platform_images) == len(set(platforms)):
                checkpoint.completed_steps.append("images")
            self._save_checkpoint(checkpoint, script)

            # Step 3: Generate or restore audio, including measured durations.
            checkpoint.status = JobStatus.GENERATING_AUDIO
            if "audio" in checkpoint.completed_steps:
                checkpoint.completed_steps.remove("audio")
            audio_ready = False
            try:
                audio_paths = self._tts_service.generate_for_script(
                    script=script,
                    checkpoint=checkpoint,
                )
                if len(audio_paths) != len(script.scenes):
                    raise PipelineError(
                        f"Expected {len(script.scenes)} audio files, "
                        f"received {len(audio_paths)}"
                    )
                self._tts_service.update_scene_durations(script)
                audio_ready = True
                checkpoint.completed_steps.append("audio")
                self.logger.info("Audio generation completed")
            except Exception as e:
                errors.append(f"Audio generation: {e}")
            self._save_checkpoint(checkpoint, script)

            # Step 4: Assemble videos
            videos_completed = "videos" in checkpoint.completed_steps
            if videos_completed:
                checkpoint.completed_steps.remove("videos")
            if audio_ready:
                self.logger.info(
                    "Starting video assembly...",
                    platforms=[p.value for p in platforms],
                )
                checkpoint.status = JobStatus.ASSEMBLING_VIDEO
                video_errors: list[str] = []

                for platform in platforms:
                    if platform not in platform_images:
                        continue
                    try:
                        for scene, image_path in zip(
                            script.scenes, platform_images[platform], strict=True
                        ):
                            scene.image_path = image_path
                        existing_output = (
                            self._settings.get_final_output_dir(script.niche)
                            / f"{script.niche.value}_{script.safe_title}_{platform.value}.mp4"
                        )
                        if videos_completed and existing_output.is_file():
                            video_paths[platform.value] = existing_output
                            continue
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
                if not video_errors and len(video_paths) == len(set(platforms)):
                    checkpoint.completed_steps.append("videos")
                    self.logger.info("All video assembly completed")
                else:
                    self.logger.warning(
                        "Video assembly had errors, not marking complete",
                        error_count=len(video_errors),
                    )
            else:
                self.logger.warning("Skipping video assembly: audio is incomplete")

            if video_paths:
                script.output_paths = video_paths.copy()
                candidate_path = (
                    self._settings.get_final_output_dir(script.niche)
                    / f"{script.safe_title}_script.json"
                )
                try:
                    script.to_json_file(candidate_path)
                    production_path = candidate_path
                except (OSError, ValueError) as e:
                    self.logger.error("Production script could not be saved", error=str(e))
                    errors.append(f"Production script: {e}")

            # Step 5: Reuse existing thumbnails and retry missing variants.
            if thumbnails and video_paths:
                if "thumbnails" in checkpoint.completed_steps:
                    checkpoint.completed_steps.remove("thumbnails")
                self.logger.info("Starting thumbnail generation...")
                checkpoint.status = JobStatus.GENERATING_THUMBNAILS
                try:
                    variant_count = 3
                    generated_thumbnails = generate_thumbnail_variants(
                        title=script.title,
                        niche=script.niche.value,
                        base_name=script.safe_title,
                        output_dir=(
                            self._settings.get_images_dir(script.niche)
                            / script.safe_title / "thumbnails"
                        ),
                        num_variants=variant_count,
                        client=self._client,
                    )
                    thumbnail_paths = [
                        path for path in generated_thumbnails
                        if path is not None and path.is_file() and path.stat().st_size > 0
                    ]
                    if len(set(thumbnail_paths)) != variant_count:
                        raise PipelineError(
                            f"Expected {variant_count} thumbnails, "
                            f"generated {len(set(thumbnail_paths))}"
                        )
                    checkpoint.completed_steps.append("thumbnails")
                    self.logger.info("Thumbnail generation completed")
                except (FacelessError, OSError, ValueError) as e:
                    self.logger.error("Thumbnail generation failed", error=str(e))
                    errors.append(f"Thumbnail generation: {e}")
                self._save_checkpoint(checkpoint, script)

            # Step 6: Use measured narration durations, independent of thumbnail success.
            if subtitles and video_paths:
                if "subtitles" in checkpoint.completed_steps:
                    checkpoint.completed_steps.remove("subtitles")
                self.logger.info("Starting subtitle generation...")
                checkpoint.status = JobStatus.GENERATING_SUBTITLES
                try:
                    if production_path is None:
                        raise PipelineError("Cannot create subtitles without the production script")
                    srt_path, vtt_path = create_subtitles_from_script(
                        production_path,
                        script.niche.value,
                        output_dir=(
                            self._settings.get_audio_dir(script.niche) / script.safe_title
                        ),
                    )
                    if not all(
                        path.is_file() and path.stat().st_size > 0
                        for path in (srt_path, vtt_path)
                    ):
                        raise PipelineError("Subtitle generation did not create both SRT and VTT files")
                    subtitle_paths = {"srt": srt_path, "vtt": vtt_path}
                    checkpoint.completed_steps.append("subtitles")
                    self.logger.info("Subtitle generation completed")
                except (FacelessError, OSError, ValueError) as e:
                    self.logger.error("Subtitle generation failed", error=str(e))
                    errors.append(f"Subtitle generation: {e}")
                self._save_checkpoint(checkpoint, script)

            # Complete
            checkpoint.status = JobStatus.FAILED if errors else JobStatus.COMPLETED
            self._save_checkpoint(checkpoint, script)

            duration = (datetime.now() - start_time).total_seconds()

            self.logger.info(
                "Script processing completed",
                duration_seconds=round(duration, 2),
                errors_count=len(errors),
            )

            return JobResult(
                success=len(errors) == 0,
                script_path=production_path or checkpoint.script_path,
                video_paths=video_paths,
                thumbnail_paths=thumbnail_paths,
                subtitle_paths=subtitle_paths,
                errors=errors,
                duration_seconds=duration,
            )

        except Exception as e:
            self.logger.exception("Pipeline failed", error=str(e))
            if checkpoint is not None:
                checkpoint.status = JobStatus.FAILED
                try:
                    self._save_checkpoint(checkpoint, script)
                except CheckpointError as checkpoint_error:
                    self.logger.error(
                        "Failed to save failed checkpoint", error=str(checkpoint_error)
                    )

            return JobResult(
                success=False,
                script_path=production_path,
                video_paths=video_paths,
                thumbnail_paths=thumbnail_paths,
                subtitle_paths=subtitle_paths,
                errors=[*errors, str(e)],
                duration_seconds=(datetime.now() - start_time).total_seconds(),
            )

        finally:
            clear_context()

    def _load_or_create_checkpoint(self, script: Script) -> Checkpoint:
        """Load existing checkpoint or create new one."""
        checkpoint_dir = self._settings.get_checkpoints_dir(script.niche)
        checkpoint_path = checkpoint_dir / f"{script.safe_title}.checkpoint.json"
        script_path = (
            self._settings.get_scripts_dir(script.niche)
            / f"{script.safe_title}_script.json"
        )

        if self._settings.enable_checkpointing and not checkpoint_path.exists():
            # Older runs saved under the enhanced title but retained the source path.
            matches: list[Path] = []
            for candidate in checkpoint_dir.glob("*.checkpoint.json"):
                try:
                    data = json.loads(candidate.read_text(encoding="utf-8"))
                except (OSError, ValueError) as e:
                    self.logger.warning(
                        "Skipping unreadable legacy checkpoint",
                        path=str(candidate),
                        error=str(e),
                    )
                    continue
                if (
                    isinstance(data, dict)
                    and isinstance(data.get("script_path"), str)
                    and Path(data["script_path"]) == script_path
                ):
                    matches.append(candidate)
            if len(matches) > 1:
                raise CheckpointError(
                    "Multiple checkpoints refer to the original script; "
                    "cannot safely select an enhanced script snapshot"
                )
            if matches:
                checkpoint_path = matches[0]

        if self._settings.enable_checkpointing and checkpoint_path.exists():
            try:
                checkpoint = Checkpoint.load(checkpoint_path)
                self.logger.info(
                    "Resuming from checkpoint",
                    completed_steps=checkpoint.completed_steps,
                )
                return checkpoint
            except (OSError, ValueError) as e:
                raise CheckpointError(
                    "Cannot load checkpoint or enhanced script snapshot",
                    checkpoint_path=str(checkpoint_path),
                ) from e

        # Create new checkpoint
        return Checkpoint(
            job_id=uuid4(),
            script_path=script_path,
            status=JobStatus.PENDING,
        )

    def _save_checkpoint(self, checkpoint: Checkpoint, script: Script) -> None:
        """Atomically save progress and its snapshot under the original identity."""
        if not self._settings.enable_checkpointing:
            return

        checkpoint_dir = self._settings.get_checkpoints_dir(script.niche)
        original_title = checkpoint.script_path.stem.removesuffix("_script")
        checkpoint_path = checkpoint_dir / f"{original_title}.checkpoint.json"
        pending_path = checkpoint_path.with_name(
            f"{checkpoint_path.name}.{uuid4().hex}.pending"
        )
        try:
            checkpoint.save(pending_path)
            pending_path.replace(checkpoint_path)
        except (OSError, ValueError) as e:
            raise CheckpointError(
                "Cannot persist checkpoint and enhanced script snapshot",
                checkpoint_path=str(checkpoint_path),
            ) from e
        finally:
            try:
                pending_path.unlink(missing_ok=True)
            except OSError as e:
                self.logger.warning(
                    "Could not remove pending checkpoint",
                    path=str(pending_path),
                    error=str(e),
                )

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

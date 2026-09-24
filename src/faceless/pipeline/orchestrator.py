"""
Pipeline orchestrator for the Faceless Content Pipeline.

This module provides the main Orchestrator class that coordinates all services
to produce complete videos from scripts.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from faceless.clients.azure_openai import AzureOpenAIClient
from faceless.config import get_settings
from faceless.core.enums import JobStatus, Niche, Platform
from faceless.core.exceptions import (
    CheckpointError,
    FacelessError,
    ImageGenerationError,
    PipelineError,
)
from faceless.core.models import (
    Checkpoint,
    JobResult,
    Scene,
    Script,
)
from faceless.services.enhancer_service import EnhancerService
from faceless.services.image_service import ImageService
from faceless.services.quality_service import QualityService
from faceless.services.subtitle_service import (
    burn_subtitles_to_video,
    create_subtitles_from_script,
    portrait_caption_style,
)
from faceless.services.thumbnail_service import generate_thumbnail_variants
from faceless.services.tts_service import TTSService
from faceless.services.video_service import VideoService
from faceless.utils.logging import LoggerMixin, bind_context, clear_context

MAX_QUALITY_REVISIONS = 2


class Orchestrator(LoggerMixin):
    """
    Main pipeline orchestrator.

    Coordinates all services to produce complete videos:
    1. Load or scrape scripts
    2. Enhance scripts with GPT (unless explicitly disabled)
    3. Approve script quality before generating media
    4. Generate images and audio for each scene
    5. Assemble videos and generate thumbnails and subtitles

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
        self._quality_service = QualityService(self._client)
        self._image_service = ImageService(self._client)
        self._tts_service = TTSService(self._client)
        self._video_service = VideoService()

    def run(
        self,
        niche: Niche,
        platforms: list[Platform] | None = None,
        count: int = 1,
        script_path: Path | None = None,
        enhance: bool = True,
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
            enhance: Whether to enhance scripts with GPT (paid, enabled by default)
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
                source_path=script_path,
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
        source_path: Path | None = None,
    ) -> JobResult:
        """Process a single script through the pipeline."""
        start_time = datetime.now()
        source_script = script.model_copy(deep=True)
        script = source_script.model_copy(deep=True)
        stage = "Checkpoint"
        stage_errors: list[str] = []

        # Set up logging context
        bind_context(script_title=source_script.safe_title, niche=script.niche.value)
        checkpoint: Checkpoint | None = None
        result = JobResult(success=False, script_path=source_path)

        try:
            loaded_checkpoint = self._load_or_create_checkpoint(
                source_script, source_path
            )
            stage = "Source checkpoint validation"
            self._verify_source_fingerprint(source_script, loaded_checkpoint)
            checkpoint = loaded_checkpoint
            result = self._load_progress(source_script, result)
            result.success = False
            result.errors = []

            stage = "Checkpoint compatibility"
            if (
                enhance
                and "quality" in checkpoint.completed_steps
                and "enhance" not in checkpoint.completed_steps
            ):
                raise PipelineError(
                    "Checkpoint claims quality approval without enhancement. "
                    "Start a new job without the existing checkpoint."
                )
            if "enhance" in checkpoint.completed_steps and not enhance:
                raise PipelineError(
                    "This checkpoint uses an enhanced script; to use --no-enhance, "
                    "start a new job without the existing checkpoint."
                )
            if enhance and "enhance" not in checkpoint.completed_steps:
                if any(
                    step in checkpoint.completed_steps
                    for step in ("images", "audio", "videos")
                ):
                    raise PipelineError(
                        "Existing media predates enhancement. Start a new job "
                        "without the existing checkpoint."
                    )
                stage = "Script enhancement"
                checkpoint.status = JobStatus.ENHANCING
                original = script
                script = self._enhancer_service.enhance_script(script)
                if not isinstance(script, Script) or script is original:
                    raise PipelineError("Enhancement did not return an enhanced script")
                checkpoint.enhanced_script = script.model_copy(deep=True)
                self._persist_script(script, source_script, checkpoint, source_path)
                result.script_path = checkpoint.script_path
                checkpoint.completed_steps.append("enhance")
                self._save_progress(checkpoint, source_script, result)
            elif "enhance" in checkpoint.completed_steps or (
                "quality" in checkpoint.completed_steps
            ):
                stage = "Production script recovery"
                if (
                    not checkpoint.script_path.exists()
                    or not checkpoint.script_path.name.endswith("_production.json")
                ):
                    raise PipelineError(
                        "Approved production script is missing; cannot resume. "
                        "Start a new job without the existing checkpoint."
                    )
                script = Script.from_json_file(checkpoint.script_path)
                if script.niche != source_script.niche:
                    raise PipelineError(
                        "Production script niche differs from the original source"
                    )
                if checkpoint.enhanced_script is not None and (
                    script.title != checkpoint.enhanced_script.title
                    or len(script.scenes) != len(checkpoint.enhanced_script.scenes)
                    or any(
                        scene.narration != approved.narration
                        or scene.image_prompt != approved.image_prompt
                        for scene, approved in zip(
                            script.scenes,
                            checkpoint.enhanced_script.scenes,
                            strict=True,
                        )
                    )
                ):
                    raise PipelineError(
                        "Production script differs from the approved enhancement snapshot"
                    )
                result.script_path = checkpoint.script_path

            stage = "Script quality"
            if "quality" not in checkpoint.completed_steps:
                revisions = 0
                while True:
                    score = self._quality_service.evaluate_script(
                        script, strict_mode=True
                    )
                    if score.hook_analysis is None:
                        raise PipelineError(
                            "Quality assessment unavailable (no AI hook analysis). "
                            "Check the AI response and retry before generating media."
                        )
                    if score.approved_for_production and score.hook_score >= 7.0:
                        break

                    details = (
                        score.critical_issues
                        + score.improvements
                        + score.hook_analysis.improvement_suggestions
                    )
                    if (
                        enhance
                        and not score.critical_issues
                        and revisions < MAX_QUALITY_REVISIONS
                    ):
                        feedback = [
                            f"Hook scored {score.hook_score:.1f}/10 (minimum 7.0)",
                            *(
                                f"Address failed gate: {gate.value}"
                                for gate in score.gates_failed
                            ),
                            *score.improvements,
                            *score.hook_analysis.improvement_suggestions,
                        ]
                        stage = "Script revision"
                        script = self._enhancer_service.enhance_script(
                            script, feedback=[item[:300] for item in feedback[:12]]
                        )
                        if not isinstance(script, Script):
                            raise PipelineError(
                                "Script revision returned no valid script"
                            )
                        checkpoint.enhanced_script = script.model_copy(deep=True)
                        self._persist_script(
                            script, source_script, checkpoint, source_path
                        )
                        result.script_path = checkpoint.script_path
                        self._save_progress(checkpoint, source_script, result)
                        revisions += 1
                        stage = "Script quality"
                        continue

                    failed_gates = ", ".join(gate.value for gate in score.gates_failed)
                    raise PipelineError(
                        f"Script rejected by quality gate (hook {score.hook_score:.1f}/10; "
                        f"minimum 7.0; overall {score.overall_score:.1f}/10; "
                        f"failed gates: {failed_gates or 'approval criteria'}; "
                        f"revisions: {revisions}/{MAX_QUALITY_REVISIONS}). "
                        "Review the script before production."
                        + (f" Suggestions: {'; '.join(details)}" if details else "")
                    )
                if result.script_path is None or result.script_path == source_path:
                    self._persist_script(script, source_script, checkpoint, source_path)
                    result.script_path = checkpoint.script_path
                checkpoint.completed_steps.append("quality")
                self._save_progress(checkpoint, source_script, result)

            stage = "Image generation"
            checkpoint.status = JobStatus.GENERATING_IMAGES
            image_errors: list[str] = []
            ready_platforms: list[Platform] = []
            changed_images: set[Platform] = set()
            for platform in platforms:
                expected = {
                    scene.scene_number: self._scene_image_path(script, scene, platform)
                    for scene in script.scenes
                }
                if "images" in checkpoint.completed_steps and all(
                    path.is_file() for path in expected.values()
                ):
                    ready_platforms.append(platform)
                    continue
                try:
                    paths = self._image_service.generate_for_script(
                        script=script, platform=platform, checkpoint=checkpoint
                    )
                    if (
                        len(paths) != len(script.scenes)
                        or set(paths) != set(expected.values())
                        or any(
                            scene.image_path != expected[scene.scene_number]
                            for scene in script.scenes
                        )
                        or any(not path.exists() for path in expected.values())
                    ):
                        raise PipelineError(
                            f"Incomplete image generation for {platform.value}: "
                            f"{len(paths)}/{len(script.scenes)} paths returned; "
                            "verify every scene has an image for this platform"
                        )
                except ImageGenerationError as error:
                    self.logger.error(
                        "Image generation failed for platform",
                        platform=platform.value,
                        error=str(error),
                    )
                    image_errors.append(f"Image generation ({platform.value}): {error}")
                    stage_errors.append(image_errors[-1])
                    continue
                ready_platforms.append(platform)
                changed_images.add(platform)
                checkpoint.videos_generated.pop(platform.value, None)
                result.video_paths.pop(platform.value, None)
            if not ready_platforms:
                raise PipelineError(
                    "; ".join(image_errors) or "No platform images are ready"
                )
            if len(ready_platforms) == len(set(platforms)):
                if "images" not in checkpoint.completed_steps:
                    checkpoint.completed_steps.append("images")
            elif "images" in checkpoint.completed_steps:
                checkpoint.completed_steps.remove("images")
            self._save_progress(checkpoint, source_script, result)

            audio_missing = any(
                scene.audio_path is None or not scene.audio_path.is_file()
                for scene in script.scenes
            )
            audio_changed = "audio" not in checkpoint.completed_steps or audio_missing
            if audio_changed:
                stage = "Audio generation"
                checkpoint.status = JobStatus.GENERATING_AUDIO
                paths = self._tts_service.generate_for_script(
                    script=script, checkpoint=checkpoint
                )
                if (
                    len(paths) != len(script.scenes)
                    or len(set(paths)) != len(script.scenes)
                    or any(
                        scene.audio_path is None
                        or not scene.audio_path.exists()
                        or scene.audio_path not in paths
                        for scene in script.scenes
                    )
                ):
                    raise PipelineError(
                        f"Incomplete audio generation: "
                        f"{len(paths)}/{len(script.scenes)} paths returned; "
                        "verify every scene has an audio file"
                    )
                self._tts_service.update_scene_durations(script)
                if enhance:
                    checkpoint.enhanced_script = script.model_copy(deep=True)
                self._persist_script(script, source_script, checkpoint, source_path)
                result.script_path = checkpoint.script_path
                if "audio" not in checkpoint.completed_steps:
                    checkpoint.completed_steps.append("audio")
                checkpoint.videos_generated.clear()
                for platform in platforms:
                    result.video_paths.pop(platform.value, None)
                self._save_progress(checkpoint, source_script, result)

            stage = "Video assembly"
            checkpoint.status = JobStatus.ASSEMBLING_VIDEO
            video_errors: list[str] = []
            for platform in ready_platforms:
                existing = result.video_paths.get(platform.value)
                if (
                    platform not in changed_images
                    and not audio_changed
                    and existing is not None
                    and existing.is_file()
                ):
                    continue
                try:
                    for scene in script.scenes:
                        scene.image_path = self._scene_image_path(
                            script, scene, platform
                        )
                    path = self._video_service.assemble_video(
                        script=script,
                        platform=platform,
                        checkpoint=checkpoint,
                        music_path=music_path,
                    )
                    if not path.is_file():
                        raise PipelineError(
                            f"Video output missing for {platform.value}: {path}"
                        )
                    result.video_paths[platform.value] = path
                except (FacelessError, OSError) as error:
                    self.logger.error(
                        "Video assembly failed for platform",
                        platform=platform.value,
                        error=str(error),
                    )
                    video_errors.append(f"Video assembly ({platform.value}): {error}")
                    stage_errors.append(video_errors[-1])
                else:
                    self._save_progress(checkpoint, source_script, result)
            if len(result.video_paths) == len(set(platforms)) and not video_errors:
                if "videos" not in checkpoint.completed_steps:
                    checkpoint.completed_steps.append("videos")
            elif "videos" in checkpoint.completed_steps:
                checkpoint.completed_steps.remove("videos")
            self._save_progress(checkpoint, source_script, result)
            if not result.video_paths:
                raise PipelineError(
                    "; ".join(video_errors) or "No platform videos are ready"
                )
            if (
                audio_changed
                or Platform.TIKTOK in changed_images
                or Platform.TIKTOK.value not in result.video_paths
                or not result.video_paths[Platform.TIKTOK.value].stem.endswith(
                    "_captioned"
                )
            ) and "captions" in checkpoint.completed_steps:
                checkpoint.completed_steps.remove("captions")

            script.output_paths = result.video_paths.copy()
            self._persist_script(script, source_script, checkpoint, source_path)
            result.script_path = checkpoint.script_path

            subtitle_missing = any(
                kind not in result.subtitle_paths
                or not result.subtitle_paths[kind].is_file()
                or result.subtitle_paths[kind].stat().st_size == 0
                for kind in ("srt", "vtt")
            )
            if subtitles and (
                audio_changed
                or subtitle_missing
                or "subtitles" not in checkpoint.completed_steps
            ):
                stage = "Subtitle generation"
                checkpoint.status = JobStatus.GENERATING_SUBTITLES
                try:
                    if result.script_path is None:
                        raise PipelineError(
                            "Production script is missing for subtitles"
                        )
                    srt_path, vtt_path = create_subtitles_from_script(
                        script_path=result.script_path,
                        niche=script.niche.value,
                        output_dir=self._settings.get_audio_dir(script.niche),
                    )
                    if not all(
                        path.is_file() and path.stat().st_size > 0
                        for path in (srt_path, vtt_path)
                    ):
                        raise PipelineError("Subtitle output files were not created")
                    result.subtitle_paths = {"srt": srt_path, "vtt": vtt_path}
                    if "subtitles" not in checkpoint.completed_steps:
                        checkpoint.completed_steps.append("subtitles")
                    if "captions" in checkpoint.completed_steps:
                        checkpoint.completed_steps.remove("captions")
                        captioned = result.video_paths.get(Platform.TIKTOK.value)
                        if captioned is not None and captioned.stem.endswith(
                            "_captioned"
                        ):
                            raw_video = captioned.with_name(
                                f"{captioned.stem.removesuffix('_captioned')}{captioned.suffix}"
                            )
                            if not raw_video.is_file():
                                raise PipelineError(
                                    f"Uncaptioned TikTok source is missing: {raw_video}"
                                )
                            result.video_paths[Platform.TIKTOK.value] = raw_video
                except (FacelessError, OSError, ValueError) as error:
                    self.logger.error("Subtitle generation failed", error=str(error))
                    stage_errors.append(f"Subtitle generation: {error}")
                else:
                    self._save_progress(checkpoint, source_script, result)

            if (
                subtitles
                and Platform.TIKTOK in platforms
                and Platform.TIKTOK.value in result.video_paths
                and "srt" in result.subtitle_paths
                and result.subtitle_paths["srt"].is_file()
            ):
                if "captions" not in checkpoint.completed_steps:
                    stage = "Portrait caption rendering"
                    checkpoint.status = JobStatus.GENERATING_SUBTITLES
                    source_video = result.video_paths[Platform.TIKTOK.value]
                    captioned_video = source_video.with_name(
                        f"{source_video.stem}_captioned{source_video.suffix}"
                    )
                    rendered = burn_subtitles_to_video(
                        video_path=source_video,
                        subtitle_path=result.subtitle_paths["srt"],
                        output_path=captioned_video,
                        niche=script.niche.value,
                        style_override=portrait_caption_style(script.niche.value),
                    )
                    if rendered != captioned_video or not rendered.is_file():
                        raise PipelineError(
                            "Portrait subtitle rendering did not create the expected video"
                        )
                    result.video_paths[Platform.TIKTOK.value] = rendered
                    script.output_paths = result.video_paths.copy()
                    self._persist_script(script, source_script, checkpoint, source_path)
                    checkpoint.completed_steps.append("captions")
                    self._save_progress(checkpoint, source_script, result)
                else:
                    captioned = result.video_paths[Platform.TIKTOK.value]
                    if (
                        not captioned.stem.endswith("_captioned")
                        or not captioned.is_file()
                    ):
                        raise PipelineError(
                            "Completed portrait captions are missing; reset the checkpoint."
                        )
            elif (
                not subtitles
                and Platform.TIKTOK in platforms
                and ("captions" in checkpoint.completed_steps)
            ):
                raise PipelineError(
                    "This checkpoint has captioned TikTok video; use subtitles or "
                    "start a new job without the existing checkpoint."
                )

            thumbnail_missing = (
                len(result.thumbnail_paths) != 3
                or len(set(result.thumbnail_paths)) != 3
                or any(
                    not path.is_file() or path.stat().st_size == 0
                    for path in result.thumbnail_paths
                )
            )
            if (
                thumbnails
                and Platform.YOUTUBE in platforms
                and Platform.YOUTUBE.value in result.video_paths
                and (
                    "thumbnails" not in checkpoint.completed_steps or thumbnail_missing
                )
            ):
                stage = "Thumbnail generation"
                checkpoint.status = JobStatus.GENERATING_THUMBNAILS
                thumbnail_variants = generate_thumbnail_variants(
                    title=script.title,
                    niche=script.niche.value,
                    base_name=script.safe_title,
                    output_dir=self._settings.get_images_dir(script.niche)
                    / "thumbnails",
                    client=self._client,
                )
                if not thumbnail_variants:
                    raise PipelineError("Thumbnail generation returned no variants")
                result.thumbnail_paths = [
                    path
                    for path in thumbnail_variants
                    if isinstance(path, Path) and path.is_file()
                ]
                if len(set(result.thumbnail_paths)) != 3:
                    raise PipelineError(
                        f"Only {len(set(result.thumbnail_paths))}/3 distinct thumbnail variants "
                        "were generated; retry after checking image generation."
                    )
                if "thumbnails" not in checkpoint.completed_steps:
                    checkpoint.completed_steps.append("thumbnails")
                self._save_progress(checkpoint, source_script, result)

            result.errors = stage_errors
            result.success = not result.errors
            checkpoint.status = (
                JobStatus.COMPLETED if result.success else JobStatus.FAILED
            )
            result.duration_seconds = (datetime.now() - start_time).total_seconds()
            self._save_progress(checkpoint, source_script, result)
            self.logger.info(
                "Script processing completed",
                duration_seconds=round(result.duration_seconds, 2),
            )
            return result

        except Exception as e:
            self.logger.exception("Pipeline failed", stage=stage, error=str(e))
            result.success = False
            result.errors = [*stage_errors, f"{stage}: {e}"]
            result.duration_seconds = (datetime.now() - start_time).total_seconds()
            if checkpoint is not None:
                checkpoint.status = JobStatus.FAILED
                try:
                    self._save_progress(checkpoint, source_script, result)
                except (CheckpointError, OSError, ValueError) as save_error:
                    self.logger.error(
                        "Could not save failed pipeline progress",
                        stage=stage,
                        error=str(save_error),
                    )
                    result.errors.append(f"Checkpoint persistence: {save_error}")
            return result

        finally:
            clear_context()

    def _scene_image_path(
        self, script: Script, scene: Scene, platform: Platform
    ) -> Path:
        """Return the generated image path for a scene and platform."""
        return (
            self._settings.get_images_dir(script.niche)
            / script.safe_title
            / f"scene_{scene.scene_number:02d}_{platform.value}.png"
        )

    def _load_or_create_checkpoint(
        self, script: Script, source_path: Path | None = None
    ) -> Checkpoint:
        """Load existing checkpoint or create new one."""
        checkpoint_dir = self._settings.get_checkpoints_dir(script.niche)
        checkpoint_path = checkpoint_dir / f"{script.safe_title}.checkpoint.json"

        if self._settings.enable_checkpointing and checkpoint_path.exists():
            try:
                checkpoint = Checkpoint.load(checkpoint_path)
                self.logger.info(
                    "Resuming from checkpoint",
                    completed_steps=checkpoint.completed_steps,
                )
                return checkpoint
            except (OSError, ValueError) as e:
                raise PipelineError(
                    f"Invalid checkpoint at {checkpoint_path}: {e}"
                ) from e

        return Checkpoint(
            job_id=uuid4(),
            script_path=source_path
            or self._settings.get_scripts_dir(script.niche)
            / f"{script.safe_title}_script.json",
            status=JobStatus.PENDING,
        )

    def _verify_source_fingerprint(
        self, script: Script, checkpoint: Checkpoint
    ) -> None:
        """Reject a same-title checkpoint created from different source content."""
        if not self._settings.enable_checkpointing:
            return

        checkpoint_dir = self._settings.get_checkpoints_dir(script.niche)
        checkpoint_path = checkpoint_dir / f"{script.safe_title}.checkpoint.json"
        fingerprint_path = checkpoint_dir / f"{script.safe_title}.source.json"
        source_data = {
            "title": script.title,
            "niche": script.niche.value,
            "source": script.source,
            "author": script.author,
            "url": script.url,
            "visual_style": (
                script.visual_style.model_dump(mode="json")
                if script.visual_style is not None
                else None
            ),
            "scenes": [
                {
                    "scene_number": scene.scene_number,
                    "narration": scene.narration,
                    "image_prompt": scene.image_prompt,
                    "duration_estimate": scene.duration_estimate,
                }
                for scene in script.scenes
            ],
        }
        fingerprint = hashlib.sha256(
            json.dumps(source_data, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()

        if checkpoint_path.exists():
            try:
                saved = json.loads(fingerprint_path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as e:
                raise PipelineError(
                    "Checkpoint source fingerprint is missing or invalid. "
                    "Start a new job without the existing checkpoint."
                ) from e
            if (
                not isinstance(saved, dict)
                or saved.get("job_id") != str(checkpoint.job_id)
                or saved.get("source_sha256") != fingerprint
            ):
                raise PipelineError(
                    "Source content differs from the approved checkpoint (or its "
                    "fingerprint is invalid). Start a new job without the existing "
                    "checkpoint."
                )
        else:
            fingerprint_path.parent.mkdir(parents=True, exist_ok=True)
            fingerprint_path.write_text(
                json.dumps(
                    {"job_id": str(checkpoint.job_id), "source_sha256": fingerprint}
                ),
                encoding="utf-8",
            )

    def _persist_script(
        self,
        script: Script,
        source_script: Script,
        checkpoint: Checkpoint,
        source_path: Path | None,
    ) -> None:
        """Write the production snapshot without modifying the input script."""
        output_path = (
            self._settings.get_scripts_dir(source_script.niche)
            / f"{source_script.safe_title}_production.json"
        )
        if source_path is not None and output_path.resolve() == source_path.resolve():
            output_path = output_path.with_name(
                f"{source_script.safe_title}_{checkpoint.job_id}_production.json"
            )
        script.to_json_file(output_path)
        checkpoint.script_path = output_path

    def _load_progress(self, script: Script, result: JobResult) -> JobResult:
        """Restore paths from the last successful checkpoint stage."""
        if not self._settings.enable_checkpointing:
            return result
        checkpoint_dir = self._settings.get_checkpoints_dir(script.niche)
        if not (checkpoint_dir / f"{script.safe_title}.checkpoint.json").exists():
            return result
        path = checkpoint_dir / f"{script.safe_title}.result.json"
        if path.exists():
            return JobResult.model_validate_json(path.read_text(encoding="utf-8"))
        return result

    def _save_progress(
        self, checkpoint: Checkpoint, script: Script, result: JobResult
    ) -> None:
        """Save produced paths alongside checkpoint state for reliable resume."""
        if not self._settings.enable_checkpointing:
            return
        path = (
            self._settings.get_checkpoints_dir(script.niche)
            / f"{script.safe_title}.result.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        self._save_checkpoint(checkpoint, script)

    def _save_checkpoint(self, checkpoint: Checkpoint, script: Script) -> None:
        """Atomically save progress under the original script identity."""
        if not self._settings.enable_checkpointing:
            return

        checkpoint_dir = self._settings.get_checkpoints_dir(script.niche)
        checkpoint_path = checkpoint_dir / f"{script.safe_title}.checkpoint.json"
        pending_path = checkpoint_path.with_name(
            f"{checkpoint_path.name}.{uuid4().hex}.pending"
        )
        try:
            checkpoint.save(pending_path)
            pending_path.replace(checkpoint_path)
        except (OSError, ValueError) as error:
            raise CheckpointError(
                "Cannot persist checkpoint and enhanced script snapshot",
                checkpoint_path=str(checkpoint_path),
            ) from error
        finally:
            try:
                pending_path.unlink(missing_ok=True)
            except OSError as error:
                self.logger.warning(
                    "Could not remove pending checkpoint",
                    path=str(pending_path),
                    error=str(error),
                )

    def run_single(
        self,
        script: Script,
        platforms: list[Platform] | None = None,
        music_path: Path | None = None,
        enhance: bool = True,
        thumbnails: bool = True,
        subtitles: bool = True,
    ) -> JobResult:
        """
        Run pipeline for a single script.

        Args:
            script: Script to process
            platforms: Target platforms
            music_path: Optional background music
            enhance: Whether to enhance with GPT before the quality gate
            thumbnails: Whether to generate YouTube thumbnails
            subtitles: Whether to create SRT and VTT subtitles

        Returns:
            JobResult with results
        """
        platforms = platforms or [Platform.YOUTUBE, Platform.TIKTOK]

        return self._process_script(
            script=script,
            platforms=platforms,
            enhance=enhance,
            thumbnails=thumbnails,
            subtitles=subtitles,
            music_path=music_path,
        )

"""
Unit tests for the pipeline orchestrator.

Tests the main pipeline coordination and job processing.
"""

from collections.abc import Generator
from contextlib import ExitStack
from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from faceless.clients.azure_openai import AzureOpenAIClient
from faceless.core.enums import JobStatus, Niche, Platform
from faceless.core.exceptions import (
    FFmpegError,
    ImageGenerationError,
    TTSGenerationError,
    VideoAssemblyError,
)
from faceless.core.models import Checkpoint, JobResult, Scene, Script, VisualStyle
from faceless.pipeline.orchestrator import Orchestrator
from faceless.services.quality_service import HookAnalysis, QualityGate, QualityScore


@pytest.fixture
def reliability_script() -> Script:
    """Create a fresh script without generated asset paths."""
    return Script(
        title="Resume test",
        niche=Niche.FINANCE,
        scenes=[
            Scene(scene_number=number, narration="Narration", image_prompt="Image")
            for number in (1, 2)
        ],
    )


@pytest.fixture
def reliability_orchestrator(tmp_path: Path) -> Orchestrator:
    """Create an orchestrator with local, checkpoint-aware service doubles."""
    with (
        patch("faceless.pipeline.orchestrator.get_settings") as settings,
        patch("faceless.pipeline.orchestrator.AzureOpenAIClient"),
        patch("faceless.pipeline.orchestrator.EnhancerService"),
        patch("faceless.pipeline.orchestrator.QualityService"),
        patch("faceless.pipeline.orchestrator.ImageService"),
        patch("faceless.pipeline.orchestrator.TTSService"),
        patch("faceless.pipeline.orchestrator.VideoService"),
    ):
        settings.return_value.enable_checkpointing = True
        settings.return_value.get_scripts_dir.return_value = tmp_path / "scripts"
        settings.return_value.get_checkpoints_dir.return_value = (
            tmp_path / "checkpoints"
        )
        settings.return_value.get_final_output_dir.return_value = tmp_path / "final"
        settings.return_value.get_images_dir.return_value = tmp_path / "images"
        settings.return_value.get_audio_dir.return_value = tmp_path / "audio"
        orchestrator = Orchestrator()
        orchestrator._client.generate_image.return_value = b"thumbnail"
        orchestrator._quality_service.evaluate_script.return_value = QualityScore(
            script_title="Resume test",
            niche=Niche.FINANCE,
            overall_score=8.0,
            hook_score=8.0,
            narrative_score=8.0,
            engagement_score=8.0,
            information_score=8.0,
            hook_analysis=HookAnalysis(
                score=8.0,
                hook_type="question",
                attention_grab=0.8,
                curiosity_gap=0.8,
            ),
            approved_for_production=True,
        )

    def generate_images(
        script: Script, platform: Platform, checkpoint: Checkpoint
    ) -> list[Path]:
        paths = []
        for scene in script.scenes:
            path = (
                tmp_path
                / "images"
                / script.safe_title
                / f"scene_{scene.scene_number:02d}_{platform.value}.png"
            )
            if not checkpoint.is_image_done(scene.scene_number) or not path.is_file():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"image")
            scene.image_path = path
            checkpoint.mark_image_done(scene.scene_number)
            paths.append(path)
        return paths

    def generate_audio(script: Script, checkpoint: Checkpoint) -> list[Path]:
        paths = []
        for scene in script.scenes:
            path = tmp_path / f"scene_{scene.scene_number:02d}.mp3"
            if not checkpoint.is_audio_done(scene.scene_number) or not path.is_file():
                path.write_bytes(b"audio")
            scene.audio_path = path
            checkpoint.mark_audio_done(scene.scene_number)
            paths.append(path)
        return paths

    def update_durations(script: Script) -> None:
        for scene in script.scenes:
            assert scene.audio_path is not None and scene.audio_path.is_file()
            scene.duration_estimate = 7.5

    def assemble(
        script: Script,
        platform: Platform,
        checkpoint: Checkpoint,
        music_path: Path | None,
    ) -> Path:
        for scene in script.scenes:
            assert scene.image_path is not None and scene.image_path.is_file()
            assert scene.image_path.name.endswith(f"_{platform.value}.png")
            assert scene.audio_path is not None and scene.audio_path.is_file()
            assert scene.duration_estimate == 7.5
            checkpoint.mark_video_done(platform.value, scene.scene_number)
        path = (
            tmp_path
            / "final"
            / f"{script.niche.value}_{script.safe_title}_{platform.value}.mp4"
        )
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(b"video")
        return path

    orchestrator._image_service.generate_for_script.side_effect = generate_images
    orchestrator._tts_service.generate_for_script.side_effect = generate_audio
    orchestrator._tts_service.update_scene_durations.side_effect = update_durations
    orchestrator._video_service.assemble_video.side_effect = assemble
    return orchestrator


def run_reliability(
    orchestrator: Orchestrator,
    script: Script,
    platforms: list[Platform] | None = None,
) -> JobResult:
    """Exercise media resumes without paying for AI or optional outputs."""
    return orchestrator.run_single(
        script,
        platforms=platforms,
        enhance=False,
        thumbnails=False,
        subtitles=False,
    )


@pytest.mark.parametrize("stage", ["images", "audio"])
@pytest.mark.parametrize("partial", [False, True])
def test_incomplete_assets_remain_retryable(
    reliability_orchestrator: Orchestrator,
    reliability_script: Script,
    stage: str,
    partial: bool,
) -> None:
    orchestrator = reliability_orchestrator
    service = (
        orchestrator._image_service if stage == "images" else orchestrator._tts_service
    )
    generate = service.generate_for_script
    original = generate.side_effect
    if partial:

        def generate_partial(
            script: Script,
            checkpoint: Checkpoint,
            platform: Platform = Platform.YOUTUBE,
        ) -> list[Path]:
            partial_script = script.model_copy(update={"scenes": script.scenes[:1]})
            if stage == "images":
                return original(partial_script, platform, checkpoint)
            return original(partial_script, checkpoint)

        generate.side_effect = generate_partial
    else:
        generate.side_effect = (
            ImageGenerationError("Failed")
            if stage == "images"
            else TTSGenerationError("Failed")
        )

    failed = run_reliability(orchestrator, reliability_script, [Platform.YOUTUBE])
    checkpoint = orchestrator._load_or_create_checkpoint(reliability_script)

    assert not failed.success
    assert checkpoint.status == JobStatus.FAILED
    assert stage not in checkpoint.completed_steps
    assert "videos" not in checkpoint.completed_steps
    if partial:
        completed_scenes = (
            checkpoint.images_generated
            if stage == "images"
            else checkpoint.audio_generated
        )
        assert completed_scenes == [1]
    orchestrator._video_service.assemble_video.assert_not_called()

    generate.side_effect = original
    resumed = run_reliability(orchestrator, reliability_script, [Platform.YOUTUBE])

    assert resumed.success, resumed.errors
    assert (
        stage
        in orchestrator._load_or_create_checkpoint(reliability_script).completed_steps
    )


def test_each_platform_uses_its_own_images(
    reliability_orchestrator: Orchestrator, reliability_script: Script
) -> None:
    result = run_reliability(reliability_orchestrator, reliability_script)

    assert result.success, result.errors
    assert set(result.video_paths) == {"youtube", "tiktok"}
    assert reliability_orchestrator._video_service.assemble_video.call_count == 2


def test_failed_platform_does_not_block_ready_platform(
    reliability_orchestrator: Orchestrator, reliability_script: Script
) -> None:
    orchestrator = reliability_orchestrator
    generate = orchestrator._image_service.generate_for_script
    original = generate.side_effect

    def fail_youtube(
        script: Script, platform: Platform, checkpoint: Checkpoint
    ) -> list[Path]:
        if platform == Platform.YOUTUBE:
            raise ImageGenerationError("YouTube images failed")
        return original(script, platform, checkpoint)

    generate.side_effect = fail_youtube
    failed = run_reliability(orchestrator, reliability_script)

    assert not failed.success
    assert set(failed.video_paths) == {"tiktok"}
    checkpoint = orchestrator._load_or_create_checkpoint(reliability_script)
    assert "images" not in checkpoint.completed_steps
    assert "videos" not in checkpoint.completed_steps

    generate.side_effect = original
    resumed = run_reliability(orchestrator, reliability_script)

    assert resumed.success, resumed.errors
    assert set(resumed.video_paths) == {"youtube", "tiktok"}


def test_resume_restores_assets_and_audio_durations(
    reliability_orchestrator: Orchestrator, reliability_script: Script
) -> None:
    orchestrator = reliability_orchestrator
    fresh_script = reliability_script.model_copy(deep=True)
    assemble = orchestrator._video_service.assemble_video
    original = assemble.side_effect
    assemble.side_effect = VideoAssemblyError("Interrupted")

    failed = run_reliability(orchestrator, reliability_script, [Platform.YOUTUBE])
    assert not failed.success

    assemble.side_effect = original
    resumed = run_reliability(orchestrator, fresh_script, [Platform.YOUTUBE])

    assert resumed.success, resumed.errors
    assert resumed.script_path is not None
    produced = Script.from_json_file(resumed.script_path)
    assert all(scene.image_path is not None for scene in produced.scenes)
    assert all(scene.audio_path is not None for scene in produced.scenes)
    assert all(scene.duration_estimate == 7.5 for scene in produced.scenes)
    assert all(scene.image_path is None for scene in fresh_script.scenes)


def test_completed_resume_returns_existing_video_paths(
    reliability_orchestrator: Orchestrator, reliability_script: Script
) -> None:
    orchestrator = reliability_orchestrator
    fresh_script = reliability_script.model_copy(deep=True)
    first = run_reliability(orchestrator, reliability_script, [Platform.YOUTUBE])
    assert first.success, first.errors
    orchestrator._video_service.assemble_video.reset_mock()

    resumed = run_reliability(orchestrator, fresh_script, [Platform.YOUTUBE])

    assert resumed.success, resumed.errors
    assert resumed.video_paths == first.video_paths
    orchestrator._video_service.assemble_video.assert_not_called()


def test_resume_repairs_missing_assets_and_final_video(
    reliability_orchestrator: Orchestrator, reliability_script: Script
) -> None:
    orchestrator = reliability_orchestrator
    fresh_script = reliability_script.model_copy(deep=True)
    first = run_reliability(orchestrator, reliability_script, [Platform.YOUTUBE])
    assert first.success and first.script_path is not None, first.errors
    scene = Script.from_json_file(first.script_path).scenes[0]
    assert scene.image_path is not None
    assert scene.audio_path is not None
    scene.image_path.unlink()
    scene.audio_path.unlink()
    first.video_paths["youtube"].unlink()

    resumed = run_reliability(orchestrator, fresh_script, [Platform.YOUTUBE])

    assert resumed.success, resumed.errors
    assert scene.image_path.is_file()
    assert scene.audio_path.is_file()
    assert resumed.video_paths["youtube"].is_file()
    assert orchestrator._video_service.assemble_video.call_count == 2


def test_resume_generates_newly_requested_platform(
    reliability_orchestrator: Orchestrator, reliability_script: Script
) -> None:
    orchestrator = reliability_orchestrator
    first = run_reliability(orchestrator, reliability_script, [Platform.YOUTUBE])
    assert first.success, first.errors
    orchestrator._video_service.assemble_video.reset_mock()

    resumed = run_reliability(orchestrator, reliability_script)

    assert resumed.success, resumed.errors
    assert set(resumed.video_paths) == {"youtube", "tiktok"}
    orchestrator._video_service.assemble_video.assert_called_once()
    assert (
        orchestrator._video_service.assemble_video.call_args.kwargs["platform"]
        == Platform.TIKTOK
    )


def test_disabled_checkpointing_ignores_existing_progress(
    reliability_orchestrator: Orchestrator, reliability_script: Script
) -> None:
    orchestrator = reliability_orchestrator
    first = run_reliability(orchestrator, reliability_script, [Platform.YOUTUBE])
    assert first.success, first.errors
    orchestrator._settings.enable_checkpointing = False

    checkpoint = orchestrator._load_or_create_checkpoint(reliability_script)

    assert checkpoint.status == JobStatus.PENDING
    assert checkpoint.completed_steps == []
    assert checkpoint.images_generated == []


# =============================================================================
# Orchestrator Initialization Tests
# =============================================================================


class TestOrchestratorInit:
    """Tests for Orchestrator initialization."""

    @patch("faceless.pipeline.orchestrator.get_settings")
    @patch("faceless.pipeline.orchestrator.AzureOpenAIClient")
    @patch("faceless.pipeline.orchestrator.EnhancerService")
    @patch("faceless.pipeline.orchestrator.ImageService")
    @patch("faceless.pipeline.orchestrator.TTSService")
    @patch("faceless.pipeline.orchestrator.VideoService")
    def test_initializes_all_services(
        self,
        mock_video: MagicMock,
        mock_tts: MagicMock,
        mock_image: MagicMock,
        mock_enhancer: MagicMock,
        mock_client: MagicMock,
        mock_settings: MagicMock,
    ) -> None:
        """Test that all services are initialized."""
        from faceless.pipeline.orchestrator import Orchestrator

        mock_settings.return_value.enable_checkpointing = True

        Orchestrator()

        mock_client.assert_called_once()
        mock_enhancer.assert_called_once()
        mock_image.assert_called_once()
        mock_tts.assert_called_once()
        mock_video.assert_called_once()


# =============================================================================
# Run Pipeline Tests
# =============================================================================


class TestOrchestratorRun:
    """Tests for the main run method."""

    @pytest.fixture
    def mock_orchestrator(self) -> MagicMock:
        """Create a mock orchestrator setup."""
        with (
            patch("faceless.pipeline.orchestrator.get_settings") as mock_settings,
            patch("faceless.pipeline.orchestrator.AzureOpenAIClient"),
            patch("faceless.pipeline.orchestrator.EnhancerService"),
            patch("faceless.pipeline.orchestrator.ImageService"),
            patch("faceless.pipeline.orchestrator.TTSService"),
            patch("faceless.pipeline.orchestrator.VideoService"),
        ):
            settings = MagicMock()
            settings.enable_checkpointing = False
            settings.output_base_dir = Path("/tmp/output")
            mock_settings.return_value = settings

            from faceless.pipeline.orchestrator import Orchestrator

            yield Orchestrator()

    @patch("faceless.pipeline.orchestrator.get_settings")
    @patch("faceless.pipeline.orchestrator.AzureOpenAIClient")
    @patch("faceless.pipeline.orchestrator.EnhancerService")
    @patch("faceless.pipeline.orchestrator.ImageService")
    @patch("faceless.pipeline.orchestrator.TTSService")
    @patch("faceless.pipeline.orchestrator.VideoService")
    def test_run_with_no_scripts(
        self,
        mock_video: MagicMock,
        mock_tts: MagicMock,
        mock_image: MagicMock,
        mock_enhancer: MagicMock,
        mock_client: MagicMock,
        mock_settings: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test run with no scripts returns empty results."""
        from faceless.pipeline.orchestrator import Orchestrator

        settings = MagicMock()
        settings.enable_checkpointing = False
        settings.output_base_dir = tmp_path
        settings.get_scripts_dir.return_value = tmp_path / "scripts"
        settings.ensure_directories = MagicMock()
        mock_settings.return_value = settings

        orchestrator = Orchestrator()
        results = orchestrator.run(niche=Niche.SCARY_STORIES, count=1)

        assert len(results) == 0

    @patch("faceless.pipeline.orchestrator.get_settings")
    @patch("faceless.pipeline.orchestrator.AzureOpenAIClient")
    @patch("faceless.pipeline.orchestrator.EnhancerService")
    @patch("faceless.pipeline.orchestrator.ImageService")
    @patch("faceless.pipeline.orchestrator.TTSService")
    @patch("faceless.pipeline.orchestrator.VideoService")
    def test_run_defaults_to_both_platforms(
        self,
        mock_video: MagicMock,
        mock_tts: MagicMock,
        mock_image: MagicMock,
        mock_enhancer: MagicMock,
        mock_client: MagicMock,
        mock_settings: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that run defaults to YouTube and TikTok platforms."""
        from faceless.pipeline.orchestrator import Orchestrator

        settings = MagicMock()
        settings.enable_checkpointing = False
        settings.output_base_dir = tmp_path
        settings.get_scripts_dir.return_value = tmp_path / "scripts"
        settings.ensure_directories = MagicMock()
        mock_settings.return_value = settings

        orchestrator = Orchestrator()

        # Should not raise
        results = orchestrator.run(niche=Niche.SCARY_STORIES)

        assert isinstance(results, list)


# =============================================================================
# Load Existing Scripts Tests
# =============================================================================


class TestLoadExistingScripts:
    """Tests for loading existing scripts."""

    @patch("faceless.pipeline.orchestrator.get_settings")
    @patch("faceless.pipeline.orchestrator.AzureOpenAIClient")
    @patch("faceless.pipeline.orchestrator.EnhancerService")
    @patch("faceless.pipeline.orchestrator.ImageService")
    @patch("faceless.pipeline.orchestrator.TTSService")
    @patch("faceless.pipeline.orchestrator.VideoService")
    def test_loads_scripts_from_directory(
        self,
        mock_video: MagicMock,
        mock_tts: MagicMock,
        mock_image: MagicMock,
        mock_enhancer: MagicMock,
        mock_client: MagicMock,
        mock_settings: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test loading scripts from directory."""
        from faceless.pipeline.orchestrator import Orchestrator

        settings = MagicMock()
        settings.enable_checkpointing = False
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(parents=True)
        settings.get_scripts_dir.return_value = scripts_dir
        mock_settings.return_value = settings

        # Create test script
        script = Script(
            title="Test Script",
            niche=Niche.SCARY_STORIES,
            scenes=[
                Scene(
                    scene_number=1,
                    narration="Test narration",
                    image_prompt="Test prompt",
                    duration_estimate=10.0,
                )
            ],
        )
        script.to_json_file(scripts_dir / "test_script.json")

        orchestrator = Orchestrator()
        scripts = orchestrator._load_existing_scripts(Niche.SCARY_STORIES, count=1)

        assert len(scripts) == 1
        assert scripts[0].title == "Test Script"

    @patch("faceless.pipeline.orchestrator.get_settings")
    @patch("faceless.pipeline.orchestrator.AzureOpenAIClient")
    @patch("faceless.pipeline.orchestrator.EnhancerService")
    @patch("faceless.pipeline.orchestrator.ImageService")
    @patch("faceless.pipeline.orchestrator.TTSService")
    @patch("faceless.pipeline.orchestrator.VideoService")
    def test_handles_missing_directory(
        self,
        mock_video: MagicMock,
        mock_tts: MagicMock,
        mock_image: MagicMock,
        mock_enhancer: MagicMock,
        mock_client: MagicMock,
        mock_settings: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test handling of missing scripts directory."""
        from faceless.pipeline.orchestrator import Orchestrator

        settings = MagicMock()
        settings.enable_checkpointing = False
        settings.get_scripts_dir.return_value = tmp_path / "nonexistent"
        mock_settings.return_value = settings

        orchestrator = Orchestrator()
        scripts = orchestrator._load_existing_scripts(Niche.SCARY_STORIES, count=1)

        assert len(scripts) == 0

    @patch("faceless.pipeline.orchestrator.get_settings")
    @patch("faceless.pipeline.orchestrator.AzureOpenAIClient")
    @patch("faceless.pipeline.orchestrator.EnhancerService")
    @patch("faceless.pipeline.orchestrator.ImageService")
    @patch("faceless.pipeline.orchestrator.TTSService")
    @patch("faceless.pipeline.orchestrator.VideoService")
    def test_handles_invalid_script_files(
        self,
        mock_video: MagicMock,
        mock_tts: MagicMock,
        mock_image: MagicMock,
        mock_enhancer: MagicMock,
        mock_client: MagicMock,
        mock_settings: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test handling of invalid script files."""
        from faceless.pipeline.orchestrator import Orchestrator

        settings = MagicMock()
        settings.enable_checkpointing = False
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(parents=True)
        settings.get_scripts_dir.return_value = scripts_dir
        mock_settings.return_value = settings

        # Create invalid script file
        invalid_script = scripts_dir / "invalid_script.json"
        invalid_script.write_text("not valid json{")

        orchestrator = Orchestrator()
        scripts = orchestrator._load_existing_scripts(Niche.SCARY_STORIES, count=1)

        # Should handle error gracefully
        assert len(scripts) == 0


# =============================================================================
# Process Script Tests
# =============================================================================


class TestProcessScript:
    """Tests for processing individual scripts."""

    @pytest.fixture
    def sample_script(self) -> Script:
        """Create a sample script."""
        return Script(
            title="Test Script",
            niche=Niche.SCARY_STORIES,
            scenes=[
                Scene(
                    scene_number=1,
                    narration="Test narration",
                    image_prompt="Test prompt",
                    duration_estimate=10.0,
                )
            ],
            visual_style=VisualStyle(
                environment="Dark",
                color_mood="Blue",
                texture="Fog",
            ),
        )

    @patch("faceless.pipeline.orchestrator.clear_context")
    @patch("faceless.pipeline.orchestrator.bind_context")
    @patch("faceless.pipeline.orchestrator.get_settings")
    @patch("faceless.pipeline.orchestrator.AzureOpenAIClient")
    @patch("faceless.pipeline.orchestrator.EnhancerService")
    @patch("faceless.pipeline.orchestrator.ImageService")
    @patch("faceless.pipeline.orchestrator.TTSService")
    @patch("faceless.pipeline.orchestrator.VideoService")
    def test_process_script_returns_job_result(
        self,
        mock_video: MagicMock,
        mock_tts: MagicMock,
        mock_image: MagicMock,
        mock_enhancer: MagicMock,
        mock_client: MagicMock,
        mock_settings: MagicMock,
        mock_bind: MagicMock,
        mock_clear: MagicMock,
        sample_script: Script,
        tmp_path: Path,
    ) -> None:
        """Test that process_script returns a JobResult."""
        from faceless.pipeline.orchestrator import Orchestrator

        settings = MagicMock()
        settings.enable_checkpointing = False
        settings.output_base_dir = tmp_path
        settings.get_scripts_dir.return_value = tmp_path / "scripts"
        settings.get_checkpoints_dir.return_value = tmp_path / "checkpoints"
        settings.get_images_dir.return_value = tmp_path / "images"
        settings.get_audio_dir.return_value = tmp_path / "audio"
        settings.get_videos_dir.return_value = tmp_path / "videos"
        mock_settings.return_value = settings

        # Setup mocks
        mock_image.return_value.generate_for_script.return_value = [
            tmp_path / "img.png"
        ]
        mock_tts.return_value.generate_for_script.return_value = None
        mock_tts.return_value.update_scene_durations.return_value = None
        mock_video.return_value.assemble_video.return_value = tmp_path / "video.mp4"

        orchestrator = Orchestrator()
        result = orchestrator._process_script(
            script=sample_script,
            platforms=[Platform.YOUTUBE],
            enhance=False,
            thumbnails=False,
            subtitles=False,
            music_path=None,
        )

        assert isinstance(result, JobResult)

    @patch("faceless.pipeline.orchestrator.clear_context")
    @patch("faceless.pipeline.orchestrator.bind_context")
    @patch("faceless.pipeline.orchestrator.get_settings")
    @patch("faceless.pipeline.orchestrator.AzureOpenAIClient")
    @patch("faceless.pipeline.orchestrator.EnhancerService")
    @patch("faceless.pipeline.orchestrator.ImageService")
    @patch("faceless.pipeline.orchestrator.TTSService")
    @patch("faceless.pipeline.orchestrator.VideoService")
    def test_process_script_with_enhancement(
        self,
        mock_video: MagicMock,
        mock_tts: MagicMock,
        mock_image: MagicMock,
        mock_enhancer_class: MagicMock,
        mock_client: MagicMock,
        mock_settings: MagicMock,
        mock_bind: MagicMock,
        mock_clear: MagicMock,
        sample_script: Script,
        tmp_path: Path,
    ) -> None:
        """Test script processing with enhancement enabled."""
        from faceless.pipeline.orchestrator import Orchestrator

        settings = MagicMock()
        settings.enable_checkpointing = False
        settings.output_base_dir = tmp_path
        settings.get_scripts_dir.return_value = tmp_path / "scripts"
        settings.get_checkpoints_dir.return_value = tmp_path / "checkpoints"
        mock_settings.return_value = settings

        # Mock enhancer to return enhanced script
        mock_enhancer = MagicMock()
        mock_enhancer.enhance_script.return_value = sample_script
        mock_enhancer_class.return_value = mock_enhancer

        mock_image.return_value.generate_for_script.return_value = []
        mock_video.return_value.assemble_video.return_value = tmp_path / "video.mp4"

        orchestrator = Orchestrator()
        orchestrator._process_script(
            script=sample_script,
            platforms=[Platform.YOUTUBE],
            enhance=True,
            thumbnails=False,
            subtitles=False,
            music_path=None,
        )

        mock_enhancer.enhance_script.assert_called_once()

    @patch("faceless.pipeline.orchestrator.clear_context")
    @patch("faceless.pipeline.orchestrator.bind_context")
    @patch("faceless.pipeline.orchestrator.get_settings")
    @patch("faceless.pipeline.orchestrator.AzureOpenAIClient")
    @patch("faceless.pipeline.orchestrator.EnhancerService")
    @patch("faceless.pipeline.orchestrator.ImageService")
    @patch("faceless.pipeline.orchestrator.TTSService")
    @patch("faceless.pipeline.orchestrator.VideoService")
    def test_process_script_handles_errors(
        self,
        mock_video: MagicMock,
        mock_tts: MagicMock,
        mock_image: MagicMock,
        mock_enhancer: MagicMock,
        mock_client: MagicMock,
        mock_settings: MagicMock,
        mock_bind: MagicMock,
        mock_clear: MagicMock,
        sample_script: Script,
        tmp_path: Path,
    ) -> None:
        """Test that errors are handled gracefully."""
        from faceless.pipeline.orchestrator import Orchestrator

        settings = MagicMock()
        settings.enable_checkpointing = False
        settings.output_base_dir = tmp_path
        settings.get_scripts_dir.return_value = tmp_path / "scripts"
        settings.get_checkpoints_dir.return_value = tmp_path / "checkpoints"
        mock_settings.return_value = settings

        # Make image service raise an error
        mock_image.return_value.generate_for_script.side_effect = Exception(
            "Image generation failed"
        )
        mock_video.return_value.assemble_video.return_value = tmp_path / "video.mp4"

        orchestrator = Orchestrator()
        result = orchestrator._process_script(
            script=sample_script,
            platforms=[Platform.YOUTUBE],
            enhance=False,
            thumbnails=False,
            subtitles=False,
            music_path=None,
        )

        # Should return a result with errors
        assert isinstance(result, JobResult)
        assert len(result.errors) > 0


# =============================================================================
# Checkpoint Tests
# =============================================================================


class TestCheckpointing:
    """Tests for checkpoint functionality."""

    @pytest.fixture
    def sample_script(self) -> Script:
        """Create a sample script."""
        return Script(
            title="Test Script",
            niche=Niche.SCARY_STORIES,
            scenes=[
                Scene(
                    scene_number=1,
                    narration="Test",
                    image_prompt="Test",
                    duration_estimate=10.0,
                )
            ],
        )

    @patch("faceless.pipeline.orchestrator.get_settings")
    @patch("faceless.pipeline.orchestrator.AzureOpenAIClient")
    @patch("faceless.pipeline.orchestrator.EnhancerService")
    @patch("faceless.pipeline.orchestrator.ImageService")
    @patch("faceless.pipeline.orchestrator.TTSService")
    @patch("faceless.pipeline.orchestrator.VideoService")
    def test_creates_new_checkpoint(
        self,
        mock_video: MagicMock,
        mock_tts: MagicMock,
        mock_image: MagicMock,
        mock_enhancer: MagicMock,
        mock_client: MagicMock,
        mock_settings: MagicMock,
        sample_script: Script,
        tmp_path: Path,
    ) -> None:
        """Test creating a new checkpoint."""
        from faceless.pipeline.orchestrator import Orchestrator

        settings = MagicMock()
        settings.enable_checkpointing = True
        checkpoint_dir = tmp_path / "checkpoints"
        checkpoint_dir.mkdir(parents=True)
        settings.get_checkpoints_dir.return_value = checkpoint_dir
        settings.get_scripts_dir.return_value = tmp_path / "scripts"
        mock_settings.return_value = settings

        orchestrator = Orchestrator()
        checkpoint = orchestrator._load_or_create_checkpoint(sample_script)

        assert checkpoint.status == JobStatus.PENDING
        assert len(checkpoint.completed_steps) == 0

    @patch("faceless.pipeline.orchestrator.get_settings")
    @patch("faceless.pipeline.orchestrator.AzureOpenAIClient")
    @patch("faceless.pipeline.orchestrator.EnhancerService")
    @patch("faceless.pipeline.orchestrator.ImageService")
    @patch("faceless.pipeline.orchestrator.TTSService")
    @patch("faceless.pipeline.orchestrator.VideoService")
    def test_loads_existing_checkpoint(
        self,
        mock_video: MagicMock,
        mock_tts: MagicMock,
        mock_image: MagicMock,
        mock_enhancer: MagicMock,
        mock_client: MagicMock,
        mock_settings: MagicMock,
        sample_script: Script,
        tmp_path: Path,
    ) -> None:
        """Test loading an existing checkpoint."""
        from faceless.pipeline.orchestrator import Orchestrator

        settings = MagicMock()
        settings.enable_checkpointing = True
        checkpoint_dir = tmp_path / "checkpoints"
        checkpoint_dir.mkdir(parents=True)
        settings.get_checkpoints_dir.return_value = checkpoint_dir
        settings.get_scripts_dir.return_value = tmp_path / "scripts"
        mock_settings.return_value = settings

        # Create existing checkpoint
        existing_checkpoint = Checkpoint(
            job_id=uuid4(),
            script_path=tmp_path / "scripts" / "test.json",
            status=JobStatus.GENERATING_IMAGES,
            completed_steps=["enhance"],
        )
        checkpoint_path = checkpoint_dir / f"{sample_script.safe_title}.checkpoint.json"
        existing_checkpoint.save(checkpoint_path)

        orchestrator = Orchestrator()
        checkpoint = orchestrator._load_or_create_checkpoint(sample_script)

        assert "enhance" in checkpoint.completed_steps

    @patch("faceless.pipeline.orchestrator.get_settings")
    @patch("faceless.pipeline.orchestrator.AzureOpenAIClient")
    @patch("faceless.pipeline.orchestrator.EnhancerService")
    @patch("faceless.pipeline.orchestrator.ImageService")
    @patch("faceless.pipeline.orchestrator.TTSService")
    @patch("faceless.pipeline.orchestrator.VideoService")
    def test_save_checkpoint_respects_setting(
        self,
        mock_video: MagicMock,
        mock_tts: MagicMock,
        mock_image: MagicMock,
        mock_enhancer: MagicMock,
        mock_client: MagicMock,
        mock_settings: MagicMock,
        sample_script: Script,
        tmp_path: Path,
    ) -> None:
        """Test that checkpointing can be disabled."""
        from faceless.pipeline.orchestrator import Orchestrator

        settings = MagicMock()
        settings.enable_checkpointing = False
        settings.get_checkpoints_dir.return_value = tmp_path / "checkpoints"
        mock_settings.return_value = settings

        checkpoint = Checkpoint(
            job_id=uuid4(),
            script_path=tmp_path / "test.json",
            status=JobStatus.PENDING,
        )

        orchestrator = Orchestrator()
        orchestrator._save_checkpoint(checkpoint, sample_script)

        # Checkpoint should not be saved
        checkpoint_path = (
            tmp_path / "checkpoints" / f"{sample_script.safe_title}.checkpoint.json"
        )
        assert not checkpoint_path.exists()


# =============================================================================
# Run Single Tests
# =============================================================================


class TestRunSingle:
    """Tests for run_single method."""

    @pytest.fixture
    def sample_script(self) -> Script:
        """Create a sample script."""
        return Script(
            title="Single Script",
            niche=Niche.FINANCE,
            scenes=[
                Scene(
                    scene_number=1,
                    narration="Test",
                    image_prompt="Test",
                    duration_estimate=10.0,
                )
            ],
        )

    @patch("faceless.pipeline.orchestrator.clear_context")
    @patch("faceless.pipeline.orchestrator.bind_context")
    @patch("faceless.pipeline.orchestrator.get_settings")
    @patch("faceless.pipeline.orchestrator.AzureOpenAIClient")
    @patch("faceless.pipeline.orchestrator.EnhancerService")
    @patch("faceless.pipeline.orchestrator.ImageService")
    @patch("faceless.pipeline.orchestrator.TTSService")
    @patch("faceless.pipeline.orchestrator.VideoService")
    def test_run_single(
        self,
        mock_video: MagicMock,
        mock_tts: MagicMock,
        mock_image: MagicMock,
        mock_enhancer: MagicMock,
        mock_client: MagicMock,
        mock_settings: MagicMock,
        mock_bind: MagicMock,
        mock_clear: MagicMock,
        sample_script: Script,
        tmp_path: Path,
    ) -> None:
        """Test run_single method."""
        from faceless.pipeline.orchestrator import Orchestrator

        settings = MagicMock()
        settings.enable_checkpointing = False
        settings.output_base_dir = tmp_path
        settings.get_scripts_dir.return_value = tmp_path / "scripts"
        settings.get_checkpoints_dir.return_value = tmp_path / "checkpoints"
        mock_settings.return_value = settings

        mock_image.return_value.generate_for_script.return_value = []
        mock_video.return_value.assemble_video.return_value = tmp_path / "video.mp4"

        orchestrator = Orchestrator()
        result = orchestrator.run_single(sample_script)

        assert isinstance(result, JobResult)

    @patch("faceless.pipeline.orchestrator.clear_context")
    @patch("faceless.pipeline.orchestrator.bind_context")
    @patch("faceless.pipeline.orchestrator.get_settings")
    @patch("faceless.pipeline.orchestrator.AzureOpenAIClient")
    @patch("faceless.pipeline.orchestrator.EnhancerService")
    @patch("faceless.pipeline.orchestrator.ImageService")
    @patch("faceless.pipeline.orchestrator.TTSService")
    @patch("faceless.pipeline.orchestrator.VideoService")
    def test_run_single_with_custom_platforms(
        self,
        mock_video: MagicMock,
        mock_tts: MagicMock,
        mock_image: MagicMock,
        mock_enhancer: MagicMock,
        mock_client: MagicMock,
        mock_settings: MagicMock,
        mock_bind: MagicMock,
        mock_clear: MagicMock,
        sample_script: Script,
        tmp_path: Path,
    ) -> None:
        """Test run_single with custom platforms."""
        from faceless.pipeline.orchestrator import Orchestrator

        settings = MagicMock()
        settings.enable_checkpointing = False
        settings.output_base_dir = tmp_path
        settings.get_scripts_dir.return_value = tmp_path / "scripts"
        settings.get_checkpoints_dir.return_value = tmp_path / "checkpoints"
        mock_settings.return_value = settings

        mock_image.return_value.generate_for_script.return_value = []
        mock_video.return_value.assemble_video.return_value = tmp_path / "video.mp4"

        orchestrator = Orchestrator()
        result = orchestrator.run_single(
            sample_script,
            platforms=[Platform.TIKTOK],
        )

        assert isinstance(result, JobResult)


class TestProductionPipeline:
    """Integration of orchestration stages with all paid services mocked."""

    @pytest.fixture
    def pipeline(
        self, tmp_path: Path
    ) -> Generator[tuple[Orchestrator, Script, MagicMock], None, None]:
        with ExitStack() as stack:
            settings_class = stack.enter_context(
                patch("faceless.pipeline.orchestrator.get_settings")
            )
            for name in (
                "AzureOpenAIClient",
                "EnhancerService",
                "QualityService",
                "ImageService",
                "TTSService",
                "VideoService",
            ):
                stack.enter_context(patch(f"faceless.pipeline.orchestrator.{name}"))
            thumbnails = stack.enter_context(
                patch("faceless.pipeline.orchestrator.generate_thumbnail_variants")
            )
            captions = stack.enter_context(
                patch("faceless.pipeline.orchestrator.burn_subtitles_to_video")
            )
            settings = MagicMock()
            settings.enable_checkpointing = True
            settings.get_scripts_dir.return_value = tmp_path / "scripts"
            settings.get_checkpoints_dir.return_value = tmp_path / "checkpoints"
            settings.get_images_dir.return_value = tmp_path / "images"
            settings.get_audio_dir.return_value = tmp_path / "audio"
            settings.get_final_output_dir.return_value = tmp_path / "final"
            settings_class.return_value = settings

            script = Script(
                title="Original Title",
                niche=Niche.SCARY_STORIES,
                scenes=[
                    Scene(
                        scene_number=1,
                        narration="Original opening",
                        image_prompt="Original image",
                    )
                ],
            )
            enhanced = script.model_copy(deep=True)
            enhanced.title = "Improved Title"
            enhanced.scenes[0].narration = "What was behind the door?"
            orchestrator = Orchestrator()
            orchestrator._enhancer_service.enhance_script.return_value = enhanced
            orchestrator._quality_service.evaluate_script.return_value = QualityScore(
                script_title=enhanced.title,
                niche=script.niche,
                overall_score=8.0,
                hook_score=8.0,
                narrative_score=8.0,
                engagement_score=8.0,
                information_score=8.0,
                hook_analysis=HookAnalysis(
                    score=8.0,
                    hook_type="mystery",
                    attention_grab=0.9,
                    curiosity_gap=0.9,
                ),
                approved_for_production=True,
            )

            def generate_images(
                script: Script, platform: Platform, checkpoint: Checkpoint
            ) -> list[Path]:
                paths = []
                for scene in script.scenes:
                    path = (
                        settings.get_images_dir(script.niche)
                        / script.safe_title
                        / f"scene_{scene.scene_number:02d}_{platform.value}.png"
                    )
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(b"image")
                    scene.image_path = path
                    paths.append(path)
                return paths

            def generate_audio(script: Script, checkpoint: Checkpoint) -> list[Path]:
                path = tmp_path / "audio" / "scene_01.mp3"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"audio")
                script.scenes[0].audio_path = path
                return [path]

            def set_duration(script: Script) -> None:
                script.scenes[0].duration_estimate = 4.2

            def assemble_video(
                script: Script,
                platform: Platform,
                checkpoint: Checkpoint,
                music_path: Path | None,
            ) -> Path:
                assert script.scenes[0].image_path is not None
                assert script.scenes[0].image_path.name.endswith(
                    f"_{platform.value}.png"
                )
                path = tmp_path / "final" / f"{platform.value}.mp4"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"video")
                return path

            def generate_thumbnails(
                title: str,
                niche: str,
                base_name: str,
                output_dir: Path,
                client: AzureOpenAIClient,
            ) -> list[Path]:
                output_dir.mkdir(parents=True, exist_ok=True)
                paths = [
                    output_dir / f"{base_name}_thumb_v{i}.png" for i in range(1, 4)
                ]
                for path in paths:
                    path.write_bytes(b"thumbnail")
                return paths

            def render_captions(
                video_path: Path,
                subtitle_path: Path,
                output_path: Path,
                niche: str,
                style_override: dict[str, object],
            ) -> Path:
                assert video_path.exists()
                assert subtitle_path.exists()
                assert style_override["margin_v"] == 520
                output_path.write_bytes(b"captioned")
                return output_path

            orchestrator._image_service.generate_for_script.side_effect = (
                generate_images
            )
            orchestrator._tts_service.generate_for_script.side_effect = generate_audio
            orchestrator._tts_service.update_scene_durations.side_effect = set_duration
            orchestrator._video_service.assemble_video.side_effect = assemble_video
            thumbnails.side_effect = generate_thumbnails
            captions.side_effect = render_captions
            yield orchestrator, script, thumbnails

    @pytest.mark.parametrize("approved", [False, True])
    def test_weak_hook_blocks_all_media(
        self, pipeline: tuple[Orchestrator, Script, MagicMock], approved: bool
    ) -> None:
        orchestrator, script, thumbnails = pipeline
        score = orchestrator._quality_service.evaluate_script.return_value
        score.hook_score = 5.0
        score.approved_for_production = approved
        score.improvements = ["Start with a concrete question"]

        result = orchestrator.run_single(script, platforms=[Platform.YOUTUBE])

        assert not result.success
        assert "hook 5.0/10" in result.errors[0]
        assert "Start with a concrete question" in result.errors[0]
        orchestrator._image_service.generate_for_script.assert_not_called()
        orchestrator._tts_service.generate_for_script.assert_not_called()
        orchestrator._video_service.assemble_video.assert_not_called()
        thumbnails.assert_not_called()
        checkpoint = orchestrator._load_or_create_checkpoint(script)
        assert checkpoint.status == JobStatus.FAILED
        assert "quality" not in checkpoint.completed_steps

    def test_other_quality_gate_rejection_stops_before_media(
        self, pipeline: tuple[Orchestrator, Script, MagicMock]
    ) -> None:
        orchestrator, script, _ = pipeline
        score = orchestrator._quality_service.evaluate_script.return_value
        score.approved_for_production = False
        score.critical_issues = ["Factual claims need sources"]

        result = orchestrator.run_single(script, platforms=[Platform.YOUTUBE])

        assert not result.success
        assert "Factual claims need sources" in result.errors[0]
        orchestrator._image_service.generate_for_script.assert_not_called()

    def test_quality_feedback_revises_hook_before_media(
        self, pipeline: tuple[Orchestrator, Script, MagicMock]
    ) -> None:
        orchestrator, script, _ = pipeline
        rejected = orchestrator._quality_service.evaluate_script.return_value
        rejected.approved_for_production = False
        rejected.hook_score = 5.0
        rejected.gates_failed = [QualityGate.HOOK_QUALITY]
        rejected.improvements = ["Open with a specific question"]
        approved = replace(
            rejected,
            approved_for_production=True,
            hook_score=8.0,
            gates_failed=[],
            improvements=[],
        )
        orchestrator._quality_service.evaluate_script.side_effect = [
            rejected,
            approved,
        ]
        initial = orchestrator._enhancer_service.enhance_script.return_value
        revised = initial.model_copy(deep=True)
        revised.scenes[0].narration = "Why was the door unlocked?"
        orchestrator._enhancer_service.enhance_script.side_effect = [initial, revised]

        result = orchestrator.run_single(
            script, platforms=[Platform.TIKTOK], thumbnails=False, subtitles=False
        )

        assert result.success
        assert orchestrator._quality_service.evaluate_script.call_count == 2
        assert orchestrator._enhancer_service.enhance_script.call_count == 2
        feedback = orchestrator._enhancer_service.enhance_script.call_args_list[
            1
        ].kwargs["feedback"]
        assert any("hook" in item.lower() for item in feedback)
        assert "Open with a specific question" in feedback
        assert result.script_path is not None
        assert (
            Script.from_json_file(result.script_path).scenes[0].narration
            == "Why was the door unlocked?"
        )
        orchestrator._image_service.generate_for_script.assert_called_once()

    def test_quality_revisions_are_bounded_before_media(
        self, pipeline: tuple[Orchestrator, Script, MagicMock]
    ) -> None:
        orchestrator, script, _ = pipeline
        score = orchestrator._quality_service.evaluate_script.return_value
        score.approved_for_production = False
        score.hook_score = 5.0
        score.gates_failed = [QualityGate.HOOK_QUALITY]

        result = orchestrator.run_single(
            script, platforms=[Platform.YOUTUBE], thumbnails=False, subtitles=False
        )

        assert not result.success
        assert "revisions: 2/2" in result.errors[0]
        assert orchestrator._quality_service.evaluate_script.call_count == 3
        assert orchestrator._enhancer_service.enhance_script.call_count == 3
        orchestrator._image_service.generate_for_script.assert_not_called()

    def test_critical_quality_issue_is_not_rewritten_automatically(
        self, pipeline: tuple[Orchestrator, Script, MagicMock]
    ) -> None:
        orchestrator, script, _ = pipeline
        score = orchestrator._quality_service.evaluate_script.return_value
        score.approved_for_production = False
        score.critical_issues = ["Verify the unsupported claim"]

        result = orchestrator.run_single(
            script, platforms=[Platform.YOUTUBE], thumbnails=False, subtitles=False
        )

        assert not result.success
        assert "Verify the unsupported claim" in result.errors[0]
        orchestrator._quality_service.evaluate_script.assert_called_once()
        orchestrator._enhancer_service.enhance_script.assert_called_once()
        orchestrator._image_service.generate_for_script.assert_not_called()

    @pytest.mark.parametrize(
        ("score_field", "failed_gate"),
        [
            ("narrative_score", QualityGate.NARRATIVE_FLOW),
            ("information_score", QualityGate.INFORMATION_DENSITY),
            ("engagement_score", QualityGate.ENGAGEMENT_POTENTIAL),
        ],
    )
    def test_strict_quality_rejects_other_weak_gates(
        self,
        pipeline: tuple[Orchestrator, Script, MagicMock],
        score_field: str,
        failed_gate: QualityGate,
    ) -> None:
        orchestrator, script, _ = pipeline
        score = orchestrator._quality_service.evaluate_script.return_value
        setattr(score, score_field, 4.0)
        score.approved_for_production = False
        score.gates_failed = [failed_gate]
        score.improvements = ["Strengthen this section"]

        result = orchestrator.run_single(script, platforms=[Platform.YOUTUBE])

        assert not result.success
        assert failed_gate.value in result.errors[0]
        assert "Strengthen this section" in result.errors[0]
        assert "hook 8.0/10" in result.errors[0]
        assert orchestrator._quality_service.evaluate_script.call_args.kwargs == {
            "strict_mode": True
        }
        orchestrator._image_service.generate_for_script.assert_not_called()

    def test_enhancement_failure_does_not_produce(
        self, pipeline: tuple[Orchestrator, Script, MagicMock]
    ) -> None:
        orchestrator, script, _ = pipeline
        orchestrator._enhancer_service.enhance_script.side_effect = RuntimeError(
            "Azure unavailable"
        )

        result = orchestrator.run_single(script, platforms=[Platform.YOUTUBE])

        assert not result.success
        assert "Script enhancement: Azure unavailable" in result.errors
        orchestrator._quality_service.evaluate_script.assert_not_called()
        orchestrator._image_service.generate_for_script.assert_not_called()
        assert orchestrator._load_or_create_checkpoint(script).completed_steps == []

    def test_quality_ai_error_is_explicit_failure(
        self, pipeline: tuple[Orchestrator, Script, MagicMock]
    ) -> None:
        orchestrator, script, _ = pipeline
        score = orchestrator._quality_service.evaluate_script.return_value
        score.hook_analysis = None

        result = orchestrator.run_single(script, platforms=[Platform.YOUTUBE])

        assert not result.success
        assert "Quality assessment unavailable" in result.errors[0]
        orchestrator._image_service.generate_for_script.assert_not_called()

    def test_explicit_opt_out_still_checks_quality(
        self, pipeline: tuple[Orchestrator, Script, MagicMock], tmp_path: Path
    ) -> None:
        orchestrator, script, thumbnails = pipeline
        source = tmp_path / "user_source.json"
        script.to_json_file(source)

        result = orchestrator.run(
            niche=script.niche,
            script_path=source,
            platforms=[Platform.TIKTOK],
            enhance=False,
            thumbnails=True,
            subtitles=False,
        )[0]

        assert result.success
        orchestrator._enhancer_service.enhance_script.assert_not_called()
        orchestrator._quality_service.evaluate_script.assert_called_once()
        assert orchestrator._quality_service.evaluate_script.call_args.kwargs == {
            "strict_mode": True
        }
        thumbnails.assert_not_called()
        assert Script.from_json_file(source).scenes[0].duration_estimate == 10.0
        assert result.script_path != source
        assert result.script_path is not None and result.script_path.exists()

    def test_default_pipeline_returns_persisted_assets_and_tts_timing(
        self, pipeline: tuple[Orchestrator, Script, MagicMock], tmp_path: Path
    ) -> None:
        orchestrator, script, thumbnails = pipeline
        source = tmp_path / "user_source.json"
        script.to_json_file(source)

        result = orchestrator.run(
            niche=script.niche,
            script_path=source,
            platforms=[Platform.YOUTUBE, Platform.TIKTOK],
        )[0]

        assert result.success
        orchestrator._enhancer_service.enhance_script.assert_called_once()
        orchestrator._quality_service.evaluate_script.assert_called_once()
        assert orchestrator._quality_service.evaluate_script.call_args.kwargs == {
            "strict_mode": True
        }
        assert len(result.video_paths) == 2
        assert result.video_paths["tiktok"].name.endswith("_captioned.mp4")
        assert result.video_paths["tiktok"].read_bytes() == b"captioned"
        assert len(result.thumbnail_paths) == 3
        assert set(result.subtitle_paths) == {"srt", "vtt"}
        thumbnails.assert_called_once()
        assert all(path.exists() for path in result.subtitle_paths.values())
        assert result.script_path is not None
        production = Script.from_json_file(result.script_path)
        assert production.title == "Improved Title"
        assert production.scenes[0].duration_estimate == 4.2
        assert "What was behind the door?" in result.subtitle_paths["srt"].read_text()
        assert "00:00:04,200" in result.subtitle_paths["srt"].read_text()
        assert Script.from_json_file(source).title == "Original Title"
        assert Script.from_json_file(source).scenes[0].duration_estimate == 10.0
        checkpoint = orchestrator._load_or_create_checkpoint(script, source)
        assert checkpoint.status == JobStatus.COMPLETED
        assert checkpoint.script_path == result.script_path
        checkpoint_dir = orchestrator._settings.get_checkpoints_dir(script.niche)
        assert (checkpoint_dir / f"{script.safe_title}.checkpoint.json").exists()
        assert not (
            checkpoint_dir / f"{production.safe_title}.checkpoint.json"
        ).exists()
        assert checkpoint.completed_steps == [
            "enhance",
            "quality",
            "images",
            "audio",
            "videos",
            "subtitles",
            "captions",
            "thumbnails",
        ]

    def test_caption_failure_does_not_generate_thumbnails_and_resumes(
        self, pipeline: tuple[Orchestrator, Script, MagicMock]
    ) -> None:
        orchestrator, script, thumbnails = pipeline
        with patch(
            "faceless.pipeline.orchestrator.burn_subtitles_to_video",
            side_effect=FFmpegError("libass failed"),
        ):
            first = orchestrator.run_single(
                script, platforms=[Platform.YOUTUBE, Platform.TIKTOK]
            )

        assert not first.success
        assert "Portrait caption rendering: libass failed" in first.errors
        assert first.video_paths["tiktok"].name == "tiktok.mp4"
        assert set(first.subtitle_paths) == {"srt", "vtt"}
        checkpoint = orchestrator._load_or_create_checkpoint(script)
        assert "subtitles" in checkpoint.completed_steps
        assert "captions" not in checkpoint.completed_steps
        thumbnails.assert_not_called()

        orchestrator._enhancer_service.enhance_script.reset_mock()
        orchestrator._quality_service.evaluate_script.reset_mock()
        orchestrator._image_service.generate_for_script.reset_mock()
        orchestrator._tts_service.generate_for_script.reset_mock()
        orchestrator._video_service.assemble_video.reset_mock()
        resumed = orchestrator.run_single(
            script, platforms=[Platform.YOUTUBE, Platform.TIKTOK]
        )

        assert resumed.success
        assert resumed.video_paths["tiktok"].name == "tiktok_captioned.mp4"
        assert resumed.video_paths["tiktok"].exists()
        assert (
            "captions"
            in orchestrator._load_or_create_checkpoint(script).completed_steps
        )
        thumbnails.assert_called_once()
        orchestrator._enhancer_service.enhance_script.assert_not_called()
        orchestrator._quality_service.evaluate_script.assert_not_called()
        orchestrator._image_service.generate_for_script.assert_not_called()
        orchestrator._tts_service.generate_for_script.assert_not_called()
        orchestrator._video_service.assemble_video.assert_not_called()

    def test_caption_burn_must_return_the_expected_file(
        self, pipeline: tuple[Orchestrator, Script, MagicMock], tmp_path: Path
    ) -> None:
        orchestrator, script, thumbnails = pipeline
        with patch(
            "faceless.pipeline.orchestrator.burn_subtitles_to_video",
            return_value=tmp_path / "missing.mp4",
        ):
            result = orchestrator.run_single(
                script, platforms=[Platform.TIKTOK], thumbnails=False
            )

        assert not result.success
        assert "did not create the expected video" in result.errors[0]
        assert (
            "captions"
            not in orchestrator._load_or_create_checkpoint(script).completed_steps
        )
        thumbnails.assert_not_called()

    def test_disabling_subtitles_cannot_reuse_a_captioned_checkpoint(
        self, pipeline: tuple[Orchestrator, Script, MagicMock]
    ) -> None:
        orchestrator, script, _ = pipeline
        first = orchestrator.run_single(
            script, platforms=[Platform.TIKTOK], thumbnails=False
        )
        assert first.success

        resumed = orchestrator.run_single(
            script, platforms=[Platform.TIKTOK], thumbnails=False, subtitles=False
        )

        assert not resumed.success
        assert "has captioned TikTok video" in resumed.errors[0]
        assert first.video_paths["tiktok"].is_file()

    def test_resume_rechecks_quality_of_persisted_enhanced_script(
        self, pipeline: tuple[Orchestrator, Script, MagicMock]
    ) -> None:
        orchestrator, script, _ = pipeline
        score = orchestrator._quality_service.evaluate_script.return_value
        score.approved_for_production = False

        first = orchestrator.run_single(
            script, platforms=[Platform.YOUTUBE], thumbnails=False, subtitles=False
        )
        assert not first.success
        assert (
            "enhance" in orchestrator._load_or_create_checkpoint(script).completed_steps
        )
        assert (
            "quality"
            not in orchestrator._load_or_create_checkpoint(script).completed_steps
        )
        orchestrator._enhancer_service.enhance_script.reset_mock()
        orchestrator._quality_service.evaluate_script.reset_mock()
        score.approved_for_production = True

        resumed = orchestrator.run_single(
            script, platforms=[Platform.YOUTUBE], thumbnails=False, subtitles=False
        )

        assert resumed.success
        orchestrator._enhancer_service.enhance_script.assert_not_called()
        assessed = orchestrator._quality_service.evaluate_script.call_args.args[0]
        assert assessed.title == "Improved Title"
        assert assessed.scenes[0].narration == "What was behind the door?"

    def test_quality_only_checkpoint_cannot_skip_default_enhancement(
        self, pipeline: tuple[Orchestrator, Script, MagicMock]
    ) -> None:
        orchestrator, script, _ = pipeline
        first = orchestrator.run_single(
            script,
            platforms=[Platform.YOUTUBE],
            enhance=False,
            thumbnails=False,
            subtitles=False,
        )
        assert first.success
        orchestrator._enhancer_service.enhance_script.reset_mock()
        orchestrator._quality_service.evaluate_script.reset_mock()
        orchestrator._image_service.generate_for_script.reset_mock()

        resumed = orchestrator.run_single(
            script, platforms=[Platform.YOUTUBE], thumbnails=False, subtitles=False
        )

        assert not resumed.success
        assert "quality approval without enhancement" in resumed.errors[0]
        orchestrator._enhancer_service.enhance_script.assert_not_called()
        orchestrator._quality_service.evaluate_script.assert_not_called()
        orchestrator._image_service.generate_for_script.assert_not_called()

    @pytest.mark.parametrize("missing", ["image", "audio"])
    def test_resume_repairs_missing_completed_media(
        self, pipeline: tuple[Orchestrator, Script, MagicMock], missing: str
    ) -> None:
        orchestrator, script, _ = pipeline
        platforms = [Platform.YOUTUBE, Platform.TIKTOK]
        first = orchestrator.run_single(
            script, platforms=platforms, thumbnails=False, subtitles=False
        )
        assert first.success and first.script_path is not None
        production = Script.from_json_file(first.script_path)
        scene = production.scenes[0]
        if missing == "image":
            orchestrator._scene_image_path(production, scene, Platform.TIKTOK).unlink()
        else:
            assert scene.audio_path is not None
            scene.audio_path.unlink()
        orchestrator._enhancer_service.enhance_script.reset_mock()
        orchestrator._quality_service.evaluate_script.reset_mock()
        orchestrator._image_service.generate_for_script.reset_mock()
        orchestrator._tts_service.generate_for_script.reset_mock()
        orchestrator._video_service.assemble_video.reset_mock()

        resumed = orchestrator.run_single(
            script, platforms=platforms, thumbnails=False, subtitles=False
        )

        assert resumed.success, resumed.errors
        assert (
            orchestrator._load_or_create_checkpoint(script).status
            == JobStatus.COMPLETED
        )
        orchestrator._enhancer_service.enhance_script.assert_not_called()
        orchestrator._quality_service.evaluate_script.assert_not_called()
        if missing == "image":
            orchestrator._image_service.generate_for_script.assert_called_once()
            orchestrator._tts_service.generate_for_script.assert_not_called()
            orchestrator._video_service.assemble_video.assert_called_once()
        else:
            orchestrator._image_service.generate_for_script.assert_not_called()
            orchestrator._tts_service.generate_for_script.assert_called_once()
            assert orchestrator._video_service.assemble_video.call_count == 2

    def test_incomplete_images_not_marked_done_or_followed_by_media(
        self, pipeline: tuple[Orchestrator, Script, MagicMock]
    ) -> None:
        orchestrator, script, _ = pipeline
        orchestrator._image_service.generate_for_script.side_effect = None
        orchestrator._image_service.generate_for_script.return_value = []

        result = orchestrator.run_single(script, platforms=[Platform.YOUTUBE])

        assert not result.success
        assert "Incomplete image generation" in result.errors[0]
        assert (
            "images"
            not in orchestrator._load_or_create_checkpoint(script).completed_steps
        )
        orchestrator._tts_service.generate_for_script.assert_not_called()
        orchestrator._video_service.assemble_video.assert_not_called()

    def test_image_paths_must_match_every_requested_platform(
        self, pipeline: tuple[Orchestrator, Script, MagicMock]
    ) -> None:
        orchestrator, script, _ = pipeline
        generate_images = orchestrator._image_service.generate_for_script.side_effect

        def return_wrong_platform_image(
            script: Script, platform: Platform, checkpoint: Checkpoint
        ) -> list[Path]:
            if platform == Platform.YOUTUBE:
                return generate_images(
                    script=script, platform=platform, checkpoint=checkpoint
                )
            assert script.scenes[0].image_path is not None
            return [script.scenes[0].image_path]

        orchestrator._image_service.generate_for_script.side_effect = (
            return_wrong_platform_image
        )

        result = orchestrator.run_single(
            script,
            platforms=[Platform.YOUTUBE, Platform.TIKTOK],
            thumbnails=False,
            subtitles=False,
        )

        assert not result.success
        assert "Incomplete image generation for tiktok" in result.errors[0]
        assert (
            "images"
            not in orchestrator._load_or_create_checkpoint(script).completed_steps
        )
        orchestrator._tts_service.generate_for_script.assert_not_called()
        orchestrator._video_service.assemble_video.assert_not_called()

    def test_returned_audio_without_scene_audio_path_does_not_advance(
        self, pipeline: tuple[Orchestrator, Script, MagicMock], tmp_path: Path
    ) -> None:
        orchestrator, script, _ = pipeline
        unrelated_audio = tmp_path / "unrelated.mp3"
        unrelated_audio.write_bytes(b"audio")
        orchestrator._tts_service.generate_for_script.side_effect = None
        orchestrator._tts_service.generate_for_script.return_value = [unrelated_audio]

        result = orchestrator.run_single(
            script, platforms=[Platform.YOUTUBE], thumbnails=False, subtitles=False
        )

        assert not result.success
        assert "Incomplete audio generation" in result.errors[0]
        assert (
            "audio"
            not in orchestrator._load_or_create_checkpoint(script).completed_steps
        )
        orchestrator._tts_service.update_scene_durations.assert_not_called()
        orchestrator._video_service.assemble_video.assert_not_called()

    def test_partial_audio_return_does_not_advance(
        self, pipeline: tuple[Orchestrator, Script, MagicMock]
    ) -> None:
        orchestrator, script, _ = pipeline
        script.scenes.append(
            Scene(scene_number=2, narration="Another scene", image_prompt="A lantern")
        )
        enhanced = orchestrator._enhancer_service.enhance_script.return_value
        enhanced.scenes.append(
            Scene(scene_number=2, narration="Another scene", image_prompt="A lantern")
        )

        result = orchestrator.run_single(
            script, platforms=[Platform.YOUTUBE], thumbnails=False, subtitles=False
        )

        assert not result.success
        assert "Incomplete audio generation: 1/2" in result.errors[0]
        checkpoint = orchestrator._load_or_create_checkpoint(script)
        assert "images" in checkpoint.completed_steps
        assert "audio" not in checkpoint.completed_steps
        orchestrator._tts_service.update_scene_durations.assert_not_called()
        orchestrator._video_service.assemble_video.assert_not_called()

    def test_failed_audio_does_not_mark_done_or_assemble(
        self, pipeline: tuple[Orchestrator, Script, MagicMock]
    ) -> None:
        orchestrator, script, _ = pipeline
        orchestrator._tts_service.generate_for_script.side_effect = RuntimeError(
            "TTS request failed"
        )

        result = orchestrator.run_single(
            script, platforms=[Platform.YOUTUBE], thumbnails=False, subtitles=False
        )

        assert not result.success
        assert "Audio generation: TTS request failed" in result.errors
        checkpoint = orchestrator._load_or_create_checkpoint(script)
        assert "images" in checkpoint.completed_steps
        assert "audio" not in checkpoint.completed_steps
        orchestrator._video_service.assemble_video.assert_not_called()

    def test_failed_video_does_not_mark_done_or_make_assets(
        self, pipeline: tuple[Orchestrator, Script, MagicMock]
    ) -> None:
        orchestrator, script, thumbnails = pipeline
        orchestrator._video_service.assemble_video.side_effect = RuntimeError(
            "FFmpeg failed"
        )

        result = orchestrator.run_single(script, platforms=[Platform.YOUTUBE])

        assert not result.success
        assert "Video assembly: FFmpeg failed" in result.errors
        checkpoint = orchestrator._load_or_create_checkpoint(script)
        assert "audio" in checkpoint.completed_steps
        assert "videos" not in checkpoint.completed_steps
        thumbnails.assert_not_called()
        assert result.script_path is not None
        assert (
            Script.from_json_file(result.script_path).scenes[0].duration_estimate == 4.2
        )

    @pytest.mark.parametrize("failure", ["none", "partial", "exception"])
    def test_failed_thumbnail_generation_does_not_mark_done(
        self, pipeline: tuple[Orchestrator, Script, MagicMock], failure: str
    ) -> None:
        orchestrator, script, thumbnails = pipeline
        thumbnails.side_effect = None
        if failure == "exception":
            thumbnails.side_effect = RuntimeError("Composition failed")
        elif failure == "partial":
            thumbnails.return_value = [None, None, None]
        else:
            thumbnails.return_value = None

        result = orchestrator.run_single(
            script, platforms=[Platform.YOUTUBE], subtitles=True
        )

        assert not result.success
        assert "Thumbnail generation:" in result.errors[0]
        assert set(result.subtitle_paths) == {"srt", "vtt"}
        checkpoint = orchestrator._load_or_create_checkpoint(script)
        assert checkpoint.status == JobStatus.FAILED
        assert "videos" in checkpoint.completed_steps
        assert "thumbnails" not in checkpoint.completed_steps
        assert "subtitles" in checkpoint.completed_steps

    def test_resume_uses_enhanced_script_and_prior_video_paths(
        self, pipeline: tuple[Orchestrator, Script, MagicMock]
    ) -> None:
        orchestrator, script, thumbnails = pipeline
        generate_thumbnails = thumbnails.side_effect
        thumbnails.side_effect = None
        thumbnails.return_value = [None, None, None]

        first = orchestrator.run_single(
            script, platforms=[Platform.YOUTUBE], subtitles=False
        )
        assert not first.success
        assert (
            "thumbnails"
            not in orchestrator._load_or_create_checkpoint(script).completed_steps
        )
        assert first.video_paths["youtube"].exists()
        thumbnails.side_effect = generate_thumbnails
        orchestrator._enhancer_service.enhance_script.reset_mock()
        orchestrator._quality_service.evaluate_script.reset_mock()
        orchestrator._image_service.generate_for_script.reset_mock()
        orchestrator._tts_service.generate_for_script.reset_mock()
        orchestrator._video_service.assemble_video.reset_mock()

        resumed = orchestrator.run_single(
            script, platforms=[Platform.YOUTUBE], subtitles=False
        )

        assert resumed.success
        assert resumed.video_paths == first.video_paths
        assert resumed.script_path is not None
        assert Script.from_json_file(resumed.script_path).title == "Improved Title"
        orchestrator._enhancer_service.enhance_script.assert_not_called()
        orchestrator._quality_service.evaluate_script.assert_not_called()
        orchestrator._image_service.generate_for_script.assert_not_called()
        orchestrator._tts_service.generate_for_script.assert_not_called()
        orchestrator._video_service.assemble_video.assert_not_called()

    def test_missing_enhanced_snapshot_prevents_original_fallback(
        self, pipeline: tuple[Orchestrator, Script, MagicMock]
    ) -> None:
        orchestrator, script, _ = pipeline
        first = orchestrator.run_single(
            script, platforms=[Platform.YOUTUBE], thumbnails=False, subtitles=False
        )
        assert first.success and first.script_path is not None
        first.script_path.unlink()
        orchestrator._image_service.generate_for_script.reset_mock()

        resumed = orchestrator.run_single(
            script, platforms=[Platform.YOUTUBE], thumbnails=False, subtitles=False
        )

        assert not resumed.success
        assert "Approved production script is missing" in resumed.errors[0]
        orchestrator._image_service.generate_for_script.assert_not_called()

    def test_same_title_different_source_cannot_reuse_approved_checkpoint(
        self, pipeline: tuple[Orchestrator, Script, MagicMock], tmp_path: Path
    ) -> None:
        orchestrator, script, _ = pipeline
        first_source = tmp_path / "original.json"
        second_source = tmp_path / "replacement.json"
        script.to_json_file(first_source)
        replacement = script.model_copy(deep=True)
        replacement.scenes[0].narration = "A completely different opening"
        replacement.to_json_file(second_source)

        first = orchestrator.run(
            niche=script.niche,
            script_path=first_source,
            platforms=[Platform.YOUTUBE],
            thumbnails=False,
            subtitles=False,
        )[0]
        assert first.success
        checkpoint_dir = orchestrator._settings.get_checkpoints_dir(script.niche)
        checkpoint_path = checkpoint_dir / f"{script.safe_title}.checkpoint.json"
        manifest_path = checkpoint_dir / f"{script.safe_title}.result.json"
        saved_checkpoint = checkpoint_path.read_bytes()
        saved_manifest = manifest_path.read_bytes()
        orchestrator._enhancer_service.enhance_script.reset_mock()
        orchestrator._quality_service.evaluate_script.reset_mock()
        orchestrator._image_service.generate_for_script.reset_mock()
        orchestrator._tts_service.generate_for_script.reset_mock()
        orchestrator._video_service.assemble_video.reset_mock()

        rejected = orchestrator.run(
            niche=script.niche,
            script_path=second_source,
            platforms=[Platform.YOUTUBE],
            thumbnails=False,
            subtitles=False,
        )[0]

        assert not rejected.success
        assert "Source content differs" in rejected.errors[0]
        assert checkpoint_path.read_bytes() == saved_checkpoint
        assert manifest_path.read_bytes() == saved_manifest
        orchestrator._enhancer_service.enhance_script.assert_not_called()
        orchestrator._quality_service.evaluate_script.assert_not_called()
        orchestrator._image_service.generate_for_script.assert_not_called()
        orchestrator._tts_service.generate_for_script.assert_not_called()
        orchestrator._video_service.assemble_video.assert_not_called()

        resumed = orchestrator.run(
            niche=script.niche,
            script_path=first_source,
            platforms=[Platform.YOUTUBE],
            thumbnails=False,
            subtitles=False,
        )[0]
        assert resumed.success
        assert resumed.video_paths == first.video_paths
        orchestrator._enhancer_service.enhance_script.assert_not_called()
        orchestrator._quality_service.evaluate_script.assert_not_called()

    def test_no_enhance_resume_uses_same_source_without_extra_ai(
        self, pipeline: tuple[Orchestrator, Script, MagicMock]
    ) -> None:
        orchestrator, script, _ = pipeline
        first = orchestrator.run_single(
            script,
            platforms=[Platform.YOUTUBE],
            enhance=False,
            thumbnails=False,
            subtitles=False,
        )
        assert first.success
        orchestrator._quality_service.evaluate_script.reset_mock()
        orchestrator._tts_service.generate_for_script.reset_mock()

        resumed = orchestrator.run_single(
            script,
            platforms=[Platform.YOUTUBE],
            enhance=False,
            thumbnails=False,
            subtitles=False,
        )

        assert resumed.success
        assert resumed.video_paths == first.video_paths
        orchestrator._enhancer_service.enhance_script.assert_not_called()
        orchestrator._quality_service.evaluate_script.assert_not_called()
        orchestrator._tts_service.generate_for_script.assert_not_called()

    def test_checkpoint_without_source_fingerprint_fails_closed(
        self, pipeline: tuple[Orchestrator, Script, MagicMock]
    ) -> None:
        orchestrator, script, _ = pipeline
        first = orchestrator.run_single(
            script, platforms=[Platform.YOUTUBE], thumbnails=False, subtitles=False
        )
        assert first.success
        checkpoint_dir = orchestrator._settings.get_checkpoints_dir(script.niche)
        checkpoint_path = checkpoint_dir / f"{script.safe_title}.checkpoint.json"
        saved_checkpoint = checkpoint_path.read_bytes()
        (checkpoint_dir / f"{script.safe_title}.source.json").unlink()
        orchestrator._enhancer_service.enhance_script.reset_mock()
        orchestrator._quality_service.evaluate_script.reset_mock()

        resumed = orchestrator.run_single(
            script, platforms=[Platform.YOUTUBE], thumbnails=False, subtitles=False
        )

        assert not resumed.success
        assert "source fingerprint is missing" in resumed.errors[0]
        assert checkpoint_path.read_bytes() == saved_checkpoint
        orchestrator._enhancer_service.enhance_script.assert_not_called()
        orchestrator._quality_service.evaluate_script.assert_not_called()

    def test_new_job_without_checkpoint_ignores_stale_result_manifest(
        self, pipeline: tuple[Orchestrator, Script, MagicMock], tmp_path: Path
    ) -> None:
        orchestrator, script, _ = pipeline
        first_source = tmp_path / "original.json"
        script.to_json_file(first_source)
        first = orchestrator.run(
            niche=script.niche,
            script_path=first_source,
            platforms=[Platform.YOUTUBE],
        )[0]
        assert first.success
        assert first.thumbnail_paths and first.subtitle_paths
        checkpoint_dir = orchestrator._settings.get_checkpoints_dir(script.niche)
        checkpoint_path = checkpoint_dir / f"{script.safe_title}.checkpoint.json"
        previous_id = orchestrator._load_or_create_checkpoint(script).job_id
        checkpoint_path.unlink()
        assert (checkpoint_dir / f"{script.safe_title}.result.json").exists()

        replacement = script.model_copy(deep=True)
        replacement.scenes[0].narration = "New source with the same title"
        second_source = tmp_path / "replacement.json"
        replacement.to_json_file(second_source)
        second = orchestrator.run(
            niche=script.niche,
            script_path=second_source,
            platforms=[Platform.YOUTUBE],
            enhance=False,
            thumbnails=False,
            subtitles=False,
        )[0]

        assert second.success
        assert second.thumbnail_paths == []
        assert second.subtitle_paths == {}
        assert second.script_path is not None
        assert Script.from_json_file(second.script_path).scenes[0].narration == (
            "New source with the same title"
        )
        assert orchestrator._load_or_create_checkpoint(script).job_id != previous_id

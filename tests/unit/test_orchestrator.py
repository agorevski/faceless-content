"""
Unit tests for the pipeline orchestrator.

Tests the main pipeline coordination and job processing.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from faceless.core.enums import JobStatus, Niche, Platform
from faceless.core.exceptions import (
    ImageGenerationError,
    TTSGenerationError,
    VideoAssemblyError,
)
from faceless.core.models import Checkpoint, JobResult, Scene, Script, VisualStyle
from faceless.pipeline.orchestrator import Orchestrator


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
        patch("faceless.pipeline.orchestrator.ImageService"),
        patch("faceless.pipeline.orchestrator.TTSService"),
        patch("faceless.pipeline.orchestrator.VideoService"),
    ):
        settings.return_value.enable_checkpointing = True
        settings.return_value.get_scripts_dir.return_value = tmp_path / "scripts"
        settings.return_value.get_checkpoints_dir.return_value = tmp_path / "checkpoints"
        settings.return_value.get_final_output_dir.return_value = tmp_path / "final"
        settings.return_value.get_images_dir.return_value = tmp_path / "images"
        settings.return_value.get_audio_dir.return_value = tmp_path / "audio"
        orchestrator = Orchestrator()
        orchestrator._client.generate_image.return_value = b"thumbnail"

    def generate_images(
        script: Script, platform: Platform, checkpoint: Checkpoint
    ) -> list[Path]:
        paths = []
        for scene in script.scenes:
            path = tmp_path / f"scene_{scene.scene_number:02d}_{platform.value}.png"
            if not checkpoint.is_image_done(scene.scene_number) or not path.is_file():
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
        path = tmp_path / "final" / f"{script.niche.value}_{script.safe_title}_{platform.value}.mp4"
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(b"video")
        return path

    orchestrator._image_service.generate_for_script.side_effect = generate_images
    orchestrator._tts_service.generate_for_script.side_effect = generate_audio
    orchestrator._tts_service.update_scene_durations.side_effect = update_durations
    orchestrator._video_service.assemble_video.side_effect = assemble
    return orchestrator


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

    failed = orchestrator.run_single(reliability_script, [Platform.YOUTUBE])
    checkpoint = orchestrator._load_or_create_checkpoint(reliability_script)

    assert not failed.success
    assert checkpoint.status == JobStatus.FAILED
    assert stage not in checkpoint.completed_steps
    assert "videos" not in checkpoint.completed_steps
    if partial:
        completed_scenes = (
            checkpoint.images_generated if stage == "images" else checkpoint.audio_generated
        )
        assert completed_scenes == [1]
    orchestrator._video_service.assemble_video.assert_not_called()

    generate.side_effect = original
    resumed = orchestrator.run_single(reliability_script, [Platform.YOUTUBE])

    assert resumed.success, resumed.errors
    assert stage in orchestrator._load_or_create_checkpoint(reliability_script).completed_steps


def test_each_platform_uses_its_own_images(
    reliability_orchestrator: Orchestrator, reliability_script: Script
) -> None:
    result = reliability_orchestrator.run_single(reliability_script)

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
    failed = orchestrator.run_single(reliability_script)

    assert not failed.success
    assert set(failed.video_paths) == {"tiktok"}
    checkpoint = orchestrator._load_or_create_checkpoint(reliability_script)
    assert "images" not in checkpoint.completed_steps
    assert "videos" not in checkpoint.completed_steps

    generate.side_effect = original
    resumed = orchestrator.run_single(reliability_script)

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

    failed = orchestrator.run_single(reliability_script, [Platform.YOUTUBE])
    assert not failed.success

    assemble.side_effect = original
    resumed = orchestrator.run_single(fresh_script, [Platform.YOUTUBE])

    assert resumed.success, resumed.errors
    assert all(scene.image_path is not None for scene in fresh_script.scenes)
    assert all(scene.audio_path is not None for scene in fresh_script.scenes)
    assert all(scene.duration_estimate == 7.5 for scene in fresh_script.scenes)


def test_completed_resume_returns_existing_video_paths(
    reliability_orchestrator: Orchestrator, reliability_script: Script
) -> None:
    orchestrator = reliability_orchestrator
    fresh_script = reliability_script.model_copy(deep=True)
    first = orchestrator.run_single(reliability_script, [Platform.YOUTUBE])
    assert first.success, first.errors
    orchestrator._video_service.assemble_video.reset_mock()

    resumed = orchestrator.run_single(fresh_script, [Platform.YOUTUBE])

    assert resumed.success, resumed.errors
    assert resumed.video_paths == first.video_paths
    orchestrator._video_service.assemble_video.assert_not_called()


def test_resume_repairs_missing_assets_and_final_video(
    reliability_orchestrator: Orchestrator, reliability_script: Script
) -> None:
    orchestrator = reliability_orchestrator
    fresh_script = reliability_script.model_copy(deep=True)
    first = orchestrator.run_single(reliability_script, [Platform.YOUTUBE])
    assert first.success, first.errors
    scene = reliability_script.scenes[0]
    assert scene.image_path is not None
    assert scene.audio_path is not None
    scene.image_path.unlink()
    scene.audio_path.unlink()
    first.video_paths["youtube"].unlink()

    resumed = orchestrator.run_single(fresh_script, [Platform.YOUTUBE])

    assert resumed.success, resumed.errors
    assert scene.image_path.is_file()
    assert scene.audio_path.is_file()
    assert resumed.video_paths["youtube"].is_file()
    assert orchestrator._video_service.assemble_video.call_count == 2


def test_resume_generates_newly_requested_platform(
    reliability_orchestrator: Orchestrator, reliability_script: Script
) -> None:
    orchestrator = reliability_orchestrator
    first = orchestrator.run_single(reliability_script, [Platform.YOUTUBE])
    assert first.success, first.errors
    orchestrator._video_service.assemble_video.reset_mock()

    resumed = orchestrator.run_single(reliability_script)

    assert resumed.success, resumed.errors
    assert set(resumed.video_paths) == {"youtube", "tiktok"}
    orchestrator._video_service.assemble_video.assert_called_once()
    assert orchestrator._video_service.assemble_video.call_args.kwargs["platform"] == Platform.TIKTOK


def test_disabled_checkpointing_ignores_existing_progress(
    reliability_orchestrator: Orchestrator, reliability_script: Script
) -> None:
    orchestrator = reliability_orchestrator
    first = orchestrator.run_single(reliability_script, [Platform.YOUTUBE])
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

        orchestrator = Orchestrator()

        assert isinstance(orchestrator, Orchestrator)
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
        with patch("faceless.pipeline.orchestrator.get_settings") as mock_settings, \
             patch("faceless.pipeline.orchestrator.AzureOpenAIClient"), \
             patch("faceless.pipeline.orchestrator.EnhancerService"), \
             patch("faceless.pipeline.orchestrator.ImageService"), \
             patch("faceless.pipeline.orchestrator.TTSService"), \
             patch("faceless.pipeline.orchestrator.VideoService"):

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
        settings.get_final_output_dir.return_value = tmp_path / "final"
        mock_settings.return_value = settings

        # Setup mocks
        mock_image.return_value.generate_for_script.return_value = [tmp_path / "img.png"]
        mock_tts.return_value.generate_for_script.return_value = [tmp_path / "audio.mp3"]
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
        assert result.success, result.errors

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
        result = orchestrator._process_script(
            script=sample_script,
            platforms=[Platform.YOUTUBE],
            enhance=True,
            thumbnails=False,
            subtitles=False,
            music_path=None,
        )

        mock_enhancer.enhance_script.assert_called_once()
        assert isinstance(result, JobResult)

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
        checkpoint_path = tmp_path / "checkpoints" / f"{sample_script.safe_title}.checkpoint.json"
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

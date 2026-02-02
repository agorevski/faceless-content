"""
Unit tests for the pipeline orchestrator.

Tests the main pipeline coordination and job processing.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from faceless.core.enums import JobStatus, Niche, Platform
from faceless.core.models import Checkpoint, JobResult, Scene, Script, VisualStyle


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
        mock_settings.return_value = settings

        # Setup mocks
        mock_image.return_value.generate_for_script.return_value = [tmp_path / "img.png"]
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
        result = orchestrator._process_script(
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

"""
Unit tests for Pydantic models.

Tests cover:
- Scene model validation
- Script model validation and methods
- VisualStyle model
- Job and Checkpoint models
"""

from pathlib import Path
from uuid import UUID

import pytest

from faceless.core.enums import JobStatus, Niche, Platform
from faceless.core.models import (
    Checkpoint,
    Job,
    JobConfig,
    JobResult,
    Scene,
    Script,
    VisualStyle,
)

# =============================================================================
# Scene Tests
# =============================================================================


class TestScene:
    """Tests for the Scene model."""

    def test_create_valid_scene(self) -> None:
        """Test creating a valid scene."""
        scene = Scene(
            scene_number=1,
            narration="This is the narration text.",
            image_prompt="A beautiful sunset over the ocean.",
            duration_estimate=15.0,
        )
        assert scene.scene_number == 1
        assert scene.narration == "This is the narration text."
        assert scene.image_prompt == "A beautiful sunset over the ocean."
        assert scene.duration_estimate == 15.0

    def test_scene_strips_whitespace(self) -> None:
        """Test that narration and image_prompt are stripped."""
        scene = Scene(
            scene_number=1,
            narration="  Some text with spaces  ",
            image_prompt="  Image prompt  ",
        )
        assert scene.narration == "Some text with spaces"
        assert scene.image_prompt == "Image prompt"

    def test_scene_number_must_be_positive(self) -> None:
        """Test that scene_number must be >= 1."""
        with pytest.raises(ValueError):
            Scene(
                scene_number=0,
                narration="Test",
                image_prompt="Test",
            )

    def test_narration_cannot_be_empty(self) -> None:
        """Test that narration cannot be empty."""
        with pytest.raises(ValueError):
            Scene(
                scene_number=1,
                narration="",
                image_prompt="Test",
            )

    def test_word_count_property(self) -> None:
        """Test the word_count property."""
        scene = Scene(
            scene_number=1,
            narration="This is a five word sentence.",
            image_prompt="Test",
        )
        assert scene.word_count == 6

    def test_estimated_duration_from_words(self) -> None:
        """Test duration estimation from word count."""
        scene = Scene(
            scene_number=1,
            narration=" ".join(["word"] * 150),  # 150 words
            image_prompt="Test",
        )
        # 150 words at 2.5 words/second = 60 seconds
        assert scene.estimated_duration_from_words == 60.0

    def test_scene_default_duration(self) -> None:
        """Test default duration estimate."""
        scene = Scene(
            scene_number=1,
            narration="Test",
            image_prompt="Test",
        )
        assert scene.duration_estimate == 10.0


# =============================================================================
# VisualStyle Tests
# =============================================================================


class TestVisualStyle:
    """Tests for the VisualStyle model."""

    def test_create_visual_style(self) -> None:
        """Test creating a visual style."""
        style = VisualStyle(
            environment="Dark forest",
            color_mood="Blue and gray",
            texture="Rough bark",
            recurring_elements={"tree": "An old oak tree"},
        )
        assert style.environment == "Dark forest"
        assert style.color_mood == "Blue and gray"
        assert "tree" in style.recurring_elements

    def test_to_prompt_suffix(self) -> None:
        """Test generating prompt suffix."""
        style = VisualStyle(
            environment="Dark forest",
            color_mood="Blue and gray",
        )
        suffix = style.to_prompt_suffix()
        assert "Dark forest" in suffix
        assert "Blue and gray" in suffix

    def test_empty_visual_style(self) -> None:
        """Test empty visual style returns empty suffix."""
        style = VisualStyle()
        assert style.to_prompt_suffix() == ""


# =============================================================================
# Script Tests
# =============================================================================


class TestScript:
    """Tests for the Script model."""

    def test_create_valid_script(self, sample_scenes: list[Scene]) -> None:
        """Test creating a valid script."""
        script = Script(
            title="Test Script",
            niche=Niche.SCARY_STORIES,
            scenes=sample_scenes,
        )
        assert script.title == "Test Script"
        assert script.niche == Niche.SCARY_STORIES
        assert len(script.scenes) == 3

    def test_script_auto_fixes_scene_numbers(self) -> None:
        """Test that scene numbers are auto-fixed to be sequential."""
        scenes = [
            Scene(scene_number=5, narration="First", image_prompt="Test"),
            Scene(scene_number=10, narration="Second", image_prompt="Test"),
        ]
        script = Script(
            title="Test",
            niche=Niche.FINANCE,
            scenes=scenes,
        )
        assert script.scenes[0].scene_number == 1
        assert script.scenes[1].scene_number == 2

    def test_script_total_duration(self, sample_scenes: list[Scene]) -> None:
        """Test total duration calculation."""
        script = Script(
            title="Test",
            niche=Niche.SCARY_STORIES,
            scenes=sample_scenes,
        )
        expected = sum(s.duration_estimate for s in sample_scenes)
        assert script.total_duration == expected

    def test_script_total_words(self, sample_scenes: list[Scene]) -> None:
        """Test total word count."""
        script = Script(
            title="Test",
            niche=Niche.SCARY_STORIES,
            scenes=sample_scenes,
        )
        expected = sum(s.word_count for s in sample_scenes)
        assert script.total_words == expected

    def test_script_safe_title(self) -> None:
        """Test safe title generation."""
        script = Script(
            title="The Story! With @Special# Characters?",
            niche=Niche.LUXURY,
            scenes=[Scene(scene_number=1, narration="Test", image_prompt="Test")],
        )
        safe = script.safe_title
        assert "@" not in safe
        assert "#" not in safe
        assert "?" not in safe
        assert "!" not in safe
        assert safe.islower()

    def test_get_scene_by_number(self, sample_script: Script) -> None:
        """Test getting scene by number."""
        scene = sample_script.get_scene(2)
        assert scene is not None
        assert scene.scene_number == 2

    def test_get_scene_returns_none_for_invalid(self, sample_script: Script) -> None:
        """Test getting non-existent scene returns None."""
        scene = sample_script.get_scene(99)
        assert scene is None

    def test_script_serialization(self, sample_script: Script, tmp_path: Path) -> None:
        """Test saving and loading script from JSON."""
        json_path = tmp_path / "test_script.json"
        sample_script.to_json_file(json_path)

        assert json_path.exists()

        loaded = Script.from_json_file(json_path)
        assert loaded.title == sample_script.title
        assert loaded.niche == sample_script.niche
        assert len(loaded.scenes) == len(sample_script.scenes)


# =============================================================================
# Job Tests
# =============================================================================


class TestJob:
    """Tests for Job-related models."""

    def test_create_job_config(self) -> None:
        """Test creating a job config."""
        config = JobConfig(
            niche=Niche.SCARY_STORIES,
            platforms=[Platform.YOUTUBE],
            enhance_script=True,
        )
        assert config.niche == Niche.SCARY_STORIES
        assert Platform.YOUTUBE in config.platforms
        assert config.enhance_script is True

    def test_job_default_status(self) -> None:
        """Test job default status is PENDING."""
        config = JobConfig(niche=Niche.FINANCE)
        job = Job(config=config)
        assert job.status == JobStatus.PENDING

    def test_job_has_uuid(self) -> None:
        """Test job has a UUID id."""
        config = JobConfig(niche=Niche.FINANCE)
        job = Job(config=config)
        assert isinstance(job.id, UUID)

    def test_job_start(self) -> None:
        """Test starting a job."""
        config = JobConfig(niche=Niche.FINANCE)
        job = Job(config=config)
        job.start()
        assert job.started_at is not None

    def test_job_complete_success(self) -> None:
        """Test completing a job successfully."""
        config = JobConfig(niche=Niche.FINANCE)
        job = Job(config=config)
        job.start()

        result = JobResult(success=True)
        job.complete(result)

        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None
        assert job.result is not None
        assert job.result.success is True

    def test_job_complete_failure(self) -> None:
        """Test completing a job with failure."""
        config = JobConfig(niche=Niche.FINANCE)
        job = Job(config=config)
        job.start()

        result = JobResult(success=False, errors=["Something went wrong"])
        job.complete(result)

        assert job.status == JobStatus.FAILED

    def test_job_fail(self) -> None:
        """Test failing a job."""
        config = JobConfig(niche=Niche.FINANCE)
        job = Job(config=config)
        job.start()
        job.fail("Connection error")

        assert job.status == JobStatus.FAILED
        assert job.error_message == "Connection error"

    def test_job_duration(self) -> None:
        """Test job duration calculation."""
        config = JobConfig(niche=Niche.FINANCE)
        job = Job(config=config)

        # Duration is None before completion
        assert job.duration is None

        job.start()
        result = JobResult(success=True)
        job.complete(result)

        # Duration should be non-negative after completion
        assert job.duration is not None
        assert job.duration >= 0


# =============================================================================
# Checkpoint Tests
# =============================================================================


class TestCheckpoint:
    """Tests for Checkpoint model."""

    def test_create_checkpoint(self) -> None:
        """Test creating a checkpoint."""
        from uuid import uuid4

        checkpoint = Checkpoint(
            job_id=uuid4(),
            script_path=Path("/path/to/script.json"),
            status=JobStatus.GENERATING_IMAGES,
        )
        assert checkpoint.status == JobStatus.GENERATING_IMAGES

    def test_mark_image_done(self) -> None:
        """Test marking an image as done."""
        from uuid import uuid4

        checkpoint = Checkpoint(
            job_id=uuid4(),
            script_path=Path("/path/to/script.json"),
            status=JobStatus.GENERATING_IMAGES,
        )

        checkpoint.mark_image_done(1)
        checkpoint.mark_image_done(2)

        assert checkpoint.is_image_done(1)
        assert checkpoint.is_image_done(2)
        assert not checkpoint.is_image_done(3)

    def test_mark_audio_done(self) -> None:
        """Test marking audio as done."""
        from uuid import uuid4

        checkpoint = Checkpoint(
            job_id=uuid4(),
            script_path=Path("/path/to/script.json"),
            status=JobStatus.GENERATING_AUDIO,
        )

        checkpoint.mark_audio_done(1)
        assert checkpoint.is_audio_done(1)
        assert not checkpoint.is_audio_done(2)

    def test_mark_video_done(self) -> None:
        """Test marking video as done."""
        from uuid import uuid4

        checkpoint = Checkpoint(
            job_id=uuid4(),
            script_path=Path("/path/to/script.json"),
            status=JobStatus.ASSEMBLING_VIDEO,
        )

        checkpoint.mark_video_done("youtube", 1)
        checkpoint.mark_video_done("youtube", 2)
        checkpoint.mark_video_done("tiktok", 1)

        assert checkpoint.is_video_done("youtube", 1)
        assert checkpoint.is_video_done("youtube", 2)
        assert checkpoint.is_video_done("tiktok", 1)
        assert not checkpoint.is_video_done("tiktok", 2)

    def test_checkpoint_serialization(self, tmp_path: Path) -> None:
        """Test saving and loading checkpoint."""
        from uuid import uuid4

        checkpoint = Checkpoint(
            job_id=uuid4(),
            script_path=Path("/path/to/script.json"),
            status=JobStatus.GENERATING_IMAGES,
        )
        checkpoint.mark_image_done(1)

        checkpoint_path = tmp_path / "checkpoint.json"
        checkpoint.save(checkpoint_path)

        loaded = Checkpoint.load(checkpoint_path)
        assert loaded.job_id == checkpoint.job_id
        assert loaded.is_image_done(1)

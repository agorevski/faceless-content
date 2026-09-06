"""Regression coverage for real optional pipeline artifacts."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from faceless.clients.azure_openai import AzureOpenAIClient
from faceless.config import Settings
from faceless.core.enums import JobStatus, Niche, Platform
from faceless.core.exceptions import (
    CheckpointError,
    ExternalToolError,
    ImageGenerationError,
)
from faceless.core.models import Checkpoint, JobResult, Scene, Script
from faceless.pipeline.orchestrator import Orchestrator


@pytest.fixture
def script() -> Script:
    """Return narration whose estimated duration differs from generated audio."""
    return Script(
        title="Optional outputs",
        niche=Niche.FINANCE,
        scenes=[
            Scene(
                scene_number=1, narration="First scene narration.", image_prompt="First"
            ),
            Scene(
                scene_number=2,
                narration="Second scene narration.",
                image_prompt="Second",
            ),
        ],
    )


@pytest.fixture
def pipeline(tmp_path: Path) -> Orchestrator:
    """Mock expensive generation but use real thumbnail/subtitle file creation."""
    settings = MagicMock(spec=Settings)
    settings.enable_checkpointing = True
    for kind in ("scripts", "images", "audio", "videos", "checkpoints"):
        getattr(settings, f"get_{kind}_dir").return_value = tmp_path / kind
    settings.get_final_output_dir.return_value = tmp_path / "final"
    client = MagicMock(spec=AzureOpenAIClient)
    client.generate_image.return_value = b"thumbnail"
    with (
        patch("faceless.pipeline.orchestrator.get_settings", return_value=settings),
        patch("faceless.pipeline.orchestrator.AzureOpenAIClient", return_value=client),
        patch("faceless.pipeline.orchestrator.EnhancerService"),
        patch("faceless.pipeline.orchestrator.ImageService"),
        patch("faceless.pipeline.orchestrator.TTSService"),
        patch("faceless.pipeline.orchestrator.VideoService"),
    ):
        result = Orchestrator()

    def images(
        script: Script, platform: Platform, checkpoint: Checkpoint
    ) -> list[Path]:
        paths = []
        for scene in script.scenes:
            scene.image_path = tmp_path / f"{scene.scene_number}_{platform.value}.png"
            scene.image_path.write_bytes(b"scene image")
            checkpoint.mark_image_done(scene.scene_number)
            paths.append(scene.image_path)
        return paths

    def audio(script: Script, checkpoint: Checkpoint) -> list[Path]:
        paths = []
        for scene in script.scenes:
            scene.audio_path = tmp_path / f"{scene.scene_number}.mp3"
            scene.audio_path.write_bytes(b"narration")
            checkpoint.mark_audio_done(scene.scene_number)
            paths.append(scene.audio_path)
        return paths

    def durations(script: Script) -> None:
        for scene in script.scenes:
            scene.duration_estimate = 7.5

    def video(
        script: Script,
        platform: Platform,
        checkpoint: Checkpoint,
        music_path: Path | None,
    ) -> Path:
        path = (
            tmp_path
            / "final"
            / f"{script.niche.value}_{script.safe_title}_{platform.value}.mp4"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"video")
        return path

    result._image_service.generate_for_script.side_effect = images
    result._tts_service.generate_for_script.side_effect = audio
    result._tts_service.update_scene_durations.side_effect = durations
    result._video_service.assemble_video.side_effect = video
    return result


def process(
    pipeline: Orchestrator,
    script: Script,
    thumbnails: bool = True,
    subtitles: bool = True,
) -> JobResult:
    """Run a single YouTube production with explicit optional stages."""
    return pipeline._process_script(
        script, [Platform.YOUTUBE], False, thumbnails, subtitles, None
    )


@pytest.mark.parametrize(
    "thumbnails,subtitles", [(True, True), (False, False), (True, False), (False, True)]
)
def test_requested_outputs_are_created_and_reported(
    pipeline: Orchestrator, script: Script, thumbnails: bool, subtitles: bool
) -> None:
    result = process(pipeline, script, thumbnails, subtitles)

    assert result.success, result.errors
    assert len(result.thumbnail_paths) == (3 if thumbnails else 0)
    assert set(result.subtitle_paths) == ({"srt", "vtt"} if subtitles else set())
    assert all(path.is_file() for path in result.thumbnail_paths)
    assert all(path.is_file() for path in result.subtitle_paths.values())
    checkpoint = pipeline._load_or_create_checkpoint(script)
    assert ("thumbnails" in checkpoint.completed_steps) == thumbnails
    assert ("subtitles" in checkpoint.completed_steps) == subtitles
    assert pipeline._client.generate_image.call_count == (3 if thumbnails else 0)
    assert result.script_path is not None and result.script_path.is_file()
    production = Script.from_json_file(result.script_path)
    assert production.total_duration == 15.0
    assert production.output_paths == result.video_paths
    if subtitles:
        assert "00:00:15,000" in result.subtitle_paths["srt"].read_text(
            encoding="utf-8"
        )
        assert "First scene narration." in result.subtitle_paths["srt"].read_text(
            encoding="utf-8"
        )


def test_partial_thumbnail_failure_preserves_video_and_subtitles(
    pipeline: Orchestrator, script: Script
) -> None:
    pipeline._client.generate_image.side_effect = [
        b"first",
        ImageGenerationError("Throttled thumbnail"),
        b"third",
    ]

    failed = process(pipeline, script)

    assert not failed.success
    assert len(failed.thumbnail_paths) == 2
    assert failed.video_paths["youtube"].is_file()
    assert set(failed.subtitle_paths) == {"srt", "vtt"}
    checkpoint = pipeline._load_or_create_checkpoint(script)
    assert "thumbnails" not in checkpoint.completed_steps
    assert "subtitles" in checkpoint.completed_steps
    assert any("Thumbnail" in error for error in failed.errors)

    pipeline._client.generate_image.side_effect = None
    pipeline._client.generate_image.reset_mock()
    pipeline._video_service.assemble_video.reset_mock()
    resumed = process(pipeline, script)

    assert resumed.success, resumed.errors
    assert len(resumed.thumbnail_paths) == 3
    pipeline._client.generate_image.assert_called_once()
    pipeline._video_service.assemble_video.assert_not_called()


def test_legacy_completion_markers_do_not_hide_missing_outputs(
    pipeline: Orchestrator, script: Script
) -> None:
    first = process(pipeline, script, thumbnails=False, subtitles=False)
    assert first.success
    checkpoint = pipeline._load_or_create_checkpoint(script)
    checkpoint.completed_steps.extend(["thumbnails", "subtitles"])
    pipeline._save_checkpoint(checkpoint, script)

    resumed = process(pipeline, script)

    assert resumed.success, resumed.errors
    assert len(resumed.thumbnail_paths) == 3
    assert set(resumed.subtitle_paths) == {"srt", "vtt"}
    assert all(path.is_file() for path in resumed.thumbnail_paths)
    assert all(path.is_file() for path in resumed.subtitle_paths.values())


def test_resume_repairs_missing_subtitles_and_returns_existing_thumbnails(
    pipeline: Orchestrator, script: Script
) -> None:
    first = process(pipeline, script)
    assert first.success
    first.subtitle_paths["vtt"].unlink()
    pipeline._client.generate_image.reset_mock()

    resumed = process(pipeline, script)

    assert resumed.success, resumed.errors
    assert resumed.thumbnail_paths == first.thumbnail_paths
    assert resumed.subtitle_paths == first.subtitle_paths
    assert resumed.subtitle_paths["vtt"].is_file()
    pipeline._client.generate_image.assert_not_called()


def test_subtitle_failure_retains_successful_artifacts(
    pipeline: Orchestrator, script: Script
) -> None:
    with patch(
        "faceless.pipeline.orchestrator.create_subtitles_from_script",
        side_effect=OSError("Subtitle directory is read-only"),
    ):
        failed = process(pipeline, script)

    assert not failed.success
    assert failed.video_paths["youtube"].is_file()
    assert len(failed.thumbnail_paths) == 3
    assert failed.subtitle_paths == {}
    assert any("Subtitle" in error for error in failed.errors)
    assert (
        "subtitles" not in pipeline._load_or_create_checkpoint(script).completed_steps
    )

    resumed = process(pipeline, script)
    assert resumed.success, resumed.errors
    assert set(resumed.subtitle_paths) == {"srt", "vtt"}


def test_invalid_audio_duration_stops_video_and_optional_outputs(
    pipeline: Orchestrator, script: Script
) -> None:
    pipeline._tts_service.update_scene_durations.side_effect = ExternalToolError(
        "FFprobe returned an invalid duration"
    )

    result = process(pipeline, script)

    assert not result.success
    assert result.video_paths == {}
    assert result.thumbnail_paths == []
    assert result.subtitle_paths == {}
    pipeline._video_service.assemble_video.assert_not_called()
    pipeline._client.generate_image.assert_not_called()
    assert "audio" not in pipeline._load_or_create_checkpoint(script).completed_steps
    assert any("invalid duration" in error for error in result.errors)


def test_production_script_failure_is_reported_without_losing_artifacts(
    pipeline: Orchestrator, script: Script
) -> None:
    with patch.object(Script, "to_json_file", side_effect=OSError("Read-only script")):
        failed = process(pipeline, script)

    assert not failed.success
    assert failed.video_paths["youtube"].is_file()
    assert len(failed.thumbnail_paths) == 3
    assert failed.subtitle_paths == {}
    assert any(
        "Production script: Read-only script" in error for error in failed.errors
    )
    assert (
        "subtitles" not in pipeline._load_or_create_checkpoint(script).completed_steps
    )

    pipeline._client.generate_image.reset_mock()
    resumed = process(pipeline, script)

    assert resumed.success, resumed.errors
    assert resumed.script_path is not None and resumed.script_path.is_file()
    assert set(resumed.subtitle_paths) == {"srt", "vtt"}
    pipeline._client.generate_image.assert_not_called()


def test_checkpoint_failure_retains_generated_artifacts(
    pipeline: Orchestrator, script: Script
) -> None:
    save = pipeline._save_checkpoint

    def fail_final_save(checkpoint: Checkpoint, script: Script) -> None:
        if checkpoint.status == JobStatus.COMPLETED:
            raise CheckpointError("Checkpoint disk error")
        save(checkpoint, script)

    with patch.object(pipeline, "_save_checkpoint", side_effect=fail_final_save):
        result = process(pipeline, script)

    assert not result.success
    assert result.video_paths["youtube"].is_file()
    assert len(result.thumbnail_paths) == 3
    assert set(result.subtitle_paths) == {"srt", "vtt"}
    assert result.script_path is not None and result.script_path.is_file()
    assert any("Checkpoint disk error" in error for error in result.errors)

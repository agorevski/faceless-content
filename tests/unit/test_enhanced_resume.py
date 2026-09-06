"""Regression tests for durable enhanced scripts and checkpoint identities."""

import json
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from faceless.core.enums import JobStatus, Niche, Platform
from faceless.core.exceptions import CheckpointError, VideoAssemblyError
from faceless.core.models import Checkpoint, JobResult, Scene, Script, VisualStyle
from faceless.pipeline.orchestrator import Orchestrator


@dataclass
class ResumeHarness:
    orchestrator: Orchestrator
    settings: MagicMock
    enhancer: MagicMock
    images: MagicMock
    audio: MagicMock
    video: MagicMock
    source: Script
    enhanced: Script
    source_path: Path
    checkpoint_path: Path
    asset_requests: list[tuple[str, int]]

    def run(self, enhance: bool = True) -> JobResult:
        return self.orchestrator.run(
            niche=self.source.niche,
            platforms=[Platform.YOUTUBE],
            script_path=self.source_path,
            enhance=enhance,
            thumbnails=False,
            subtitles=False,
        )[0]


@pytest.fixture
def resume_harness(tmp_path: Path) -> ResumeHarness:
    source = Script(
        title="Original title",
        niche=Niche.FINANCE,
        scenes=[Scene(scene_number=1, narration="Original words", image_prompt="Old")],
    )
    enhanced = Script(
        title="A better title",
        niche=Niche.FINANCE,
        scenes=[
            Scene(
                scene_number=number,
                narration=f"Enhanced narration {number}",
                image_prompt=f"Enhanced image {number}",
                duration_estimate=12.0,
            )
            for number in (1, 2)
        ],
        visual_style=VisualStyle(environment="City", color_mood="Gold", texture="Film"),
    )
    source_path = tmp_path / "scripts" / "original-title_script.json"
    source.to_json_file(source_path)
    with (
        patch("faceless.pipeline.orchestrator.get_settings") as get_settings,
        patch("faceless.pipeline.orchestrator.AzureOpenAIClient"),
        patch("faceless.pipeline.orchestrator.EnhancerService") as enhancer_class,
        patch("faceless.pipeline.orchestrator.ImageService") as images_class,
        patch("faceless.pipeline.orchestrator.TTSService") as audio_class,
        patch("faceless.pipeline.orchestrator.VideoService") as video_class,
    ):
        settings = get_settings.return_value
        settings.enable_checkpointing = True
        settings.get_scripts_dir.return_value = source_path.parent
        settings.get_checkpoints_dir.return_value = tmp_path / "checkpoints"
        settings.get_final_output_dir.return_value = tmp_path / "final"
        settings.get_images_dir.return_value = tmp_path / "images"
        settings.get_audio_dir.return_value = tmp_path / "audio"
        orchestrator = Orchestrator()
        orchestrator._client.generate_image.return_value = b"thumbnail"
        enhancer = enhancer_class.return_value
        images = images_class.return_value
        audio = audio_class.return_value
        video = video_class.return_value

    requests: list[tuple[str, int]] = []

    def enhance_script(script: Script) -> Script:
        # Mutating service implementations must not change the caller's script.
        script.scenes[0].narration = "Service mutated its input"
        return enhanced.model_copy(deep=True)

    def generate_images(
        script: Script, platform: Platform, checkpoint: Checkpoint
    ) -> list[Path]:
        directory = tmp_path / "images" / script.safe_title
        directory.mkdir(parents=True, exist_ok=True)
        paths = []
        for scene in script.scenes:
            path = directory / f"scene_{scene.scene_number:02d}_{platform.value}.png"
            if not checkpoint.is_image_done(scene.scene_number) or not path.is_file():
                requests.append(("image", scene.scene_number))
                path.write_text(scene.image_prompt, encoding="utf-8")
            scene.image_path = path
            checkpoint.mark_image_done(scene.scene_number)
            paths.append(path)
        return paths

    def generate_audio(script: Script, checkpoint: Checkpoint) -> list[Path]:
        directory = tmp_path / "audio" / script.safe_title
        directory.mkdir(parents=True, exist_ok=True)
        paths = []
        for scene in script.scenes:
            path = directory / f"scene_{scene.scene_number:02d}.mp3"
            if not checkpoint.is_audio_done(scene.scene_number) or not path.is_file():
                requests.append(("audio", scene.scene_number))
                path.write_text(scene.narration, encoding="utf-8")
            scene.audio_path = path
            checkpoint.mark_audio_done(scene.scene_number)
            paths.append(path)
        return paths

    def update_durations(script: Script) -> None:
        for scene in script.scenes:
            scene.duration_estimate = 7.5 + scene.scene_number

    def assemble(
        script: Script,
        platform: Platform,
        checkpoint: Checkpoint,
        music_path: Path | None,
    ) -> Path:
        for scene in script.scenes:
            assert scene.image_path is not None
            assert scene.audio_path is not None
            assert scene.image_path.read_text(encoding="utf-8") == scene.image_prompt
            assert scene.audio_path.read_text(encoding="utf-8") == scene.narration
            assert scene.duration_estimate == 7.5 + scene.scene_number
        path = (
            tmp_path
            / "final"
            / f"{script.niche.value}_{script.safe_title}_{platform.value}.mp4"
        )
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(b"video")
        return path

    enhancer.enhance_script.side_effect = enhance_script
    images.generate_for_script.side_effect = generate_images
    audio.generate_for_script.side_effect = generate_audio
    audio.update_scene_durations.side_effect = update_durations
    video.assemble_video.side_effect = assemble
    return ResumeHarness(
        orchestrator,
        settings,
        enhancer,
        images,
        audio,
        video,
        source,
        enhanced,
        source_path,
        tmp_path / "checkpoints" / "original-title.checkpoint.json",
        requests,
    )


@pytest.mark.parametrize("resume_enhance", [False, True])
def test_resume_restores_exact_enhancement_without_paid_calls(
    resume_harness: ResumeHarness, resume_enhance: bool
) -> None:
    harness = resume_harness
    original_bytes = harness.source_path.read_bytes()
    assemble = harness.video.assemble_video.side_effect
    harness.video.assemble_video.side_effect = VideoAssemblyError("Interrupted")

    first = harness.run()
    assert not first.success
    checkpoint = Checkpoint.load(harness.checkpoint_path)
    assert checkpoint.enhanced_script == harness.enhanced
    assert checkpoint.completed_steps == ["enhance", "images", "audio"]
    assert checkpoint.script_path == harness.source_path
    assert list(harness.checkpoint_path.parent.glob("*.checkpoint.json")) == [
        harness.checkpoint_path
    ]
    requests = list(harness.asset_requests)

    harness.video.assemble_video.side_effect = assemble
    resumed = harness.run(enhance=resume_enhance)

    assert resumed.success, resumed.errors
    harness.enhancer.enhance_script.assert_called_once()
    assert harness.asset_requests == requests
    restored = harness.video.assemble_video.call_args.kwargs["script"]
    assert restored.title == harness.enhanced.title
    assert restored.visual_style == harness.enhanced.visual_style
    assert len(restored.scenes) == 2
    assert restored.scenes[1].duration_estimate == 9.5
    assert harness.source_path.read_bytes() == original_bytes
    assert Checkpoint.load(harness.checkpoint_path).enhanced_script == harness.enhanced


def test_snapshot_is_durable_before_first_asset_generation(
    resume_harness: ResumeHarness,
) -> None:
    harness = resume_harness

    def interrupt(
        script: Script, platform: Platform, checkpoint: Checkpoint
    ) -> list[Path]:
        saved = Checkpoint.load(harness.checkpoint_path)
        assert saved.enhanced_script == harness.enhanced
        assert saved.completed_steps == ["enhance"]
        raise KeyboardInterrupt

    original = harness.images.generate_for_script.side_effect
    harness.images.generate_for_script.side_effect = interrupt
    with pytest.raises(KeyboardInterrupt):
        harness.run()
    harness.images.generate_for_script.side_effect = original

    resumed = harness.run()
    assert resumed.success, resumed.errors
    harness.enhancer.enhance_script.assert_called_once()


@pytest.mark.parametrize(
    "corruption",
    [
        "missing_snapshot",
        "invalid_snapshot",
        "wrong_niche",
        "missing_marker",
        "invalid_json",
    ],
)
def test_corrupt_or_legacy_enhancement_fails_before_assets(
    resume_harness: ResumeHarness, corruption: str
) -> None:
    harness = resume_harness
    assert harness.run().success
    data = json.loads(harness.checkpoint_path.read_text(encoding="utf-8"))
    if corruption == "missing_snapshot":
        data.pop("enhanced_script")
    elif corruption == "invalid_snapshot":
        data["enhanced_script"]["scenes"] = []
    elif corruption == "wrong_niche":
        data["enhanced_script"]["niche"] = Niche.SCARY_STORIES.value
    elif corruption == "missing_marker":
        data["completed_steps"].remove("enhance")
    harness.checkpoint_path.write_text(
        "invalid json" if corruption == "invalid_json" else json.dumps(data),
        encoding="utf-8",
    )
    for service in (harness.enhancer, harness.images, harness.audio, harness.video):
        service.reset_mock()

    result = harness.run(enhance=False)

    assert not result.success
    assert "snapshot" in result.errors[0]
    harness.enhancer.enhance_script.assert_not_called()
    harness.images.generate_for_script.assert_not_called()
    harness.audio.generate_for_script.assert_not_called()
    harness.video.assemble_video.assert_not_called()


def test_disabled_checkpointing_ignores_snapshot_and_regenerates(
    resume_harness: ResumeHarness,
) -> None:
    harness = resume_harness
    assert harness.run().success
    checkpoint_bytes = harness.checkpoint_path.read_bytes()
    harness.settings.enable_checkpointing = False
    harness.enhanced.scenes[0].narration = "New enhancement"

    result = harness.run()

    assert result.success, result.errors
    assert harness.enhancer.enhance_script.call_count == 2
    assert harness.checkpoint_path.read_bytes() == checkpoint_bytes
    script = harness.audio.generate_for_script.call_args.kwargs["script"]
    assert script.scenes[0].narration == "New enhancement"


def test_enhancement_invalidates_unenhanced_asset_markers(
    resume_harness: ResumeHarness,
) -> None:
    harness = resume_harness
    assert harness.run(enhance=False).success
    harness.enhanced.title = harness.source.title
    harness.asset_requests.clear()

    result = harness.run()

    assert result.success, result.errors
    assert harness.asset_requests == [
        ("image", 1),
        ("image", 2),
        ("audio", 1),
        ("audio", 2),
    ]


def test_atomic_checkpoint_failure_preserves_previous_file(
    resume_harness: ResumeHarness,
) -> None:
    harness = resume_harness
    assert harness.run().success
    previous = harness.checkpoint_path.read_bytes()
    checkpoint = Checkpoint.load(harness.checkpoint_path)
    checkpoint.status = JobStatus.FAILED

    with (
        patch.object(Path, "replace", side_effect=OSError("Disk error")),
        pytest.raises(CheckpointError, match="Cannot persist"),
    ):
        harness.orchestrator._save_checkpoint(checkpoint, harness.enhanced)

    assert harness.checkpoint_path.read_bytes() == previous
    assert list(harness.checkpoint_path.parent.glob("*.pending")) == []


def test_snapshot_persistence_failure_blocks_asset_generation(
    resume_harness: ResumeHarness,
) -> None:
    harness = resume_harness
    with patch.object(Path, "replace", side_effect=OSError("Disk error")):
        result = harness.run()

    assert not result.success
    assert "Cannot persist" in result.errors[0]
    harness.images.generate_for_script.assert_not_called()
    harness.audio.generate_for_script.assert_not_called()
    assert not harness.checkpoint_path.exists()


def test_enhancer_mutation_does_not_change_callers_script(
    resume_harness: ResumeHarness,
) -> None:
    harness = resume_harness
    original = harness.source.model_copy(deep=True)
    result = harness.orchestrator._process_script(
        script=harness.source,
        platforms=[Platform.YOUTUBE],
        enhance=True,
        thumbnails=False,
        subtitles=False,
        music_path=None,
    )

    assert result.success, result.errors
    assert harness.source == original


@pytest.mark.parametrize("has_snapshot", [False, True])
def test_finds_legacy_checkpoint_saved_under_enhanced_title(
    resume_harness: ResumeHarness, has_snapshot: bool
) -> None:
    harness = resume_harness
    assert harness.run().success
    data = json.loads(harness.checkpoint_path.read_text(encoding="utf-8"))
    if not has_snapshot:
        data.pop("enhanced_script")
    legacy_path = harness.checkpoint_path.with_name("a-better-title.checkpoint.json")
    legacy_path.write_text(json.dumps(data), encoding="utf-8")
    harness.checkpoint_path.unlink()
    harness.enhancer.reset_mock()
    harness.images.reset_mock()

    result = harness.run()

    assert result.success is has_snapshot
    harness.enhancer.enhance_script.assert_not_called()
    if has_snapshot:
        assert result.script_path is not None and result.script_path.is_file()
        assert Script.from_json_file(result.script_path).title == harness.enhanced.title
        assert harness.checkpoint_path.is_file()
        assert Checkpoint.load(harness.checkpoint_path).script_path == harness.source_path
    else:
        assert "no script snapshot" in result.errors[0]
        harness.images.generate_for_script.assert_not_called()


def test_disabled_checkpointing_creates_no_checkpoint_files(
    resume_harness: ResumeHarness,
) -> None:
    harness = resume_harness
    harness.settings.enable_checkpointing = False

    assert harness.run().success
    assert harness.run().success

    assert harness.enhancer.enhance_script.call_count == 2
    assert not harness.checkpoint_path.parent.exists()


def test_optional_outputs_use_restored_enhanced_narration_and_measured_timing(
    resume_harness: ResumeHarness,
) -> None:
    harness = resume_harness
    assert harness.run().success
    original_source = harness.source_path.read_bytes()
    harness.video.assemble_video.reset_mock()

    result = harness.orchestrator.run(
        niche=harness.source.niche,
        platforms=[Platform.YOUTUBE],
        script_path=harness.source_path,
        enhance=False,
        thumbnails=True,
        subtitles=True,
    )[0]

    assert result.success, result.errors
    assert len(result.thumbnail_paths) == 3
    subtitle_text = result.subtitle_paths["srt"].read_text(encoding="utf-8")
    assert "Enhanced narration 1" in subtitle_text
    assert "Original words" not in subtitle_text
    assert "00:00:18,000" in subtitle_text
    assert result.script_path is not None
    production_script = Script.from_json_file(result.script_path)
    assert production_script.title == harness.enhanced.title
    assert production_script.total_duration == 18.0
    assert harness.source_path.read_bytes() == original_source
    harness.enhancer.enhance_script.assert_called_once()
    harness.video.assemble_video.assert_not_called()

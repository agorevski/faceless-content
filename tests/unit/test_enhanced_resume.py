"""Regression tests for durable enhanced scripts and checkpoint identities."""

import json
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from faceless.clients.azure_openai import AzureOpenAIClient
from faceless.core.enums import JobStatus, Niche, Platform
from faceless.core.exceptions import CheckpointError, VideoAssemblyError
from faceless.core.models import Checkpoint, JobResult, Scene, Script, VisualStyle
from faceless.pipeline.orchestrator import Orchestrator
from faceless.services.quality_service import HookAnalysis, QualityScore


@dataclass
class ResumeHarness:
    orchestrator: Orchestrator
    settings: MagicMock
    enhancer: MagicMock
    quality: MagicMock
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
        patch("faceless.pipeline.orchestrator.QualityService") as quality_class,
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
        quality = quality_class.return_value
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

    def evaluate_quality(script: Script, strict_mode: bool) -> QualityScore:
        assert strict_mode is True
        return QualityScore(
            script_title=script.title,
            niche=script.niche,
            overall_score=8.5,
            hook_score=8.0,
            hook_analysis=HookAnalysis(
                score=8.0,
                hook_type="story",
                attention_grab=0.8,
                curiosity_gap=0.8,
            ),
            approved_for_production=True,
        )

    quality.evaluate_script.side_effect = evaluate_quality
    images.generate_for_script.side_effect = generate_images
    audio.generate_for_script.side_effect = generate_audio
    audio.update_scene_durations.side_effect = update_durations
    video.assemble_video.side_effect = assemble
    return ResumeHarness(
        orchestrator,
        settings,
        enhancer,
        quality,
        images,
        audio,
        video,
        source,
        enhanced,
        source_path,
        tmp_path / "checkpoints" / "original-title.checkpoint.json",
        requests,
    )


def test_resume_restores_exact_enhancement_without_paid_calls(
    resume_harness: ResumeHarness,
) -> None:
    harness = resume_harness
    original_bytes = harness.source_path.read_bytes()
    assemble = harness.video.assemble_video.side_effect
    harness.video.assemble_video.side_effect = VideoAssemblyError("Interrupted")

    first = harness.run()
    assert not first.success
    checkpoint = Checkpoint.load(harness.checkpoint_path)
    snapshot = checkpoint.enhanced_script
    assert snapshot is not None
    assert snapshot.title == harness.enhanced.title
    assert snapshot.visual_style == harness.enhanced.visual_style
    assert [scene.narration for scene in snapshot.scenes] == [
        scene.narration for scene in harness.enhanced.scenes
    ]
    assert [scene.duration_estimate for scene in snapshot.scenes] == [8.5, 9.5]
    assert checkpoint.completed_steps == ["enhance", "quality", "images", "audio"]
    assert checkpoint.script_path == harness.source_path.with_name(
        "original-title_production.json"
    )
    assert Script.from_json_file(checkpoint.script_path) == snapshot
    assert list(harness.checkpoint_path.parent.glob("*.checkpoint.json")) == [
        harness.checkpoint_path
    ]
    requests = list(harness.asset_requests)

    harness.video.assemble_video.side_effect = assemble
    resumed = harness.run()

    assert resumed.success, resumed.errors
    harness.enhancer.enhance_script.assert_called_once()
    harness.quality.evaluate_script.assert_called_once()
    assert harness.asset_requests == requests
    restored = harness.video.assemble_video.call_args.kwargs["script"]
    assert restored.title == harness.enhanced.title
    assert restored.visual_style == harness.enhanced.visual_style
    assert len(restored.scenes) == 2
    assert restored.scenes[1].duration_estimate == 9.5
    assert harness.source_path.read_bytes() == original_bytes
    assert Checkpoint.load(harness.checkpoint_path).enhanced_script == snapshot


def test_no_enhance_cannot_resume_enhanced_checkpoint(
    resume_harness: ResumeHarness,
) -> None:
    harness = resume_harness
    assert harness.run().success
    source_bytes = harness.source_path.read_bytes()
    for service in (
        harness.enhancer,
        harness.quality,
        harness.images,
        harness.audio,
        harness.video,
    ):
        service.reset_mock()

    result = harness.run(enhance=False)

    assert not result.success
    assert "checkpoint uses an enhanced script" in result.errors[0]
    harness.enhancer.enhance_script.assert_not_called()
    harness.quality.evaluate_script.assert_not_called()
    harness.images.generate_for_script.assert_not_called()
    harness.audio.generate_for_script.assert_not_called()
    harness.video.assemble_video.assert_not_called()
    assert harness.source_path.read_bytes() == source_bytes
    assert Checkpoint.load(harness.checkpoint_path).completed_steps == [
        "enhance",
        "quality",
        "images",
        "audio",
        "videos",
    ]


def test_snapshot_is_durable_before_first_asset_generation(
    resume_harness: ResumeHarness,
) -> None:
    harness = resume_harness

    def interrupt(
        script: Script, platform: Platform, checkpoint: Checkpoint
    ) -> list[Path]:
        saved = Checkpoint.load(harness.checkpoint_path)
        assert saved.enhanced_script == harness.enhanced
        assert saved.completed_steps == ["enhance", "quality"]
        assert saved.script_path.is_file()
        assert Script.from_json_file(saved.script_path) == harness.enhanced
        raise KeyboardInterrupt

    original = harness.images.generate_for_script.side_effect
    harness.images.generate_for_script.side_effect = interrupt
    with pytest.raises(KeyboardInterrupt):
        harness.run()
    harness.images.generate_for_script.side_effect = original

    resumed = harness.run()
    assert resumed.success, resumed.errors
    harness.enhancer.enhance_script.assert_called_once()


def test_strict_quality_rejection_preserves_source_and_blocks_assets(
    resume_harness: ResumeHarness,
) -> None:
    harness = resume_harness
    original_source = harness.source_path.read_bytes()

    def reject_quality(script: Script, strict_mode: bool) -> QualityScore:
        assert strict_mode is True
        return QualityScore(
            script_title=script.title,
            niche=script.niche,
            overall_score=5.0,
            hook_score=6.0,
            hook_analysis=HookAnalysis(
                score=6.0,
                hook_type="story",
                attention_grab=0.5,
                curiosity_gap=0.5,
            ),
            critical_issues=["Unverified factual claim"],
            approved_for_production=False,
        )

    harness.quality.evaluate_script.side_effect = reject_quality

    result = harness.run()

    assert not result.success
    assert "Script rejected by quality gate" in result.errors[0]
    assert "minimum 7.0" in result.errors[0]
    assert harness.source_path.read_bytes() == original_source
    assert Checkpoint.load(harness.checkpoint_path).completed_steps == ["enhance"]
    harness.enhancer.enhance_script.assert_called_once()
    harness.quality.evaluate_script.assert_called_once()
    harness.images.generate_for_script.assert_not_called()
    harness.audio.generate_for_script.assert_not_called()
    harness.video.assemble_video.assert_not_called()


@pytest.mark.parametrize(
    "corruption",
    [
        "missing_production",
        "invalid_production",
        "wrong_niche",
        "missing_marker",
        "invalid_json",
        "invalid_metadata",
        "missing_fingerprint",
        "changed_source",
    ],
)
def test_corrupt_checkpoint_or_production_fails_before_assets(
    resume_harness: ResumeHarness, corruption: str
) -> None:
    harness = resume_harness
    assert harness.run().success
    data = json.loads(harness.checkpoint_path.read_text(encoding="utf-8"))
    production_path = Path(data["script_path"])
    if corruption == "missing_production":
        production_path.unlink()
    elif corruption == "invalid_production":
        production_path.write_text("invalid json", encoding="utf-8")
    elif corruption == "wrong_niche":
        production = Script.from_json_file(production_path)
        production.niche = Niche.SCARY_STORIES
        production.to_json_file(production_path)
    elif corruption == "missing_marker":
        data["completed_steps"].remove("enhance")
        harness.checkpoint_path.write_text(json.dumps(data), encoding="utf-8")
    elif corruption == "invalid_json":
        harness.checkpoint_path.write_text("invalid json", encoding="utf-8")
    elif corruption == "invalid_metadata":
        data["enhanced_script"]["scenes"] = []
        harness.checkpoint_path.write_text(json.dumps(data), encoding="utf-8")
    elif corruption == "missing_fingerprint":
        harness.checkpoint_path.with_name("original-title.source.json").unlink()
    elif corruption == "changed_source":
        changed = Script.from_json_file(harness.source_path)
        changed.scenes[0].narration = "Different source narration"
        changed.to_json_file(harness.source_path)
    source_bytes = harness.source_path.read_bytes()
    for service in (
        harness.enhancer,
        harness.quality,
        harness.images,
        harness.audio,
        harness.video,
    ):
        service.reset_mock()

    result = harness.run()

    assert not result.success
    expected_error = {
        "missing_production": "Approved production script is missing",
        "invalid_production": "Production script recovery",
        "wrong_niche": "niche",
        "missing_marker": "quality approval without enhancement",
        "invalid_json": "Invalid checkpoint",
        "invalid_metadata": "Invalid checkpoint",
        "missing_fingerprint": "fingerprint is missing",
        "changed_source": "Source content differs",
    }[corruption]
    assert expected_error in result.errors[0]
    harness.enhancer.enhance_script.assert_not_called()
    harness.quality.evaluate_script.assert_not_called()
    harness.images.generate_for_script.assert_not_called()
    harness.audio.generate_for_script.assert_not_called()
    harness.video.assemble_video.assert_not_called()
    assert harness.source_path.read_bytes() == source_bytes


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


def test_enhancement_rejects_unenhanced_asset_markers(
    resume_harness: ResumeHarness,
) -> None:
    harness = resume_harness
    assert harness.run(enhance=False).success
    source_bytes = harness.source_path.read_bytes()
    requests = list(harness.asset_requests)
    for service in (
        harness.enhancer,
        harness.quality,
        harness.images,
        harness.audio,
        harness.video,
    ):
        service.reset_mock()

    result = harness.run()

    assert not result.success
    assert "quality approval without enhancement" in result.errors[0]
    assert harness.asset_requests == requests
    assert harness.source_path.read_bytes() == source_bytes
    harness.enhancer.enhance_script.assert_not_called()
    harness.quality.evaluate_script.assert_not_called()
    harness.images.generate_for_script.assert_not_called()
    harness.audio.generate_for_script.assert_not_called()
    harness.video.assemble_video.assert_not_called()


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
        harness.orchestrator._save_checkpoint(checkpoint, harness.source)

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


@pytest.mark.parametrize("has_snapshot_metadata", [False, True])
def test_ignores_checkpoint_saved_under_enhanced_title(
    resume_harness: ResumeHarness, has_snapshot_metadata: bool
) -> None:
    harness = resume_harness
    assert harness.run().success
    original_checkpoint = Checkpoint.load(harness.checkpoint_path)
    data = json.loads(harness.checkpoint_path.read_text(encoding="utf-8"))
    if not has_snapshot_metadata:
        data.pop("enhanced_script")
    legacy_path = harness.checkpoint_path.with_name("a-better-title.checkpoint.json")
    legacy_bytes = json.dumps(data).encode("utf-8")
    legacy_path.write_bytes(legacy_bytes)
    harness.checkpoint_path.unlink()
    harness.enhancer.reset_mock()
    harness.images.reset_mock()
    harness.quality.reset_mock()
    prior_requests = list(harness.asset_requests)

    result = harness.run()

    assert result.success, result.errors
    assert harness.enhancer.enhance_script.call_count == 1
    harness.quality.evaluate_script.assert_called_once()
    assert harness.asset_requests[len(prior_requests) :] == prior_requests
    assert legacy_path.read_bytes() == legacy_bytes
    assert harness.checkpoint_path.is_file()
    checkpoint = Checkpoint.load(harness.checkpoint_path)
    assert checkpoint.job_id != original_checkpoint.job_id
    assert checkpoint.script_path == harness.source_path.with_name(
        "original-title_production.json"
    )
    assert result.script_path == checkpoint.script_path
    assert Script.from_json_file(checkpoint.script_path).title == harness.enhanced.title


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

    def thumbnail_variants(
        title: str,
        niche: str,
        base_name: str,
        output_dir: Path,
        client: AzureOpenAIClient,
    ) -> list[Path]:
        assert title == harness.enhanced.title
        assert niche == harness.enhanced.niche.value
        assert base_name == harness.enhanced.safe_title
        assert client is harness.orchestrator._client
        output_dir.mkdir(parents=True, exist_ok=True)
        paths = [output_dir / f"variant_{number}.png" for number in (1, 2, 3)]
        for path in paths:
            path.write_bytes(b"thumbnail")
        return paths

    with patch(
        "faceless.pipeline.orchestrator.generate_thumbnail_variants",
        side_effect=thumbnail_variants,
    ) as thumbnail_service:
        result = harness.orchestrator.run(
            niche=harness.source.niche,
            platforms=[Platform.YOUTUBE],
            script_path=harness.source_path,
            enhance=True,
            thumbnails=True,
            subtitles=True,
        )[0]

    assert result.success, result.errors
    thumbnail_service.assert_called_once()
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

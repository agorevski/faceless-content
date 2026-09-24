"""Offline production smoke test with real FFmpeg and mocked paid services."""

import shutil
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from faceless.core.enums import Niche, Platform
from faceless.core.models import Checkpoint, Scene, Script
from faceless.pipeline.orchestrator import Orchestrator
from faceless.services.quality_service import HookAnalysis, QualityScore


def _ffmpeg(*args: str) -> None:
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=90,
    )


def _resolution(path: Path) -> str:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=p=0:s=x",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout.strip()


def _bright_pixels(path: Path, crop: str) -> int:
    frame = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            "0.35",
            "-i",
            str(path),
            "-frames:v",
            "1",
            "-vf",
            f"crop={crop},format=gray",
            "-f",
            "rawvideo",
            "pipe:1",
        ],
        check=True,
        capture_output=True,
        timeout=60,
    ).stdout
    assert frame
    return sum(pixel > 210 for pixel in frame)


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="FFmpeg and FFprobe are needed to inspect rendered media",
)
def test_production_renders_approved_hook_captions_and_thumbnails(
    tmp_path: Path,
) -> None:
    """Produce both platform outputs without making any paid API requests."""
    source_image = tmp_path / "source.png"
    source_audio = tmp_path / "source.mp3"
    _ffmpeg(
        "-f",
        "lavfi",
        "-i",
        "color=c=black:s=64x64",
        "-frames:v",
        "1",
        "-update",
        "1",
        str(source_image),
    )
    _ffmpeg(
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=44100:cl=mono",
        "-t",
        "0.8",
        "-c:a",
        "libmp3lame",
        str(source_audio),
    )

    output = tmp_path / "output" / "scary-stories"
    settings = MagicMock()
    settings.enable_checkpointing = True
    settings.max_concurrent_videos = 1
    settings.ffmpeg_path = "ffmpeg"
    settings.ffprobe_path = "ffprobe"
    for name, directory in (
        ("get_scripts_dir", "scripts"),
        ("get_images_dir", "images"),
        ("get_audio_dir", "audio"),
        ("get_videos_dir", "videos"),
        ("get_final_output_dir", "final"),
        ("get_checkpoints_dir", ".checkpoints"),
    ):
        getattr(settings, name).return_value = output / directory

    script = Script(
        title="The Closed Door",
        niche=Niche.SCARY_STORIES,
        scenes=[
            Scene(
                scene_number=1,
                narration="An old door stood in the hallway.",
                image_prompt="An old door in a hallway",
            )
        ],
    )
    enhanced = script.model_copy(deep=True)
    enhanced.scenes[
        0
    ].narration = "What's behind the door? The old hallway offers a clue."

    def generate_images(
        script: Script, platform: Platform, checkpoint: Checkpoint
    ) -> list[Path]:
        image = output / "images" / script.safe_title / f"scene_01_{platform.value}.png"
        image.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_image, image)
        script.scenes[0].image_path = image
        return [image]

    def generate_audio(script: Script, checkpoint: Checkpoint) -> list[Path]:
        audio = output / "audio" / script.safe_title / "scene_01.mp3"
        audio.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_audio, audio)
        script.scenes[0].audio_path = audio
        return [audio]

    def set_duration(script: Script) -> None:
        script.scenes[0].duration_estimate = 0.8

    def generate_thumbnail_image(
        prompt: str,
        niche: str,
        output_name: str,
        output_dir: Path,
        client: object | None = None,
    ) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        image = output_dir / f"{output_name}.png"
        shutil.copyfile(source_image, image)
        return image

    with (
        patch("faceless.pipeline.orchestrator.get_settings", return_value=settings),
        patch("faceless.services.video_service.get_settings", return_value=settings),
        patch("faceless.pipeline.orchestrator.AzureOpenAIClient"),
        patch("faceless.pipeline.orchestrator.EnhancerService") as enhancer,
        patch("faceless.pipeline.orchestrator.QualityService") as quality,
        patch("faceless.pipeline.orchestrator.ImageService") as images,
        patch("faceless.pipeline.orchestrator.TTSService") as tts,
        patch(
            "faceless.services.thumbnail_service.generate_thumbnail",
            side_effect=generate_thumbnail_image,
        ),
    ):
        enhancer.return_value.enhance_script.return_value = enhanced
        quality.return_value.evaluate_script.return_value = QualityScore(
            script_title=enhanced.title,
            niche=enhanced.niche,
            overall_score=8.0,
            hook_score=8.0,
            narrative_score=8.0,
            engagement_score=8.0,
            information_score=8.0,
            hook_analysis=HookAnalysis(
                score=8.0,
                hook_type="mystery",
                attention_grab=0.8,
                curiosity_gap=0.8,
            ),
            approved_for_production=True,
        )
        images.return_value.generate_for_script.side_effect = generate_images
        tts.return_value.generate_for_script.side_effect = generate_audio
        tts.return_value.update_scene_durations.side_effect = set_duration
        result = Orchestrator().run_single(script)

    assert result.success, result.errors
    assert result.script_path is not None
    assert (
        Script.from_json_file(result.script_path)
        .scenes[0]
        .narration.startswith("What's behind the door?")
    )
    assert _resolution(result.video_paths["youtube"]) == "1920x1080"
    assert _resolution(result.video_paths["tiktok"]) == "1080x1920"
    assert _bright_pixels(result.video_paths["youtube"], "1450:380:200:100") > 100
    assert _bright_pixels(result.video_paths["tiktok"], "720:440:100:250") > 100
    assert _bright_pixels(result.video_paths["tiktok"], "750:600:90:950") > 100
    assert result.video_paths["tiktok"].stem.endswith("_captioned")
    assert set(result.subtitle_paths) == {"srt", "vtt"}
    assert "What's behind the door?" in result.subtitle_paths["srt"].read_text()
    assert len(result.thumbnail_paths) == 3
    assert all(_resolution(path) == "1280x720" for path in result.thumbnail_paths)

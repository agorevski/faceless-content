"""
Unit tests for VideoService.

Tests cover:
- FFmpeg command execution
- Scene video creation
- Video concatenation
- Background music mixing
- Video assembly
"""

import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from faceless.core.enums import JobStatus, Niche, Platform
from faceless.core.exceptions import ExternalToolError, FFmpegError, VideoAssemblyError
from faceless.core.models import Checkpoint, Scene, Script
from faceless.services.video_service import VideoService


class TestVideoService:
    """Tests for VideoService."""

    @pytest.fixture
    def mock_settings(self, tmp_path: Path) -> Iterator[MagicMock]:
        """Mock settings."""
        with patch("faceless.services.video_service.get_settings") as mock:
            settings = MagicMock()
            settings.ffmpeg_path = "ffmpeg"
            settings.ffprobe_path = "ffprobe"
            settings.get_images_dir.return_value = tmp_path / "images"
            settings.get_videos_dir.return_value = tmp_path / "videos"
            settings.get_final_output_dir.return_value = tmp_path / "final"
            settings.max_concurrent_videos = 2
            mock.return_value = settings
            yield settings

    @pytest.fixture
    def video_service(self, mock_settings):
        """Create video service instance."""
        from faceless.services.video_service import VideoService

        return VideoService()

    @pytest.fixture
    def sample_scene(self, tmp_path: Path) -> Scene:
        """Create sample scene with paths."""
        scene = Scene(
            scene_number=1,
            narration="Test narration",
            image_prompt="Test prompt",
            duration_estimate=10.0,
        )
        # Create dummy files
        image_path = tmp_path / "scene_01.png"
        image_path.write_bytes(b"fake_image")
        audio_path = tmp_path / "scene_01.mp3"
        audio_path.write_bytes(b"fake_audio")

        scene.image_path = image_path
        scene.audio_path = audio_path
        return scene

    def test_init(self, mock_settings) -> None:
        """Test service initialization."""
        from faceless.services.video_service import VideoService

        with patch("faceless.services.video_service.shutil.which", return_value=None):
            service = VideoService()
            assert service._ffmpeg == "ffmpeg"
            assert service._ffprobe == "ffprobe"

    def test_run_ffmpeg_success(self, video_service, mock_settings) -> None:
        """Test successful FFmpeg execution."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            result = video_service._run_ffmpeg(["-version"], "Test version")

            mock_run.assert_called_once()
            assert result.returncode == 0

    def test_run_ffmpeg_does_not_use_shell_for_filter_text(self, mock_settings) -> None:
        """An unresolved executable still receives an argv list, never a shell."""
        from faceless.services.video_service import VideoService

        with patch("faceless.services.video_service.shutil.which", return_value=None):
            service = VideoService()
        graph = "drawtext=text=hello\\; touch unexpected:expansion=none"
        with patch("subprocess.run", return_value=MagicMock(returncode=0)) as run:
            service._run_ffmpeg(["-filter_complex", graph])
        assert run.call_args.args[0] == ["ffmpeg", "-filter_complex", graph]
        assert run.call_args.kwargs["shell"] is False

    def test_run_ffmpeg_failure(self, video_service) -> None:
        """Test FFmpeg execution failure."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr="Error message"
            )

            with pytest.raises(FFmpegError) as exc_info:
                video_service._run_ffmpeg(["-invalid"], "Test failure")

            assert exc_info.value.details["return_code"] == 1

    @pytest.mark.parametrize("executable", ["ffmpeg", r"C:\Program Files\ffmpeg.exe"])
    def test_run_ffmpeg_preserves_arguments_without_shell(
        self, video_service: VideoService, executable: str
    ) -> None:
        """Shell metacharacters in filters and paths must remain literal arguments."""
        video_service._ffmpeg = executable
        args = [
            "-filter_complex",
            "[0:a]volume=0.15[music];[music]anull[aout]",
            "Alice's story & %PATH%.mp4",
        ]
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            video_service._run_ffmpeg(args)

        assert mock_run.call_args.args[0] == [executable, *args]
        assert mock_run.call_args.kwargs["shell"] is False

    def test_run_ffmpeg_timeout(self, video_service) -> None:
        """Test FFmpeg timeout."""
        import subprocess

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="ffmpeg", timeout=600)

            with pytest.raises(FFmpegError) as exc_info:
                video_service._run_ffmpeg(["-i", "input.mp4"], "Test timeout")

            assert "timed out" in str(exc_info.value).lower()

    def test_run_ffmpeg_not_found(self, video_service) -> None:
        """Test FFmpeg not found."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()

            with pytest.raises(FFmpegError) as exc_info:
                video_service._run_ffmpeg(["-version"], "Test not found")

            assert "not found" in str(exc_info.value).lower()

    def test_create_scene_video_success(
        self, video_service, sample_scene, tmp_path: Path
    ) -> None:
        """Test successful scene video creation."""
        output_path = tmp_path / "scene_video.mp4"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = video_service.create_scene_video(
                scene=sample_scene,
                platform=Platform.YOUTUBE,
                output_path=output_path,
            )

            assert result == output_path
            assert sample_scene.video_path == output_path

    def test_create_scene_video_with_ken_burns_disabled(
        self, video_service, sample_scene, tmp_path: Path
    ) -> None:
        """Test scene video without Ken Burns effect."""
        output_path = tmp_path / "scene_video.mp4"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            video_service.create_scene_video(
                scene=sample_scene,
                platform=Platform.TIKTOK,
                output_path=output_path,
                enable_ken_burns=False,
            )

            # Check that mock was called (loop filter used instead of zoompan)
            assert mock_run.called

    def test_create_scene_video_missing_image(
        self, video_service, tmp_path: Path
    ) -> None:
        """Test scene video creation with missing image."""
        scene = Scene(
            scene_number=1,
            narration="Test",
            image_prompt="Test",
            duration_estimate=10.0,
        )
        scene.image_path = tmp_path / "nonexistent.png"
        scene.audio_path = tmp_path / "audio.mp3"
        (tmp_path / "audio.mp3").write_bytes(b"audio")

        with pytest.raises(VideoAssemblyError) as exc_info:
            video_service.create_scene_video(
                scene=scene,
                platform=Platform.YOUTUBE,
                output_path=tmp_path / "out.mp4",
            )

        assert "image not found" in str(exc_info.value).lower()

    def test_create_scene_video_missing_audio(
        self, video_service, tmp_path: Path
    ) -> None:
        """Test scene video creation with missing audio."""
        scene = Scene(
            scene_number=1,
            narration="Test",
            image_prompt="Test",
            duration_estimate=10.0,
        )
        image_path = tmp_path / "image.png"
        image_path.write_bytes(b"image")
        scene.image_path = image_path
        scene.audio_path = tmp_path / "nonexistent.mp3"

        with pytest.raises(VideoAssemblyError) as exc_info:
            video_service.create_scene_video(
                scene=scene,
                platform=Platform.YOUTUBE,
                output_path=tmp_path / "out.mp4",
            )

        assert "audio not found" in str(exc_info.value).lower()

    def test_concatenate_scenes_success(self, video_service, tmp_path: Path) -> None:
        """Test successful scene concatenation."""
        # Create dummy video files
        video1 = tmp_path / "scene1.mp4"
        video2 = tmp_path / "scene2.mp4"
        video1.write_bytes(b"video1")
        video2.write_bytes(b"video2")

        output_path = tmp_path / "concat.mp4"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = video_service.concatenate_scenes([video1, video2], output_path)

            assert result == output_path
            mock_run.assert_called_once()

    def test_concatenate_scenes_empty_list(self, video_service, tmp_path: Path) -> None:
        """Test concatenation with empty list."""
        with pytest.raises(VideoAssemblyError) as exc_info:
            video_service.concatenate_scenes([], tmp_path / "out.mp4")

        assert "no scene videos" in str(exc_info.value).lower()

    def test_concatenate_scenes_cleans_up_concat_file(
        self, video_service, tmp_path: Path
    ) -> None:
        """Test that concat file is cleaned up after concatenation."""
        video1 = tmp_path / "scene1.mp4"
        video1.write_bytes(b"video1")

        output_path = tmp_path / "output" / "concat.mp4"
        output_path.parent.mkdir(parents=True)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            video_service.concatenate_scenes([video1], output_path)

            assert not list(output_path.parent.glob(".concat_*.txt"))

    def test_concatenate_scenes_escapes_paths(
        self, video_service: VideoService, tmp_path: Path
    ) -> None:
        """Apostrophes and Windows separators must survive ffconcat parsing."""
        video = tmp_path / "Alice's scene.mp4"
        video.write_bytes(b"video")
        output_path = tmp_path / "nested" / "output.mp4"

        def check_manifest(args: list[str], description: str) -> MagicMock:
            manifest = Path(args[args.index("-i") + 1])
            escaped = video.absolute().as_posix().replace("'", "'\\''")
            assert manifest.read_text(encoding="utf-8") == f"file '{escaped}'\n"
            return MagicMock(returncode=0)

        with patch.object(video_service, "_run_ffmpeg", side_effect=check_manifest):
            assert video_service.concatenate_scenes([video], output_path) == output_path

        assert not list(output_path.parent.glob(".concat_*.txt"))

    def test_concatenate_scenes_isolates_overlapping_manifests(
        self, video_service: VideoService, tmp_path: Path
    ) -> None:
        """Overlapping jobs in the same directory must not overwrite manifests."""
        first = tmp_path / "first.mp4"
        second = tmp_path / "second.mp4"
        manifests: list[Path] = []

        def overlap(args: list[str], description: str) -> MagicMock:
            manifest = Path(args[args.index("-i") + 1])
            manifests.append(manifest)
            original = manifest.read_text(encoding="utf-8")
            if len(manifests) == 1:
                video_service.concatenate_scenes([second], tmp_path / "second_out.mp4")
                assert manifest.read_text(encoding="utf-8") == original
            return MagicMock(returncode=0)

        with patch.object(video_service, "_run_ffmpeg", side_effect=overlap):
            video_service.concatenate_scenes([first], tmp_path / "first_out.mp4")

        assert len(set(manifests)) == 2
        assert all(not manifest.exists() for manifest in manifests)

    def test_concatenate_scenes_cleans_manifest_after_failure(
        self, video_service: VideoService, tmp_path: Path
    ) -> None:
        """Failed FFmpeg runs must not leave stale concat manifests."""
        with (
            patch.object(
                video_service, "_run_ffmpeg", side_effect=FFmpegError("Concat failed")
            ),
            pytest.raises(FFmpegError),
        ):
            video_service.concatenate_scenes(
                [tmp_path / "scene.mp4"], tmp_path / "output.mp4"
            )

        assert not list(tmp_path.glob(".concat_*.txt"))

    def test_add_background_music_success(self, video_service, tmp_path: Path) -> None:
        """Test adding background music."""
        video_path = tmp_path / "video.mp4"
        music_path = tmp_path / "music.mp3"
        output_path = tmp_path / "output.mp4"

        video_path.write_bytes(b"video")
        music_path.write_bytes(b"music")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = video_service.add_background_music(
                video_path=video_path,
                music_path=music_path,
                output_path=output_path,
                music_volume=0.2,
            )

            assert result == output_path

    def test_add_background_music_preserves_narration_volume(
        self, video_service: VideoService, tmp_path: Path
    ) -> None:
        """amix must not normalize narration to half its original volume."""
        video = tmp_path / "video.mp4"
        music = tmp_path / "music.mp3"
        video.write_bytes(b"video")
        music.write_bytes(b"music")

        with patch.object(video_service, "_run_ffmpeg") as mock_run:
            video_service.add_background_music(video, music, tmp_path / "output.mp4")

        args = mock_run.call_args.args[0]
        audio_filter = args[args.index("-filter_complex") + 1]
        assert "[1:a]volume=0.15[music]" in audio_filter
        assert "duration=first" in audio_filter
        assert "normalize=0" in audio_filter

    def test_add_background_music_missing_video(
        self, video_service, tmp_path: Path
    ) -> None:
        """Test adding music with missing video."""
        music_path = tmp_path / "music.mp3"
        music_path.write_bytes(b"music")

        with pytest.raises(VideoAssemblyError) as exc_info:
            video_service.add_background_music(
                video_path=tmp_path / "nonexistent.mp4",
                music_path=music_path,
                output_path=tmp_path / "out.mp4",
            )

        assert "video not found" in str(exc_info.value).lower()

    def test_add_background_music_missing_music(
        self, video_service, tmp_path: Path
    ) -> None:
        """Test adding music with missing music file."""
        video_path = tmp_path / "video.mp4"
        video_path.write_bytes(b"video")

        with pytest.raises(VideoAssemblyError) as exc_info:
            video_service.add_background_music(
                video_path=video_path,
                music_path=tmp_path / "nonexistent.mp3",
                output_path=tmp_path / "out.mp4",
            )

        assert "music file not found" in str(exc_info.value).lower()

    def test_assemble_video(
        self, video_service, mock_settings, sample_scene, tmp_path: Path
    ) -> None:
        """Test full video assembly."""
        scenes = [sample_scene]
        script = Script(
            title="Test Script",
            niche=Niche.SCARY_STORIES,
            scenes=scenes,
        )

        mock_settings.get_videos_dir.return_value = tmp_path / "videos"
        mock_settings.get_final_output_dir.return_value = tmp_path / "final"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            with patch("shutil.copy2"):
                result = video_service.assemble_video(
                    script=script,
                    platform=Platform.YOUTUBE,
                )

                assert result is not None

    def test_assemble_for_all_platforms_selects_matching_images(
        self,
        video_service,
        mock_settings,
        sample_scene: Scene,
        tmp_path: Path,
    ) -> None:
        """The last generated image must not be reused for the other platform."""
        script = Script(
            title="Platform assets", niche=Niche.SCARY_STORIES, scenes=[sample_scene]
        )
        images_dir = tmp_path / "images" / script.safe_title
        images_dir.mkdir(parents=True)
        youtube_image = images_dir / "scene_01_youtube.png"
        tiktok_image = images_dir / "scene_01_tiktok.png"
        youtube_image.write_bytes(b"landscape")
        tiktok_image.write_bytes(b"portrait")
        sample_scene.image_path = tiktok_image

        with (
            patch("subprocess.run", return_value=MagicMock(returncode=0)) as run,
            patch("shutil.copy2"),
        ):
            outputs = video_service.assemble_for_all_platforms(
                script, [Platform.YOUTUBE, Platform.TIKTOK]
            )

        commands = [
            args
            for call in run.call_args_list
            if isinstance(args := call.args[0], list)
            and "-filter_complex" in args
            and "scene_01_" in args[-1]
        ]
        assert list(outputs) == [Platform.YOUTUBE, Platform.TIKTOK]
        assert [Path(args[args.index("-i") + 1]) for args in commands] == [
            youtube_image,
            tiktok_image,
        ]
        assert sample_scene.image_path == tiktok_image

    @pytest.mark.parametrize("platform", [Platform.YOUTUBE, Platform.TIKTOK])
    @pytest.mark.parametrize("image_path_is_missing", [False, True])
    def test_assemble_video_resume_resolves_image_for_pending_scene(
        self,
        video_service,
        mock_settings,
        sample_scene: Scene,
        tmp_path: Path,
        platform: Platform,
        image_path_is_missing: bool,
    ) -> None:
        """A completed scene needs no image; a pending one uses its own platform."""
        from uuid import uuid4

        sample_scene.image_path = None
        second = Scene(
            scene_number=2,
            narration="Next scene",
            image_prompt="Next image",
            audio_path=sample_scene.audio_path,
        )
        script = Script(
            title="Resume assets",
            niche=Niche.SCARY_STORIES,
            scenes=[sample_scene, second],
        )
        images_dir = tmp_path / "images" / script.safe_title
        images_dir.mkdir(parents=True)
        expected = images_dir / f"scene_02_{platform.value}.png"
        other = images_dir / (
            f"scene_02_{Platform.TIKTOK.value if platform == Platform.YOUTUBE else Platform.YOUTUBE.value}.png"
        )
        expected.write_bytes(b"requested")
        other.write_bytes(b"other platform")
        second.image_path = None if image_path_is_missing else other
        checkpoint = Checkpoint(
            job_id=uuid4(),
            script_path=tmp_path / "script.json",
            status=JobStatus.ASSEMBLING_VIDEO,
        )
        checkpoint.mark_video_done(platform.value, 1)
        video_dir = tmp_path / "videos" / script.safe_title
        video_dir.mkdir(parents=True)
        (video_dir / f"scene_01_{platform.value}.mp4").write_bytes(b"already rendered")

        with (
            patch("subprocess.run", return_value=MagicMock(returncode=0)) as run,
            patch("shutil.copy2"),
        ):
            video_service.assemble_video(script, platform, checkpoint=checkpoint)

        commands = [
            args
            for call in run.call_args_list
            if isinstance(args := call.args[0], list) and "-filter_complex" in args
        ]
        assert len(commands) == 1
        assert Path(commands[0][commands[0].index("-i") + 1]) == expected
        assert checkpoint.is_video_done(platform.value, 2)

    @pytest.mark.parametrize("platform", [Platform.YOUTUBE, Platform.TIKTOK])
    def test_assemble_video_uses_matching_sibling_from_moved_image_dir(
        self,
        video_service,
        sample_scene: Scene,
        tmp_path: Path,
        platform: Platform,
    ) -> None:
        """Resume still works when the images directory has moved since generation."""
        script = Script(
            title="Moved assets", niche=Niche.SCARY_STORIES, scenes=[sample_scene]
        )
        archive = tmp_path / "archived-images"
        archive.mkdir()
        expected = archive / f"scene_01_{platform.value}.png"
        other_platform = (
            Platform.TIKTOK if platform == Platform.YOUTUBE else Platform.YOUTUBE
        )
        other = archive / f"scene_01_{other_platform.value}.png"
        expected.write_bytes(b"requested")
        other.write_bytes(b"other platform")
        sample_scene.image_path = other

        with (
            patch("subprocess.run", return_value=MagicMock(returncode=0)) as run,
            patch("shutil.copy2"),
        ):
            video_service.assemble_video(script, platform)

        command = next(
            args
            for call in run.call_args_list
            if isinstance(args := call.args[0], list) and "-filter_complex" in args
        )
        assert Path(command[command.index("-i") + 1]) == expected

    @pytest.mark.parametrize("platform", [Platform.YOUTUBE, Platform.TIKTOK])
    def test_assemble_video_rejects_other_platform_image(
        self,
        video_service,
        sample_scene: Scene,
        tmp_path: Path,
        platform: Platform,
    ) -> None:
        """Never stretch a different platform's asset if the requested one is missing."""
        other_platform = (
            Platform.TIKTOK if platform == Platform.YOUTUBE else Platform.YOUTUBE
        )
        other = tmp_path / f"scene_01_{other_platform.value}.png"
        other.write_bytes(b"wrong orientation")
        sample_scene.image_path = other
        script = Script(
            title="Missing image", niche=Niche.SCARY_STORIES, scenes=[sample_scene]
        )

        with (
            patch("subprocess.run") as run,
            pytest.raises(
                VideoAssemblyError,
                match=f"Image not found for scene 1 on {platform.value}",
            ),
        ):
            video_service.assemble_video(script, platform)
        run.assert_not_called()

    @pytest.mark.parametrize("platform", [Platform.YOUTUBE, Platform.TIKTOK])
    def test_assemble_video_burns_hook_into_first_scene_only(
        self,
        video_service,
        mock_settings,
        sample_scene,
        tmp_path: Path,
        platform: Platform,
    ) -> None:
        """Parallel assembly renders source narration only in the opening scene."""
        sample_scene.narration = "What's behind the locked door at 9:30?"
        second = Scene(
            scene_number=2,
            narration="The story continues after the opening.",
            image_prompt="Another image",
            duration_estimate=8.0,
            image_path=sample_scene.image_path,
            audio_path=sample_scene.audio_path,
        )
        script = Script(
            title="Two scenes",
            niche=Niche.SCARY_STORIES,
            scenes=[sample_scene, second],
        )
        mock_settings.get_videos_dir.return_value = tmp_path / "videos"
        mock_settings.get_final_output_dir.return_value = tmp_path / "final"

        with (
            patch("subprocess.run", return_value=MagicMock(returncode=0)) as run,
            patch("shutil.copy2"),
        ):
            video_service.assemble_video(script, platform)

        filters = {
            Path(args[-1]).name: args[args.index("-filter_complex") + 1]
            for call in run.call_args_list
            if isinstance(args := call.args[0], list) and "-filter_complex" in args
        }
        first = filters[f"scene_01_{platform.value}.mp4"]
        second_filter = filters[f"scene_02_{platform.value}.mp4"]
        width, height = platform.resolution
        left = round(width * (0.15 if platform == Platform.TIKTOK else 0.10))
        right = round(width * (0.20 if platform == Platform.TIKTOK else 0.10))

        assert f"scale={width}:{height}" in first
        assert f"x=({width - left - right}-text_w)/2+{left}" in first
        assert "zoompan=" in first
        assert first.count("drawtext=") >= 1
        assert "enable='between(t,0.0,3.0)'" in first
        assert "box=1" in first
        assert "drawtext=" not in second_filter

    def test_assemble_video_surfaces_overlay_failure(
        self,
        video_service,
        mock_settings,
        sample_scene,
        tmp_path: Path,
    ) -> None:
        """A drawtext failure must fail assembly rather than silently omit the hook."""
        script = Script(
            title="Hook failure", niche=Niche.SCARY_STORIES, scenes=[sample_scene]
        )
        mock_settings.get_videos_dir.return_value = tmp_path / "videos"
        mock_settings.get_final_output_dir.return_value = tmp_path / "final"

        def fail_drawtext(*args: object, **kwargs: object) -> MagicMock:
            command = args[0]
            assert isinstance(command, list)
            assert "-filter_complex" in command
            return MagicMock(
                returncode=1, stdout="", stderr="drawtext font unavailable"
            )

        with (
            patch("subprocess.run", side_effect=fail_drawtext),
            pytest.raises(VideoAssemblyError, match="drawtext font unavailable"),
        ):
            video_service.assemble_video(script, Platform.YOUTUBE)

    @pytest.mark.skipif(
        not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
        reason="FFmpeg or FFprobe unavailable",
    )
    @pytest.mark.parametrize("platform", [Platform.YOUTUBE, Platform.TIKTOK])
    def test_assemble_video_renders_visible_opening(
        self,
        video_service,
        mock_settings,
        tmp_path: Path,
        platform: Platform,
    ) -> None:
        """Render a real black scene and verify visible text in the safe top area."""
        width, height = platform.resolution
        image = tmp_path / "black.ppm"
        image.write_bytes(b"P6\n64 64\n255\n" + b"\x00\x00\x00" * (64 * 64))
        audio = tmp_path / "quiet.mp3"
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "anullsrc=r=44100:cl=mono",
                "-t",
                "0.4",
                "-q:a",
                "9",
                str(audio),
            ],
            capture_output=True,
            check=True,
            timeout=30,
        )
        scene = Scene(
            scene_number=1,
            narration="What's at 9:30? 100% true.",
            image_prompt="Black background",
            duration_estimate=0.4,
            image_path=image,
            audio_path=audio,
        )
        script = Script(title="Visible hook", niche=Niche.SCARY_STORIES, scenes=[scene])
        mock_settings.get_videos_dir.return_value = tmp_path / "videos"
        mock_settings.get_final_output_dir.return_value = tmp_path / "final"

        output = video_service.assemble_video(script, platform)
        assert output.exists()
        probe = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height",
                "-of",
                "csv=p=0",
                str(output),
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        assert probe.stdout.strip() == f"{width},{height}"
        frame = subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(output),
                "-frames:v",
                "1",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "gray",
                "-",
            ],
            capture_output=True,
            check=True,
            timeout=30,
        ).stdout
        assert len(frame) == width * height
        left = round(width * (0.15 if platform == Platform.TIKTOK else 0.10))
        right = round(width * (0.20 if platform == Platform.TIKTOK else 0.10))
        assert any(
            max(frame[y * width + left : y * width + width - right]) > 80
            for y in range(height // 10, height // 2)
        )
        assert (
            max(frame[height * 4 // 5 * width : height * 4 // 5 * width + width]) < 30
        )

    def test_assemble_video_with_checkpoint_skip(
        self, video_service, mock_settings, sample_scene, tmp_path: Path
    ) -> None:
        """Test video assembly with checkpoint skipping."""
        from uuid import uuid4

        scenes = [sample_scene]
        script = Script(
            title="Test Script",
            niche=Niche.SCARY_STORIES,
            scenes=scenes,
        )

        checkpoint = Checkpoint(
            job_id=uuid4(),
            script_path=Path("/test/script.json"),
            status=JobStatus.ASSEMBLING_VIDEO,
        )
        checkpoint.mark_video_done("youtube", 1)

        mock_settings.get_videos_dir.return_value = tmp_path / "videos"
        mock_settings.get_final_output_dir.return_value = tmp_path / "final"

        # Create existing scene video
        videos_dir = tmp_path / "videos" / script.safe_title
        videos_dir.mkdir(parents=True)
        existing_video = videos_dir / "scene_01_youtube.mp4"
        existing_video.write_bytes(b"existing")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            with patch("shutil.copy2"):
                video_service.assemble_video(
                    script=script,
                    platform=Platform.YOUTUBE,
                    checkpoint=checkpoint,
                )

    def test_assemble_for_all_platforms(
        self, video_service, mock_settings, sample_scene, tmp_path: Path
    ) -> None:
        """Test video assembly for all platforms."""
        scenes = [sample_scene]
        script = Script(
            title="Test Script",
            niche=Niche.FINANCE,
            scenes=scenes,
        )

        mock_settings.get_videos_dir.return_value = tmp_path / "videos"
        mock_settings.get_final_output_dir.return_value = tmp_path / "final"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            with patch("shutil.copy2"):
                results = video_service.assemble_for_all_platforms(
                    script=script,
                    platforms=[Platform.YOUTUBE, Platform.TIKTOK],
                )

                assert len(results) == 2

    def test_get_video_duration_success(self, video_service, tmp_path: Path) -> None:
        """Test getting video duration."""
        video_path = tmp_path / "video.mp4"
        video_path.write_bytes(b"video")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="60.5\n", stderr="")

            result = video_service.get_video_duration(video_path)

            assert result == 60.5

    def test_get_video_duration_unresolved_executable_uses_argv(
        self, mock_settings
    ) -> None:
        """Probing a path never interpolates it into a shell command."""
        from faceless.services.video_service import VideoService

        unsafe_path = Path('video"; unexpected-command ".mp4')
        with (
            patch("faceless.services.video_service.shutil.which", return_value=None),
            patch(
                "subprocess.run",
                return_value=MagicMock(returncode=0, stdout="1.0\n", stderr=""),
            ) as run,
        ):
            service = VideoService()
            assert service.get_video_duration(unsafe_path) == 1.0
        assert run.call_args.args[0][0] == "ffprobe"
        assert run.call_args.args[0][-1] == str(unsafe_path)
        assert run.call_args.kwargs["shell"] is False

    def test_get_video_duration_failure(self, video_service, tmp_path: Path) -> None:
        """Test getting video duration with error."""
        video_path = tmp_path / "video.mp4"

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = OSError("ffprobe not found")

            with pytest.raises(ExternalToolError, match="Could not run FFprobe"):
                video_service.get_video_duration(video_path)

    def test_get_video_duration_preserves_path_without_shell(
        self, video_service: VideoService, tmp_path: Path
    ) -> None:
        """Unresolved ffprobe must receive filenames without shell expansion."""
        video_service._ffprobe = "ffprobe"
        video = tmp_path / "Alice's story & %PATH%.mp4"
        with (
            patch("faceless.utils.media.shutil.which", return_value=None),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="12.5")

            assert video_service.get_video_duration(video) == 12.5

        assert mock_run.call_args.args[0][0] == "ffprobe"
        assert mock_run.call_args.args[0][-1] == str(video)
        assert mock_run.call_args.kwargs["shell"] is False

    def test_get_video_duration_nonzero_returncode(
        self, video_service, tmp_path: Path
    ) -> None:
        """Test getting video duration when ffprobe returns non-zero exit code."""
        video_path = tmp_path / "video.mp4"
        video_path.write_bytes(b"video")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="123.5", stderr="File not found"
            )

            with pytest.raises(ExternalToolError, match="probe failed") as exc_info:
                video_service.get_video_duration(video_path)
            assert exc_info.value.details["return_code"] == 1
            assert exc_info.value.details["stdout"] == "123.5"

    def test_get_video_duration_timeout(self, video_service, tmp_path: Path) -> None:
        """Test getting video duration with timeout."""
        import subprocess

        video_path = tmp_path / "video.mp4"
        video_path.write_bytes(b"video")

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="ffprobe", timeout=30)

            with pytest.raises(ExternalToolError, match="timed out"):
                video_service.get_video_duration(video_path)

    def test_get_video_duration_invalid_output(
        self, video_service, tmp_path: Path
    ) -> None:
        """Test getting video duration with invalid output."""
        video_path = tmp_path / "video.mp4"
        video_path.write_bytes(b"video")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="not_a_number\n", stderr=""
            )

            with pytest.raises(ExternalToolError, match="invalid duration"):
                video_service.get_video_duration(video_path)

    def test_get_video_duration_configured_executable(
        self, mock_settings: MagicMock, tmp_path: Path
    ) -> None:
        executable = str(tmp_path / "tools & %PATH%" / "probe.exe")
        mock_settings.ffprobe_path = executable
        service = VideoService()
        video = tmp_path / "Alice's & %PATH%.mp4"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="2.5", stderr="")
            assert service.get_video_duration(video) == 2.5
        assert mock_run.call_args.args[0][0] == executable
        assert mock_run.call_args.args[0][-1] == str(video)
        assert mock_run.call_args.kwargs["shell"] is False

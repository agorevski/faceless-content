"""
Unit tests for VideoService.

Tests cover:
- FFmpeg command execution
- Scene video creation
- Video concatenation
- Background music mixing
- Video assembly
"""

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
    def mock_settings(self):
        """Mock settings."""
        with patch("faceless.services.video_service.get_settings") as mock:
            settings = MagicMock()
            settings.ffmpeg_path = "ffmpeg"
            settings.ffprobe_path = "ffprobe"
            settings.get_videos_dir.return_value = Path("/tmp/videos")
            settings.get_final_output_dir.return_value = Path("/tmp/final")
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

"""
Unit tests for the subtitle service.

Tests subtitle generation, timestamp formatting, and animated captions.
"""

import json
import shutil
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from faceless.core.exceptions import ExternalToolError

# =============================================================================
# Timestamp Formatting Tests
# =============================================================================


class TestFormatTimestampSrt:
    """Tests for SRT timestamp formatting."""

    def test_format_zero(self) -> None:
        """Test formatting zero seconds."""
        from faceless.services.subtitle_service import format_timestamp_srt

        result = format_timestamp_srt(0.0)
        assert result == "00:00:00,000"

    def test_format_seconds(self) -> None:
        """Test formatting seconds only."""
        from faceless.services.subtitle_service import format_timestamp_srt

        result = format_timestamp_srt(45.5)
        assert result == "00:00:45,500"

    def test_format_minutes(self) -> None:
        """Test formatting minutes and seconds."""
        from faceless.services.subtitle_service import format_timestamp_srt

        result = format_timestamp_srt(125.25)  # 2:05.250
        assert result == "00:02:05,250"

    def test_format_hours(self) -> None:
        """Test formatting hours, minutes, and seconds."""
        from faceless.services.subtitle_service import format_timestamp_srt

        result = format_timestamp_srt(3725.5)  # 1:02:05.500
        assert result == "01:02:05,500"

    def test_format_milliseconds(self) -> None:
        """Test millisecond precision."""
        from faceless.services.subtitle_service import format_timestamp_srt

        result = format_timestamp_srt(1.123)
        assert result == "00:00:01,123"


class TestFormatTimestampVtt:
    """Tests for VTT timestamp formatting."""

    def test_format_zero(self) -> None:
        """Test formatting zero seconds."""
        from faceless.services.subtitle_service import format_timestamp_vtt

        result = format_timestamp_vtt(0.0)
        assert result == "00:00:00.000"

    def test_format_seconds(self) -> None:
        """Test formatting seconds only."""
        from faceless.services.subtitle_service import format_timestamp_vtt

        result = format_timestamp_vtt(45.5)
        assert result == "00:00:45.500"

    def test_uses_period_separator(self) -> None:
        """Test that VTT uses period instead of comma."""
        from faceless.services.subtitle_service import format_timestamp_vtt

        result = format_timestamp_vtt(1.5)
        assert "." in result
        assert "," not in result


# =============================================================================
# Get Audio Duration Tests
# =============================================================================


class TestGetAudioDuration:
    """Tests for audio duration detection."""

    @patch("faceless.services.subtitle_service.subprocess.run")
    def test_get_audio_duration_success(self, mock_run: MagicMock) -> None:
        """Test successful duration extraction."""
        from faceless.services.subtitle_service import get_audio_duration

        mock_run.return_value = MagicMock(returncode=0, stdout="125.5\n", stderr="")

        result = get_audio_duration("test.mp3")

        assert result == 125.5
        mock_run.assert_called_once()

    @patch("faceless.services.subtitle_service.subprocess.run")
    def test_get_audio_duration_timeout(self, mock_run: MagicMock) -> None:
        """Timeout errors must not fabricate a 60-second duration."""

        from faceless.services.subtitle_service import get_audio_duration

        mock_run.side_effect = subprocess.TimeoutExpired("ffprobe", 30)

        with pytest.raises(ExternalToolError, match="timed out"):
            get_audio_duration("test.mp3")

    @patch("faceless.services.subtitle_service.subprocess.run")
    def test_get_audio_duration_invalid_output(self, mock_run: MagicMock) -> None:
        """Invalid probe output must not fabricate a 60-second duration."""
        from faceless.services.subtitle_service import get_audio_duration

        mock_run.return_value = MagicMock(returncode=0, stdout="invalid", stderr="")

        with pytest.raises(ExternalToolError, match="invalid duration"):
            get_audio_duration("test.mp3")

    def test_get_audio_duration_configured_executable(self, tmp_path: Path) -> None:
        from faceless.services.subtitle_service import get_audio_duration

        executable = str(tmp_path / "tools & %PATH%" / "probe.exe")
        audio = tmp_path / "Alice's & %PATH%.mp3"
        with (
            patch("faceless.services.subtitle_service.get_settings") as mock_settings,
            patch("subprocess.run") as mock_run,
        ):
            mock_settings.return_value.ffprobe_path = executable
            mock_run.return_value = MagicMock(returncode=0, stdout="1.5", stderr="")
            assert get_audio_duration(audio) == 1.5
        assert mock_run.call_args.args[0][0] == executable
        assert mock_run.call_args.args[0][-1] == str(audio)
        assert mock_run.call_args.kwargs["shell"] is False

    def test_audio_probe_failure_does_not_write_subtitles(self, tmp_path: Path) -> None:
        from faceless.services.subtitle_service import create_subtitles_from_audio

        audio = tmp_path / "bad.mp3"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="60", stderr="corrupt audio"
            )
            with pytest.raises(ExternalToolError, match="probe failed"):
                create_subtitles_from_audio(audio, "finance")
        assert not audio.with_suffix(".srt").exists()
        assert not audio.with_suffix(".vtt").exists()


# =============================================================================
# Create Subtitles From Script Tests
# =============================================================================


class TestCreateSubtitlesFromScript:
    """Tests for creating subtitles from script files."""

    @pytest.fixture
    def sample_script(self, tmp_path: Path) -> Path:
        """Create a sample script file."""
        script = {
            "title": "Test Script",
            "scenes": [
                {
                    "scene_number": 1,
                    "narration": "This is the first scene with some narration text.",
                    "duration_estimate": 10.0,
                },
                {
                    "scene_number": 2,
                    "narration": "This is the second scene with more content.",
                    "duration_estimate": 8.0,
                },
            ],
        }
        script_path = tmp_path / "test_script.json"
        with open(script_path, "w") as f:
            json.dump(script, f)
        return script_path

    @patch("faceless.services.subtitle_service.get_settings")
    def test_creates_srt_and_vtt_files(
        self, mock_settings: MagicMock, sample_script: Path, tmp_path: Path
    ) -> None:
        """Test that both SRT and VTT files are created."""
        from faceless.services.subtitle_service import create_subtitles_from_script

        mock_settings.return_value.output_base_dir = tmp_path

        srt_path, vtt_path = create_subtitles_from_script(
            sample_script, "scary-stories", output_dir=tmp_path
        )

        assert srt_path.exists()
        assert vtt_path.exists()
        assert srt_path.suffix == ".srt"
        assert vtt_path.suffix == ".vtt"

    @patch("faceless.services.subtitle_service.get_settings")
    def test_srt_format(
        self, mock_settings: MagicMock, sample_script: Path, tmp_path: Path
    ) -> None:
        """Test SRT file format."""
        from faceless.services.subtitle_service import create_subtitles_from_script

        mock_settings.return_value.output_base_dir = tmp_path

        srt_path, _ = create_subtitles_from_script(
            sample_script, "scary-stories", output_dir=tmp_path
        )

        content = srt_path.read_text()

        # SRT should have numbered entries
        assert "1\n" in content
        # SRT uses comma for milliseconds
        assert "-->" in content

    @patch("faceless.services.subtitle_service.get_settings")
    def test_vtt_format(
        self, mock_settings: MagicMock, sample_script: Path, tmp_path: Path
    ) -> None:
        """Test VTT file format."""
        from faceless.services.subtitle_service import create_subtitles_from_script

        mock_settings.return_value.output_base_dir = tmp_path

        _, vtt_path = create_subtitles_from_script(
            sample_script, "scary-stories", output_dir=tmp_path
        )

        content = vtt_path.read_text()

        # VTT should start with WEBVTT header
        assert content.startswith("WEBVTT")
        assert "-->" in content

    @patch("faceless.services.subtitle_service.get_settings")
    def test_words_per_subtitle(self, mock_settings: MagicMock, tmp_path: Path) -> None:
        """Test that words_per_subtitle parameter works."""
        from faceless.services.subtitle_service import create_subtitles_from_script

        mock_settings.return_value.output_base_dir = tmp_path

        # Create script with known word count
        script = {
            "title": "Test",
            "scenes": [
                {
                    "scene_number": 1,
                    "narration": "One two three four five six seven eight nine ten",
                    "duration_estimate": 5.0,
                },
            ],
        }
        script_path = tmp_path / "script.json"
        with open(script_path, "w") as f:
            json.dump(script, f)

        srt_path, _ = create_subtitles_from_script(
            script_path, "scary-stories", output_dir=tmp_path, words_per_subtitle=5
        )

        content = srt_path.read_text()

        # Should have at least 2 subtitle entries for 10 words at 5 per subtitle
        assert content.count("-->") >= 2

    @patch("faceless.services.subtitle_service.get_settings")
    def test_empty_narration_handled(
        self, mock_settings: MagicMock, tmp_path: Path
    ) -> None:
        """Test handling scenes with empty narration."""
        from faceless.services.subtitle_service import create_subtitles_from_script

        mock_settings.return_value.output_base_dir = tmp_path

        script = {
            "title": "Test",
            "scenes": [
                {
                    "scene_number": 1,
                    "narration": "",
                    "duration_estimate": 5.0,
                },
                {
                    "scene_number": 2,
                    "narration": "Second scene with content.",
                    "duration_estimate": 5.0,
                },
            ],
        }
        script_path = tmp_path / "script.json"
        with open(script_path, "w") as f:
            json.dump(script, f)

        srt_path, vtt_path = create_subtitles_from_script(
            script_path, "scary-stories", output_dir=tmp_path
        )

        assert srt_path.exists()
        assert vtt_path.exists()

    @pytest.mark.parametrize("chunk_size", [0, -1, False])
    def test_invalid_chunk_size_is_rejected(
        self, tmp_path: Path, chunk_size: int
    ) -> None:
        """A zero or negative chunk size cannot generate timed subtitles."""
        from faceless.core.exceptions import InputValidationError
        from faceless.services.subtitle_service import create_subtitles_from_script

        with pytest.raises(InputValidationError, match="words_per_subtitle"):
            create_subtitles_from_script(
                tmp_path / "unused.json",
                "scary-stories",
                output_dir=tmp_path,
                words_per_subtitle=chunk_size,
            )


# =============================================================================
# Create Subtitles From Audio Tests
# =============================================================================


class TestCreateSubtitlesFromAudio:
    """Tests for creating subtitles from audio files."""

    @patch("faceless.services.subtitle_service.get_audio_duration")
    def test_creates_placeholder_subtitles(
        self, mock_duration: MagicMock, tmp_path: Path
    ) -> None:
        """Test that placeholder subtitles are created."""
        from faceless.services.subtitle_service import create_subtitles_from_audio

        mock_duration.return_value = 120.0

        audio_path = tmp_path / "test.mp3"
        audio_path.touch()

        srt_path, vtt_path = create_subtitles_from_audio(audio_path, "scary-stories")

        assert srt_path.exists()
        assert vtt_path.exists()

    @patch("faceless.services.subtitle_service.get_audio_duration")
    def test_skips_if_exists(self, mock_duration: MagicMock, tmp_path: Path) -> None:
        """Test that existing subtitles are not overwritten."""
        from faceless.services.subtitle_service import create_subtitles_from_audio

        audio_path = tmp_path / "test.mp3"
        audio_path.touch()

        srt_path = tmp_path / "test.srt"
        vtt_path = tmp_path / "test.vtt"
        srt_path.write_text("existing")
        vtt_path.write_text("existing")

        result_srt, result_vtt = create_subtitles_from_audio(
            audio_path, "scary-stories"
        )

        assert result_srt.read_text() == "existing"
        mock_duration.assert_not_called()

    @patch("faceless.services.subtitle_service.get_audio_duration")
    def test_placeholder_content(
        self, mock_duration: MagicMock, tmp_path: Path
    ) -> None:
        """Test placeholder subtitle content."""
        from faceless.services.subtitle_service import create_subtitles_from_audio

        mock_duration.return_value = 60.0

        audio_path = tmp_path / "test.mp3"
        audio_path.touch()

        srt_path, _ = create_subtitles_from_audio(audio_path, "scary-stories")

        content = srt_path.read_text()
        assert "[Audio transcription pending]" in content


# =============================================================================
# Burn Subtitles Tests
# =============================================================================


class TestBurnSubtitlesToVideo:
    """Tests for burning subtitles into video."""

    @staticmethod
    def _successful_run(
        cmd: list[str], **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        Path(cmd[-1]).write_bytes(b"mock video")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    @patch("faceless.services.subtitle_service.subprocess.run")
    def test_burn_subtitles_success(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test successful subtitle burning."""
        from faceless.services.subtitle_service import burn_subtitles_to_video

        mock_run.side_effect = self._successful_run

        video_path = tmp_path / "video.mp4"
        video_path.touch()
        subtitle_path = tmp_path / "subs.srt"
        subtitle_path.touch()
        output_path = tmp_path / "nested" / "output.mp4"

        result = burn_subtitles_to_video(
            video_path, subtitle_path, output_path, "scary-stories"
        )

        assert result == output_path
        assert output_path.read_bytes() == b"mock video"
        mock_run.assert_called_once()
        assert mock_run.call_args.kwargs["timeout"] == 600
        assert mock_run.call_args.kwargs["capture_output"] is True
        assert "shell" not in mock_run.call_args.kwargs

    @patch("faceless.services.subtitle_service.subprocess.run")
    def test_burn_subtitles_with_style_override(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Test subtitle burning with style override."""
        from faceless.services.subtitle_service import burn_subtitles_to_video

        mock_run.side_effect = self._successful_run

        video_path = tmp_path / "video.mp4"
        video_path.touch()
        subtitle_path = tmp_path / "subs.srt"
        subtitle_path.touch()
        output_path = tmp_path / "output.mp4"

        result = burn_subtitles_to_video(
            video_path,
            subtitle_path,
            output_path,
            "scary-stories",
            style_override={"font_size": 64},
        )

        assert result == output_path
        cmd = mock_run.call_args.args[0]
        assert "FontSize=64" in cmd[cmd.index("-vf") + 1]

    @patch("faceless.services.subtitle_service.subprocess.run")
    def test_portrait_override_and_escaped_path(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """The filtergraph keeps special characters in paths and ASS styles."""
        from faceless.services.subtitle_service import (
            burn_subtitles_to_video,
            portrait_caption_style,
        )

        mock_run.side_effect = self._successful_run
        video_path = tmp_path / "video.mp4"
        video_path.touch()
        subtitle_path = tmp_path / "it's a:caption\\demo,[];.srt"
        subtitle_path.touch()

        burn_subtitles_to_video(
            video_path,
            subtitle_path,
            tmp_path / "captioned.mp4",
            "finance",
            style_override=portrait_caption_style("finance"),
        )

        cmd = mock_run.call_args.args[0]
        filter_spec = cmd[cmd.index("-vf") + 1]
        assert "subtitles=filename=" in filter_spec
        assert r"\:" in filter_spec
        assert r"\'" in filter_spec
        assert r"\\" in filter_spec
        assert r"\," in filter_spec
        assert "MarginR=240" in filter_spec
        assert "MarginV=520" in filter_spec
        assert "PlayResY=1920" in filter_spec

    @patch("faceless.services.subtitle_service.subprocess.run")
    def test_burn_subtitles_ffmpeg_error(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Test handling FFmpeg errors."""
        from faceless.core.exceptions import FFmpegError
        from faceless.services.subtitle_service import burn_subtitles_to_video

        mock_run.return_value = MagicMock(returncode=1, stderr="FFmpeg error")

        video_path = tmp_path / "video.mp4"
        video_path.touch()
        subtitle_path = tmp_path / "subs.srt"
        subtitle_path.touch()
        output_path = tmp_path / "output.mp4"

        with pytest.raises(FFmpegError, match="FFmpeg subtitle burn failed"):
            burn_subtitles_to_video(
                video_path, subtitle_path, output_path, "scary-stories"
            )
        assert not output_path.exists()

    @pytest.mark.parametrize("failure", ["timeout", "missing_binary", "empty_output"])
    @patch("faceless.services.subtitle_service.subprocess.run")
    def test_ffmpeg_failure_does_not_report_success(
        self, mock_run: MagicMock, failure: str, tmp_path: Path
    ) -> None:
        """Timeouts, missing executables, and missing output raise FFmpegError."""
        from faceless.core.exceptions import FFmpegError
        from faceless.services.subtitle_service import burn_subtitles_to_video

        video_path = tmp_path / "video.mp4"
        video_path.touch()
        subtitle_path = tmp_path / "subs.srt"
        subtitle_path.touch()
        output_path = tmp_path / "output.mp4"
        if failure == "timeout":
            mock_run.side_effect = subprocess.TimeoutExpired("ffmpeg", 600)
        elif failure == "missing_binary":
            mock_run.side_effect = FileNotFoundError("ffmpeg")
        else:
            mock_run.return_value = subprocess.CompletedProcess([], 0, "", "")

        with patch("faceless.services.subtitle_service.logger") as mock_logger:
            with pytest.raises(FFmpegError):
                burn_subtitles_to_video(video_path, subtitle_path, output_path)
            mock_logger.error.assert_called_once()
            assert not any(
                call.args[0] == "Created video with subtitles"
                for call in mock_logger.info.call_args_list
            )

    @pytest.mark.parametrize(
        "invalid_input", ["video", "subtitles", "output", "format"]
    )
    @patch("faceless.services.subtitle_service.subprocess.run")
    def test_rejects_invalid_paths(
        self, mock_run: MagicMock, invalid_input: str, tmp_path: Path
    ) -> None:
        """Reject missing input, unsupported subtitles, and destructive outputs."""
        from faceless.core.exceptions import InputValidationError
        from faceless.services.subtitle_service import burn_subtitles_to_video

        video_path = tmp_path / "video.mp4"
        video_path.touch()
        subtitle_path = tmp_path / "subs.srt"
        subtitle_path.touch()
        output_path = tmp_path / "output.mp4"
        if invalid_input == "video":
            video_path.unlink()
        elif invalid_input == "subtitles":
            subtitle_path.unlink()
        elif invalid_input == "output":
            output_path = video_path
        else:
            subtitle_path = subtitle_path.rename(tmp_path / "subs.txt")

        with pytest.raises(InputValidationError):
            burn_subtitles_to_video(video_path, subtitle_path, output_path)
        mock_run.assert_not_called()

    @pytest.mark.parametrize(
        "invalid_style",
        [
            {"font_name": "Arial',evil=1"},
            {"font_size": 0},
            {"margin_r": -1},
            {"alignment": 10},
            {"play_res_y": 0},
            {"primary_color": "red"},
            {"font_size": float("nan")},
            {"unknown_option": "unsafe"},
        ],
    )
    @patch("faceless.services.subtitle_service.subprocess.run")
    def test_rejects_invalid_style_overrides(
        self, mock_run: MagicMock, invalid_style: dict[str, object], tmp_path: Path
    ) -> None:
        """Style overrides cannot inject filter syntax or hide captions."""
        from faceless.core.exceptions import InputValidationError
        from faceless.services.subtitle_service import burn_subtitles_to_video

        video_path = tmp_path / "video.mp4"
        video_path.touch()
        subtitle_path = tmp_path / "subs.srt"
        subtitle_path.touch()

        with pytest.raises(InputValidationError):
            burn_subtitles_to_video(
                video_path,
                subtitle_path,
                tmp_path / "output.mp4",
                style_override=invalid_style,
            )
        mock_run.assert_not_called()

    @pytest.mark.skipif(
        shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
        reason="FFmpeg and FFprobe are required for the portrait smoke test",
    )
    def test_portrait_smoke_with_special_subtitle_path(self, tmp_path: Path) -> None:
        """A real burn yields video and keeps visible text in the safe zone."""
        from faceless.services.subtitle_service import (
            burn_subtitles_to_video,
            portrait_caption_style,
        )

        video_path = tmp_path / "portrait.mp4"
        subtitle_path = tmp_path / "it's a:caption\\demo,[];.srt"
        subtitle_path.write_text(
            "1\n00:00:00,000 --> 00:00:02,000\n"
            "Readable captions are clear in a portrait video\n",
            encoding="utf-8",
        )
        output_path = tmp_path / "captioned.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "color=c=0x303030:s=1080x1920:r=1:d=2",
                "-c:v",
                "mpeg4",
                "-threads",
                "2",
                str(video_path),
            ],
            capture_output=True,
            check=True,
            timeout=60,
        )

        burn_subtitles_to_video(
            video_path,
            subtitle_path,
            output_path,
            style_override=portrait_caption_style("scary-stories"),
        )

        probe = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height,codec_name",
                "-of",
                "json",
                str(output_path),
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        stream = json.loads(probe.stdout)["streams"][0]
        assert (stream["width"], stream["height"]) == (1080, 1920)
        assert stream["codec_name"] != ""

        frame = subprocess.run(
            [
                "ffmpeg",
                "-loglevel",
                "error",
                "-ss",
                "0.5",
                "-i",
                str(output_path),
                "-frames:v",
                "1",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "rgb24",
                "-",
            ],
            capture_output=True,
            check=True,
            timeout=60,
        ).stdout
        assert len(frame) == 1080 * 1920 * 3
        bright_pixels = [
            (x, y)
            for y in range(0, 1920, 2)
            for x in range(0, 1080, 2)
            if min(frame[(y * 1080 + x) * 3 : (y * 1080 + x) * 3 + 3]) > 210
        ]
        assert len(bright_pixels) > 300
        assert min(y for _, y in bright_pixels) > 850
        assert max(y for _, y in bright_pixels) < 1600
        assert min(x for x, _ in bright_pixels) > 40
        assert max(x for x, _ in bright_pixels) < 900


# =============================================================================
# Generate Animated Captions Tests
# =============================================================================


class TestGenerateAnimatedCaptions:
    """Tests for animated caption generation."""

    @patch("faceless.services.subtitle_service.get_settings")
    def test_generates_caption_json(
        self, mock_settings: MagicMock, tmp_path: Path
    ) -> None:
        """Test that animated caption JSON is generated."""
        from faceless.services.subtitle_service import generate_animated_captions

        mock_settings.return_value.output_base_dir = tmp_path

        script = {
            "title": "Test Script",
            "scenes": [
                {
                    "scene_number": 1,
                    "narration": "Hello world this is a test.",
                    "duration_estimate": 5.0,
                },
            ],
        }
        script_path = tmp_path / "script.json"
        with open(script_path, "w") as f:
            json.dump(script, f)

        result = generate_animated_captions(
            script_path, "scary-stories", output_dir=tmp_path
        )

        assert result.exists()
        assert result.suffix == ".json"

    @patch("faceless.services.subtitle_service.get_settings")
    def test_caption_structure(self, mock_settings: MagicMock, tmp_path: Path) -> None:
        """Test animated caption data structure."""
        from faceless.services.subtitle_service import generate_animated_captions

        mock_settings.return_value.output_base_dir = tmp_path

        script = {
            "title": "Test Script",
            "scenes": [
                {
                    "scene_number": 1,
                    "narration": "One two three",
                    "duration_estimate": 3.0,
                },
            ],
        }
        script_path = tmp_path / "script.json"
        with open(script_path, "w") as f:
            json.dump(script, f)

        result = generate_animated_captions(
            script_path, "scary-stories", output_dir=tmp_path
        )

        with open(result) as f:
            data = json.load(f)

        assert "captions" in data
        assert "word_count" in data
        assert data["word_count"] == 3

        for caption in data["captions"]:
            assert "word" in caption
            assert "start" in caption
            assert "end" in caption
            assert "scene" in caption

    @patch("faceless.services.subtitle_service.get_settings")
    def test_caption_timing(self, mock_settings: MagicMock, tmp_path: Path) -> None:
        """Test that caption timing is sequential."""
        from faceless.services.subtitle_service import generate_animated_captions

        mock_settings.return_value.output_base_dir = tmp_path

        script = {
            "title": "Test",
            "scenes": [
                {
                    "scene_number": 1,
                    "narration": "Word one two three",
                    "duration_estimate": 4.0,
                },
            ],
        }
        script_path = tmp_path / "script.json"
        with open(script_path, "w") as f:
            json.dump(script, f)

        result = generate_animated_captions(
            script_path, "scary-stories", output_dir=tmp_path
        )

        with open(result) as f:
            data = json.load(f)

        captions = data["captions"]
        for i in range(1, len(captions)):
            assert captions[i]["start"] >= captions[i - 1]["start"]


# =============================================================================
# Generate All Subtitle Formats Tests
# =============================================================================


class TestGenerateAllSubtitleFormats:
    """Tests for generating all subtitle formats."""

    @patch("faceless.services.subtitle_service.get_settings")
    def test_generates_all_formats(
        self, mock_settings: MagicMock, tmp_path: Path
    ) -> None:
        """Test that all subtitle formats are generated."""
        from faceless.services.subtitle_service import generate_all_subtitle_formats

        mock_settings.return_value.output_base_dir = tmp_path

        script = {
            "title": "Test",
            "scenes": [
                {
                    "scene_number": 1,
                    "narration": "Test narration content.",
                    "duration_estimate": 5.0,
                },
            ],
        }
        script_path = tmp_path / "script.json"
        with open(script_path, "w") as f:
            json.dump(script, f)

        result = generate_all_subtitle_formats(
            script_path, "scary-stories", output_dir=tmp_path
        )

        assert "srt" in result
        assert "vtt" in result
        assert "animated_json" in result

        assert result["srt"].exists()
        assert result["vtt"].exists()
        assert result["animated_json"].exists()


# =============================================================================
# Subtitle Style Tests
# =============================================================================


class TestSubtitleStyles:
    """Tests for subtitle style presets."""

    def test_scary_stories_style_exists(self) -> None:
        """Test scary-stories style preset exists."""
        from faceless.services.subtitle_service import SUBTITLE_STYLES

        assert "scary-stories" in SUBTITLE_STYLES
        style = SUBTITLE_STYLES["scary-stories"]
        assert "font_name" in style
        assert "font_size" in style

    def test_finance_style_exists(self) -> None:
        """Test finance style preset exists."""
        from faceless.services.subtitle_service import SUBTITLE_STYLES

        assert "finance" in SUBTITLE_STYLES

    def test_luxury_style_exists(self) -> None:
        """Test luxury style preset exists."""
        from faceless.services.subtitle_service import SUBTITLE_STYLES

        assert "luxury" in SUBTITLE_STYLES

    def test_portrait_style_is_high_contrast_and_does_not_mutate_preset(self) -> None:
        """A separate portrait override preserves the existing landscape preset."""
        from faceless.services.subtitle_service import (
            SUBTITLE_STYLES,
            portrait_caption_style,
        )

        initial = SUBTITLE_STYLES["finance"].copy()
        style = portrait_caption_style("finance")
        assert style["primary_color"] == "&H00FFFFFF"
        assert style["outline_color"] == "&H00000000"
        assert style["font_size"] >= 70
        assert style["margin_r"] > style["margin_l"]
        assert style["margin_v"] >= 400
        assert style["alignment"] == 2
        assert SUBTITLE_STYLES["finance"] == initial

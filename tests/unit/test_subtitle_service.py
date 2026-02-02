"""
Unit tests for the subtitle service.

Tests subtitle generation, timestamp formatting, and animated captions.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

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

        mock_run.return_value = MagicMock(stdout="125.5\n")

        result = get_audio_duration("test.mp3")

        assert result == 125.5
        mock_run.assert_called_once()

    @patch("faceless.services.subtitle_service.subprocess.run")
    def test_get_audio_duration_timeout(self, mock_run: MagicMock) -> None:
        """Test fallback on timeout."""
        import subprocess

        from faceless.services.subtitle_service import get_audio_duration

        mock_run.side_effect = subprocess.TimeoutExpired("ffprobe", 30)

        result = get_audio_duration("test.mp3")

        assert result == 60.0  # Default fallback

    @patch("faceless.services.subtitle_service.subprocess.run")
    def test_get_audio_duration_invalid_output(self, mock_run: MagicMock) -> None:
        """Test fallback on invalid output."""
        from faceless.services.subtitle_service import get_audio_duration

        mock_run.return_value = MagicMock(stdout="invalid")

        result = get_audio_duration("test.mp3")

        assert result == 60.0  # Default fallback


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

    @patch("faceless.services.subtitle_service.subprocess.run")
    def test_burn_subtitles_success(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test successful subtitle burning."""
        from faceless.services.subtitle_service import burn_subtitles_to_video

        mock_run.return_value = MagicMock(returncode=0, stderr="")

        video_path = tmp_path / "video.mp4"
        video_path.touch()
        subtitle_path = tmp_path / "subs.srt"
        subtitle_path.touch()
        output_path = tmp_path / "output.mp4"

        result = burn_subtitles_to_video(
            video_path, subtitle_path, output_path, "scary-stories"
        )

        assert result == output_path
        mock_run.assert_called_once()

    @patch("faceless.services.subtitle_service.subprocess.run")
    def test_burn_subtitles_with_style_override(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Test subtitle burning with style override."""
        from faceless.services.subtitle_service import burn_subtitles_to_video

        mock_run.return_value = MagicMock(returncode=0, stderr="")

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

    @patch("faceless.services.subtitle_service.subprocess.run")
    def test_burn_subtitles_ffmpeg_error(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Test handling FFmpeg errors."""
        from faceless.services.subtitle_service import burn_subtitles_to_video

        mock_run.return_value = MagicMock(returncode=1, stderr="FFmpeg error")

        video_path = tmp_path / "video.mp4"
        video_path.touch()
        subtitle_path = tmp_path / "subs.srt"
        subtitle_path.touch()
        output_path = tmp_path / "output.mp4"

        with pytest.raises(RuntimeError, match="FFmpeg subtitle burn failed"):
            burn_subtitles_to_video(
                video_path, subtitle_path, output_path, "scary-stories"
            )


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

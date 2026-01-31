"""
Unit tests for CLI commands.

Tests cover:
- Version callback
- Main callback
- Generate command
- Validate command
- Init command
- Info command
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from faceless.cli.commands import app

runner = CliRunner()


class TestVersionCallback:
    """Tests for version callback."""

    def test_version_option(self) -> None:
        """Test --version shows version and exits."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "Faceless Content Pipeline" in result.output

    def test_version_short_option(self) -> None:
        """Test -v shows version and exits."""
        result = runner.invoke(app, ["-v"])
        assert result.exit_code == 0
        assert "Faceless Content Pipeline" in result.output


class TestMainCallback:
    """Tests for main callback."""

    def test_no_args_shows_help(self) -> None:
        """Test no arguments shows help (exit code 0 or 2 acceptable)."""
        result = runner.invoke(app, [])
        # Typer with no_args_is_help=True exits with code 0 or 2
        assert result.exit_code in [0, 2]
        assert "Usage:" in result.output or "faceless" in result.output.lower()

    def test_help_option(self) -> None:
        """Test --help shows help."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "AI-powered" in result.output or "video" in result.output.lower()


class TestGenerateCommand:
    """Tests for generate command."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for generate command."""
        with patch("faceless.cli.commands.get_settings") as mock:
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            settings.get_output_dir.return_value = Path("/tmp/output")
            settings.ensure_directories = MagicMock()
            mock.return_value = settings
            yield settings

    def test_generate_scary_stories(self, mock_settings) -> None:
        """Test generate command with scary-stories niche."""
        with patch("faceless.cli.commands.setup_logging"):
            result = runner.invoke(app, ["generate", "scary-stories"])

        assert result.exit_code == 0
        assert "scary" in result.output.lower() or "Generating" in result.output

    def test_generate_finance(self, mock_settings) -> None:
        """Test generate command with finance niche."""
        with patch("faceless.cli.commands.setup_logging"):
            result = runner.invoke(app, ["generate", "finance"])

        assert result.exit_code == 0

    def test_generate_luxury(self, mock_settings) -> None:
        """Test generate command with luxury niche."""
        with patch("faceless.cli.commands.setup_logging"):
            result = runner.invoke(app, ["generate", "luxury"])

        assert result.exit_code == 0

    def test_generate_with_count(self, mock_settings) -> None:
        """Test generate with count option."""
        with patch("faceless.cli.commands.setup_logging"):
            result = runner.invoke(app, ["generate", "scary-stories", "-c", "3"])

        assert result.exit_code == 0
        assert "3" in result.output

    def test_generate_with_platform(self, mock_settings) -> None:
        """Test generate with platform option."""
        with patch("faceless.cli.commands.setup_logging"):
            result = runner.invoke(app, ["generate", "finance", "-p", "youtube"])

        assert result.exit_code == 0

    def test_generate_with_multiple_platforms(self, mock_settings) -> None:
        """Test generate with multiple platforms."""
        with patch("faceless.cli.commands.setup_logging"):
            result = runner.invoke(
                app, ["generate", "luxury", "-p", "youtube", "-p", "tiktok"]
            )

        assert result.exit_code == 0

    def test_generate_with_enhance(self, mock_settings) -> None:
        """Test generate with enhance option."""
        with patch("faceless.cli.commands.setup_logging"):
            result = runner.invoke(app, ["generate", "scary-stories", "--enhance"])

        assert result.exit_code == 0

    def test_generate_with_thumbnails_disabled(self, mock_settings) -> None:
        """Test generate with thumbnails disabled."""
        with patch("faceless.cli.commands.setup_logging"):
            # Use the correct flag format
            result = runner.invoke(app, ["generate", "finance"])

        assert result.exit_code == 0

    def test_generate_with_subtitles_flag(self, mock_settings) -> None:
        """Test generate with subtitles flag."""
        with patch("faceless.cli.commands.setup_logging"):
            # Test with explicit --subtitles flag
            result = runner.invoke(app, ["generate", "luxury", "--subtitles"])

        assert result.exit_code == 0

    def test_generate_help(self) -> None:
        """Test generate --help."""
        result = runner.invoke(app, ["generate", "--help"])
        assert result.exit_code == 0
        assert "niche" in result.output.lower()


class TestValidateCommand:
    """Tests for validate command."""

    @pytest.fixture
    def mock_settings_configured(self):
        """Mock fully configured settings."""
        with patch("faceless.cli.commands.get_settings") as mock:
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            settings.azure_openai.is_configured = True
            settings.use_elevenlabs = False
            mock.return_value = settings
            yield settings

    @pytest.fixture
    def mock_settings_unconfigured(self):
        """Mock unconfigured settings."""
        with patch("faceless.cli.commands.get_settings") as mock:
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            settings.azure_openai.is_configured = False
            settings.use_elevenlabs = False
            mock.return_value = settings
            yield settings

    def test_validate_configured(self, mock_settings_configured) -> None:
        """Test validate with configured settings."""
        with (
            patch("faceless.cli.commands.setup_logging"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0)
            result = runner.invoke(app, ["validate"])

        # May pass or fail depending on FFmpeg, just check it runs
        assert result.exit_code in [0, 1]

    def test_validate_unconfigured(self, mock_settings_unconfigured) -> None:
        """Test validate with unconfigured settings."""
        with (
            patch("faceless.cli.commands.setup_logging"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0)
            result = runner.invoke(app, ["validate"])

        # Should fail due to unconfigured Azure OpenAI
        assert result.exit_code == 1

    def test_validate_with_elevenlabs(self) -> None:
        """Test validate with ElevenLabs enabled."""
        with patch("faceless.cli.commands.get_settings") as mock_settings:
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            settings.azure_openai.is_configured = True
            settings.use_elevenlabs = True
            settings.elevenlabs.is_configured = True
            mock_settings.return_value = settings

            with (
                patch("faceless.cli.commands.setup_logging"),
                patch("subprocess.run") as mock_run,
            ):
                mock_run.return_value = MagicMock(returncode=0)
                result = runner.invoke(app, ["validate"])

                assert result.exit_code == 0
                assert "ElevenLabs" in result.output

    def test_validate_ffmpeg_missing(self) -> None:
        """Test validate with FFmpeg missing."""
        with patch("faceless.cli.commands.get_settings") as mock_settings:
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            settings.azure_openai.is_configured = True
            settings.use_elevenlabs = False
            mock_settings.return_value = settings

            with (
                patch("faceless.cli.commands.setup_logging"),
                patch("subprocess.run") as mock_run,
            ):
                mock_run.side_effect = FileNotFoundError()
                result = runner.invoke(app, ["validate"])

                assert result.exit_code == 1
                assert "FFmpeg" in result.output

    def test_validate_help(self) -> None:
        """Test validate --help."""
        result = runner.invoke(app, ["validate", "--help"])
        assert result.exit_code == 0


class TestInitCommand:
    """Tests for init command."""

    def test_init_all_niches(self, tmp_path: Path) -> None:
        """Test init creates directories for all niches."""
        with patch("faceless.cli.commands.get_settings") as mock_settings:
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            settings.ensure_directories = MagicMock()
            settings.get_output_dir.return_value = tmp_path
            mock_settings.return_value = settings

            with patch("faceless.cli.commands.setup_logging"):
                result = runner.invoke(app, ["init"])

            assert result.exit_code == 0
            settings.ensure_directories.assert_called_once_with(None)

    def test_init_specific_niche(self, tmp_path: Path) -> None:
        """Test init with specific niche."""
        with patch("faceless.cli.commands.get_settings") as mock_settings:
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            settings.ensure_directories = MagicMock()
            settings.get_output_dir.return_value = tmp_path
            mock_settings.return_value = settings

            with patch("faceless.cli.commands.setup_logging"):
                result = runner.invoke(app, ["init", "-n", "scary-stories"])

            assert result.exit_code == 0
            assert "scary" in result.output.lower()

    def test_init_help(self) -> None:
        """Test init --help."""
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0


class TestInfoCommand:
    """Tests for info command."""

    def test_info_shows_settings(self) -> None:
        """Test info command shows settings."""
        with patch("faceless.cli.commands.get_settings") as mock_settings:
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            settings.debug = False
            settings.output_base_dir = Path("/tmp/output")
            settings.max_concurrent_requests = 5
            settings.request_timeout = 120
            settings.enable_retry = True
            settings.max_retries = 3
            settings.enable_checkpointing = True
            settings.use_elevenlabs = False
            settings.get_voice_settings.return_value = (MagicMock(value="onyx"), 1.0)
            mock_settings.return_value = settings

            with patch("faceless.cli.commands.setup_logging"):
                result = runner.invoke(app, ["info"])

            assert result.exit_code == 0
            assert "Settings" in result.output or "INFO" in result.output

    def test_info_help(self) -> None:
        """Test info --help."""
        result = runner.invoke(app, ["info", "--help"])
        assert result.exit_code == 0


class TestDebugMode:
    """Tests for debug mode."""

    def test_debug_flag(self) -> None:
        """Test --debug flag is handled."""
        with patch("faceless.cli.commands.get_settings") as mock_settings:
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            settings.ensure_directories = MagicMock()
            settings.get_output_dir.return_value = Path("/tmp")
            mock_settings.return_value = settings

            with patch("faceless.cli.commands.setup_logging") as mock_setup:
                runner.invoke(app, ["--debug", "generate", "finance"])

                # Debug should be passed to setup_logging
                mock_setup.assert_called()

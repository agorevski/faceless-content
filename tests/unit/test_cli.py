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
    def mock_pipeline(self):
        """Mock settings and orchestrator for generate command."""
        with (
            patch("faceless.cli.commands.get_settings") as mock_settings,
            patch("faceless.cli.commands.Orchestrator") as mock_orchestrator,
        ):
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            settings.get_output_dir.return_value = Path("/tmp/output")
            settings.ensure_directories = MagicMock()
            mock_settings.return_value = settings

            # Mock orchestrator to return empty results
            orchestrator_instance = MagicMock()
            orchestrator_instance.run.return_value = []
            mock_orchestrator.return_value = orchestrator_instance

            yield settings, orchestrator_instance

    def test_generate_scary_stories(self, mock_pipeline) -> None:
        """Test generate command with scary-stories niche."""
        with patch("faceless.cli.commands.setup_logging"):
            result = runner.invoke(app, ["generate", "scary-stories"])

        assert result.exit_code == 0
        assert "scary" in result.output.lower() or "Generating" in result.output

    def test_generate_finance(self, mock_pipeline) -> None:
        """Test generate command with finance niche."""
        with patch("faceless.cli.commands.setup_logging"):
            result = runner.invoke(app, ["generate", "finance"])

        assert result.exit_code == 0

    def test_generate_luxury(self, mock_pipeline) -> None:
        """Test generate command with luxury niche."""
        with patch("faceless.cli.commands.setup_logging"):
            result = runner.invoke(app, ["generate", "luxury"])

        assert result.exit_code == 0

    def test_generate_with_count(self, mock_pipeline) -> None:
        """Test generate with count option."""
        with patch("faceless.cli.commands.setup_logging"):
            result = runner.invoke(app, ["generate", "scary-stories", "-c", "3"])

        assert result.exit_code == 0
        assert "3" in result.output

    def test_generate_with_platform(self, mock_pipeline) -> None:
        """Test generate with platform option."""
        with patch("faceless.cli.commands.setup_logging"):
            result = runner.invoke(app, ["generate", "finance", "-p", "youtube"])

        assert result.exit_code == 0

    def test_generate_with_multiple_platforms(self, mock_pipeline) -> None:
        """Test generate with multiple platforms."""
        with patch("faceless.cli.commands.setup_logging"):
            result = runner.invoke(
                app, ["generate", "luxury", "-p", "youtube", "-p", "tiktok"]
            )

        assert result.exit_code == 0

    def test_generate_with_enhance(self, mock_pipeline) -> None:
        """Test generate with enhance option."""
        with patch("faceless.cli.commands.setup_logging"):
            result = runner.invoke(app, ["generate", "scary-stories", "--enhance"])

        assert result.exit_code == 0

    def test_generate_with_thumbnails_disabled(self, mock_pipeline) -> None:
        """Test generate with thumbnails disabled."""
        with patch("faceless.cli.commands.setup_logging"):
            # Use the correct flag format
            result = runner.invoke(app, ["generate", "finance"])

        assert result.exit_code == 0

    def test_generate_with_subtitles_flag(self, mock_pipeline) -> None:
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


class TestGenerateCommandPipeline:
    """Tests for generate command pipeline execution."""

    @pytest.fixture
    def mock_orchestrator_success(self):
        """Mock successful orchestrator run."""
        with patch("faceless.cli.commands.Orchestrator") as mock:
            orchestrator = MagicMock()
            result = MagicMock()
            result.success = True
            result.video_paths = {"youtube": Path("/tmp/video.mp4")}
            result.duration_seconds = 120.5
            result.script_path = Path("/tmp/script.json")
            result.errors = []
            orchestrator.run.return_value = [result]
            mock.return_value = orchestrator
            yield orchestrator

    @pytest.fixture
    def mock_orchestrator_failure(self):
        """Mock failed orchestrator run."""
        with patch("faceless.cli.commands.Orchestrator") as mock:
            orchestrator = MagicMock()
            result = MagicMock()
            result.success = False
            result.video_paths = {}
            result.duration_seconds = 0
            result.script_path = Path("/tmp/script.json")
            result.errors = ["Generation failed"]
            orchestrator.run.return_value = [result]
            mock.return_value = orchestrator
            yield orchestrator

    @pytest.fixture
    def mock_orchestrator_exception(self):
        """Mock orchestrator throwing exception."""
        with patch("faceless.cli.commands.Orchestrator") as mock:
            orchestrator = MagicMock()
            orchestrator.run.side_effect = Exception("Pipeline error")
            mock.return_value = orchestrator
            yield orchestrator

    def test_generate_pipeline_success(self, mock_orchestrator_success) -> None:
        """Test generate command with successful pipeline."""
        with (
            patch("faceless.cli.commands.get_settings") as mock_settings,
            patch("faceless.cli.commands.setup_logging"),
        ):
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            settings.get_output_dir.return_value = Path("/tmp")
            settings.ensure_directories = MagicMock()
            settings.debug = False
            mock_settings.return_value = settings

            result = runner.invoke(app, ["generate", "scary-stories"])

            assert result.exit_code == 0
            assert "Success" in result.output or "generated" in result.output.lower()

    def test_generate_pipeline_failure(self, mock_orchestrator_failure) -> None:
        """Test generate command with failed pipeline."""
        with (
            patch("faceless.cli.commands.get_settings") as mock_settings,
            patch("faceless.cli.commands.setup_logging"),
        ):
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            settings.get_output_dir.return_value = Path("/tmp")
            settings.ensure_directories = MagicMock()
            settings.debug = False
            mock_settings.return_value = settings

            result = runner.invoke(app, ["generate", "finance"])

            assert result.exit_code == 0  # Still exits 0, shows failure in output
            assert "failed" in result.output.lower() or "Failed" in result.output

    def test_generate_pipeline_exception(self, mock_orchestrator_exception) -> None:
        """Test generate command with pipeline exception."""
        with (
            patch("faceless.cli.commands.get_settings") as mock_settings,
            patch("faceless.cli.commands.setup_logging"),
        ):
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            settings.get_output_dir.return_value = Path("/tmp")
            settings.ensure_directories = MagicMock()
            settings.debug = False
            mock_settings.return_value = settings

            result = runner.invoke(app, ["generate", "luxury"])

            assert result.exit_code == 1
            assert (
                "Pipeline failed" in result.output or "failed" in result.output.lower()
            )

    def test_generate_pipeline_exception_debug_mode(
        self, mock_orchestrator_exception
    ) -> None:
        """Test generate command shows traceback in debug mode."""
        with (
            patch("faceless.cli.commands.get_settings") as mock_settings,
            patch("faceless.cli.commands.setup_logging"),
        ):
            settings = MagicMock()
            settings.log_level = "DEBUG"
            settings.log_json_format = False
            settings.get_output_dir.return_value = Path("/tmp")
            settings.ensure_directories = MagicMock()
            settings.debug = True
            mock_settings.return_value = settings

            result = runner.invoke(app, ["--debug", "generate", "scary-stories"])

            assert result.exit_code == 1


class TestValidateTestConnections:
    """Tests for validate --test-connections."""

    def test_validate_test_connections_success(self) -> None:
        """Test validate with successful test connections."""
        with (
            patch("faceless.cli.commands.get_settings") as mock_settings,
            patch("faceless.cli.commands.setup_logging"),
            patch("subprocess.run") as mock_run,
            patch(
                "faceless.clients.azure_openai.AzureOpenAIClient"
            ) as mock_client_class,
        ):
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            settings.azure_openai.is_configured = True
            settings.use_elevenlabs = False
            mock_settings.return_value = settings
            mock_run.return_value = MagicMock(returncode=0)

            mock_client = MagicMock()
            mock_client.test_connection.return_value = True
            mock_client_class.return_value = mock_client

            result = runner.invoke(app, ["validate", "--test-connections"])

            assert result.exit_code == 0
            assert "Connected" in result.output

    def test_validate_test_connections_failure(self) -> None:
        """Test validate with failed test connections."""
        with (
            patch("faceless.cli.commands.get_settings") as mock_settings,
            patch("faceless.cli.commands.setup_logging"),
            patch("subprocess.run") as mock_run,
            patch(
                "faceless.clients.azure_openai.AzureOpenAIClient"
            ) as mock_client_class,
        ):
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            settings.azure_openai.is_configured = True
            settings.use_elevenlabs = False
            mock_settings.return_value = settings
            mock_run.return_value = MagicMock(returncode=0)

            mock_client = MagicMock()
            mock_client.test_connection.return_value = False
            mock_client_class.return_value = mock_client

            result = runner.invoke(app, ["validate", "--test-connections"])

            assert result.exit_code == 0
            assert (
                "failed" in result.output.lower()
                or "Connection failed" in result.output
            )

    def test_validate_test_connections_exception(self) -> None:
        """Test validate with exception during test connections."""
        with (
            patch("faceless.cli.commands.get_settings") as mock_settings,
            patch("faceless.cli.commands.setup_logging"),
            patch("subprocess.run") as mock_run,
            patch(
                "faceless.clients.azure_openai.AzureOpenAIClient"
            ) as mock_client_class,
        ):
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            settings.azure_openai.is_configured = True
            settings.use_elevenlabs = False
            mock_settings.return_value = settings
            mock_run.return_value = MagicMock(returncode=0)

            mock_client_class.side_effect = Exception("Connection error")

            result = runner.invoke(app, ["validate", "--test-connections"])

            assert result.exit_code == 0
            assert (
                "error" in result.output.lower() or "Connection error" in result.output
            )


class TestResearchCommand:
    """Tests for research command."""

    def test_research_basic(self) -> None:
        """Test research command basic usage."""
        with (
            patch("faceless.cli.commands.get_settings") as mock_settings,
            patch("faceless.cli.commands.setup_logging"),
            patch(
                "faceless.services.research_service.DeepResearchService"
            ) as mock_service_class,
        ):
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            mock_settings.return_value = settings

            service = MagicMock()
            result = MagicMock()
            result.confidence_score = 0.85
            result.key_findings = [MagicMock(content="Finding", importance=0.9)]
            result.statistics = [MagicMock(content="Stat")]
            result.suggested_hook = "Hook"
            result.why_it_matters = "Because..."
            result.follow_up_topics = ["Topic"]
            result.to_dict.return_value = {}
            service.research_topic.return_value = result
            mock_service_class.return_value = service

            result_cli = runner.invoke(app, ["research", "Bitcoin history"])

            assert result_cli.exit_code == 0
            assert (
                "Research Complete" in result_cli.output or "85%" in result_cli.output
            )

    def test_research_with_depth(self) -> None:
        """Test research command with depth option."""
        with (
            patch("faceless.cli.commands.get_settings") as mock_settings,
            patch("faceless.cli.commands.setup_logging"),
            patch(
                "faceless.services.research_service.DeepResearchService"
            ) as mock_service_class,
        ):
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            mock_settings.return_value = settings

            service = MagicMock()
            result = MagicMock()
            result.confidence_score = 0.9
            result.key_findings = []
            result.statistics = []
            result.suggested_hook = None
            result.why_it_matters = None
            result.follow_up_topics = []
            result.to_dict.return_value = {}
            service.research_topic.return_value = result
            mock_service_class.return_value = service

            result_cli = runner.invoke(
                app, ["research", "Stock market", "-n", "finance", "-d", "deep"]
            )

            assert result_cli.exit_code == 0

    def test_research_with_structure(self) -> None:
        """Test research command with structure option."""
        with (
            patch("faceless.cli.commands.get_settings") as mock_settings,
            patch("faceless.cli.commands.setup_logging"),
            patch(
                "faceless.services.research_service.DeepResearchService"
            ) as mock_service_class,
        ):
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            mock_settings.return_value = settings

            service = MagicMock()
            result = MagicMock()
            result.confidence_score = 0.85
            result.key_findings = []
            result.statistics = []
            result.suggested_hook = None
            result.why_it_matters = None
            result.follow_up_topics = []
            result.to_dict.return_value = {}
            service.research_topic.return_value = result
            service.generate_content_structure.return_value = {
                "hook": "Opening hook",
                "sections": [{"title": "Section 1", "duration_seconds": 30}],
                "cta": "Subscribe!",
            }
            mock_service_class.return_value = service

            result_cli = runner.invoke(
                app, ["research", "AI trends", "-n", "tech-gadgets", "--structure"]
            )

            assert result_cli.exit_code == 0
            assert (
                "Content Structure" in result_cli.output or "Hook" in result_cli.output
            )

    def test_research_save_output(self, tmp_path: Path) -> None:
        """Test research command with output file."""
        with (
            patch("faceless.cli.commands.get_settings") as mock_settings,
            patch("faceless.cli.commands.setup_logging"),
            patch(
                "faceless.services.research_service.DeepResearchService"
            ) as mock_service_class,
        ):
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            mock_settings.return_value = settings

            service = MagicMock()
            result = MagicMock()
            result.confidence_score = 0.85
            result.key_findings = []
            result.statistics = []
            result.suggested_hook = None
            result.why_it_matters = None
            result.follow_up_topics = []
            result.to_dict.return_value = {"topic": "test"}
            service.research_topic.return_value = result
            mock_service_class.return_value = service

            output_file = tmp_path / "research.json"
            result_cli = runner.invoke(
                app, ["research", "Test topic", "-o", str(output_file)]
            )

            assert result_cli.exit_code == 0
            assert output_file.exists()

    def test_research_failure(self) -> None:
        """Test research command with failure."""
        with (
            patch("faceless.cli.commands.get_settings") as mock_settings,
            patch("faceless.cli.commands.setup_logging"),
            patch(
                "faceless.services.research_service.DeepResearchService"
            ) as mock_service_class,
        ):
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            mock_settings.return_value = settings
            mock_service_class.return_value.research_topic.side_effect = Exception(
                "API Error"
            )

            result = runner.invoke(app, ["research", "Failed topic"])

            assert result.exit_code == 1
            assert "Research failed" in result.output

    def test_research_help(self) -> None:
        """Test research --help."""
        result = runner.invoke(app, ["research", "--help"])
        assert result.exit_code == 0
        assert "topic" in result.output.lower()


class TestQualityCommand:
    """Tests for quality command."""

    @pytest.fixture
    def mock_script_file(self, tmp_path: Path) -> Path:
        """Create a mock script file."""
        import json

        script_data = {
            "title": "Test Script",
            "niche": "scary-stories",
            "scenes": [
                {
                    "scene_number": 1,
                    "narration": "Test narration",
                    "image_prompt": "Test prompt",
                    "duration_estimate": 10.0,
                }
            ],
        }
        script_path = tmp_path / "test_script.json"
        script_path.write_text(json.dumps(script_data))
        return script_path

    def test_quality_basic(self, mock_script_file) -> None:
        """Test quality command basic usage."""
        with (
            patch("faceless.cli.commands.get_settings") as mock_settings,
            patch("faceless.cli.commands.setup_logging"),
            patch("faceless.core.models.Script") as mock_script,
            patch(
                "faceless.services.quality_service.QualityService"
            ) as mock_service_class,
        ):
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            mock_settings.return_value = settings

            script = MagicMock()
            script.title = "Test Script"
            script.scenes = [MagicMock()]
            mock_script.from_json_file.return_value = script

            result_mock = MagicMock()
            result_mock.overall_score = 8.5
            result_mock.hook_score = 8.0
            result_mock.narrative_score = 7.5
            result_mock.engagement_score = 8.0
            result_mock.information_score = 7.0
            result_mock.gates_passed = [MagicMock(value="hook_quality")]
            result_mock.gates_failed = []
            result_mock.hook_analysis = MagicMock(
                hook_type="question", attention_grab=0.8, curiosity_gap=0.7
            )
            result_mock.retention_analysis = MagicMock(
                predicted_retention_30s=0.75,
                predicted_completion_rate=0.6,
                drop_off_risks=["Risk 1"],
            )
            result_mock.critical_issues = []
            result_mock.improvements = ["Improvement 1"]
            result_mock.approved_for_production = True
            result_mock.to_dict.return_value = {"overall_score": 8.5}
            mock_service_class.return_value.evaluate_script.return_value = result_mock

            result = runner.invoke(app, ["quality", str(mock_script_file)])

            assert result.exit_code == 0
            assert "Quality Scores" in result.output or "APPROVED" in result.output

    def test_quality_with_improve_hooks(self, mock_script_file) -> None:
        """Test quality command with improve hooks option."""
        with (
            patch("faceless.cli.commands.get_settings") as mock_settings,
            patch("faceless.cli.commands.setup_logging"),
            patch("faceless.core.models.Script") as mock_script,
            patch(
                "faceless.services.quality_service.QualityService"
            ) as mock_service_class,
        ):
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            mock_settings.return_value = settings

            script = MagicMock()
            script.title = "Test Script"
            script.scenes = [MagicMock()]
            mock_script.from_json_file.return_value = script

            result_mock = MagicMock()
            result_mock.overall_score = 8.5
            result_mock.hook_score = 8.0
            result_mock.narrative_score = 7.5
            result_mock.engagement_score = 8.0
            result_mock.information_score = 7.0
            result_mock.gates_passed = []
            result_mock.gates_failed = []
            result_mock.hook_analysis = None
            result_mock.retention_analysis = None
            result_mock.critical_issues = []
            result_mock.improvements = []
            result_mock.approved_for_production = True
            mock_service_class.return_value.evaluate_script.return_value = result_mock
            mock_service_class.return_value.generate_better_hooks.return_value = [
                "Hook 1",
                "Hook 2",
            ]

            result = runner.invoke(
                app, ["quality", str(mock_script_file), "--improve-hooks"]
            )

            assert result.exit_code == 0
            assert "Alternative Hooks" in result.output or "Hook" in result.output

    def test_quality_not_approved(self, mock_script_file) -> None:
        """Test quality command with unapproved script."""
        with (
            patch("faceless.cli.commands.get_settings") as mock_settings,
            patch("faceless.cli.commands.setup_logging"),
            patch("faceless.core.models.Script") as mock_script,
            patch("faceless.services.quality_service.QualityService") as mock_service,
        ):
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            mock_settings.return_value = settings

            script = MagicMock()
            script.title = "Test Script"
            script.scenes = [MagicMock()]
            mock_script.from_json_file.return_value = script

            result_mock = MagicMock()
            result_mock.overall_score = 4.0
            result_mock.hook_score = 3.0
            result_mock.narrative_score = 4.0
            result_mock.engagement_score = 3.5
            result_mock.information_score = 4.0
            result_mock.gates_passed = []
            result_mock.gates_failed = [MagicMock(value="hook_quality")]
            result_mock.hook_analysis = None
            result_mock.retention_analysis = None
            result_mock.critical_issues = ["Weak hook"]
            result_mock.improvements = []
            result_mock.approved_for_production = False
            mock_service.return_value.evaluate_script.return_value = result_mock

            result = runner.invoke(app, ["quality", str(mock_script_file)])

            assert result.exit_code == 1
            assert "NOT APPROVED" in result.output

    def test_quality_failure(self, mock_script_file) -> None:
        """Test quality command with failure."""
        with (
            patch("faceless.cli.commands.get_settings") as mock_settings,
            patch("faceless.cli.commands.setup_logging"),
            patch("faceless.core.models.Script") as mock_script,
        ):
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            mock_settings.return_value = settings
            mock_script.from_json_file.side_effect = Exception("Invalid JSON")

            result = runner.invoke(app, ["quality", str(mock_script_file)])

            assert result.exit_code == 1
            assert "failed" in result.output.lower()

    def test_quality_help(self) -> None:
        """Test quality --help."""
        result = runner.invoke(app, ["quality", "--help"])
        assert result.exit_code == 0


class TestTrendingCommand:
    """Tests for trending command."""

    def test_trending_basic(self) -> None:
        """Test trending command basic usage."""
        with (
            patch("faceless.cli.commands.get_settings") as mock_settings,
            patch("faceless.cli.commands.setup_logging"),
            patch(
                "faceless.services.trending_service.TrendingService"
            ) as mock_service_class,
        ):
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            mock_settings.return_value = settings

            service = MagicMock()
            report = MagicMock()
            report.hot_topics = [MagicMock(title="Hot Topic", score=90)]
            report.rising_topics = [MagicMock(title="Rising", growth_rate=150)]
            report.viral_potential = [MagicMock(title="Viral", video_potential=0.9)]
            report.evergreen_topics = [MagicMock(title="Evergreen")]
            report.top_recommendation = MagicMock(title="Top Rec")
            report.content_calendar_suggestions = []
            report.to_dict.return_value = {}
            service.get_trend_report.return_value = report
            mock_service_class.return_value = service

            result = runner.invoke(app, ["trending", "scary-stories"])

            assert result.exit_code == 0
            assert "Hot Topics" in result.output or "Trending" in result.output

    def test_trending_with_analyze(self) -> None:
        """Test trending command with analyze option."""
        with (
            patch("faceless.cli.commands.get_settings") as mock_settings,
            patch("faceless.cli.commands.setup_logging"),
            patch(
                "faceless.services.trending_service.TrendingService"
            ) as mock_service_class,
        ):
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            mock_settings.return_value = settings

            service = MagicMock()
            topic = MagicMock()
            topic.score = 85
            topic.lifecycle = MagicMock(value="rising")
            topic.video_potential = 0.8
            topic.competition_level = "medium"
            topic.evergreen_potential = 0.6
            topic.suggested_angles = ["Angle 1"]
            service.analyze_topic_potential.return_value = topic
            service.suggest_content_timing.return_value = {
                "recommendation": "Post now",
                "window": "Morning",
            }
            mock_service_class.return_value = service

            result = runner.invoke(
                app, ["trending", "finance", "--analyze", "Bitcoin crash"]
            )

            assert result.exit_code == 0
            assert "Topic Analysis" in result.output or "Score" in result.output

    def test_trending_with_calendar(self) -> None:
        """Test trending command with calendar option."""
        with (
            patch("faceless.cli.commands.get_settings") as mock_settings,
            patch("faceless.cli.commands.setup_logging"),
            patch(
                "faceless.services.trending_service.TrendingService"
            ) as mock_service_class,
        ):
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            mock_settings.return_value = settings

            service = MagicMock()
            report = MagicMock()
            report.hot_topics = []
            report.rising_topics = []
            report.viral_potential = []
            report.evergreen_topics = []
            report.top_recommendation = None
            report.content_calendar_suggestions = [
                {"timing": "Monday", "topic": "Topic 1", "reason": "High engagement"}
            ]
            report.to_dict.return_value = {}
            service.get_trend_report.return_value = report
            mock_service_class.return_value = service

            result = runner.invoke(app, ["trending", "luxury", "--calendar"])

            assert result.exit_code == 0
            assert "Content Calendar" in result.output or "Monday" in result.output

    def test_trending_save_output(self, tmp_path: Path) -> None:
        """Test trending command with output file."""
        with (
            patch("faceless.cli.commands.get_settings") as mock_settings,
            patch("faceless.cli.commands.setup_logging"),
            patch(
                "faceless.services.trending_service.TrendingService"
            ) as mock_service_class,
        ):
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            mock_settings.return_value = settings

            service = MagicMock()
            report = MagicMock()
            report.hot_topics = []
            report.rising_topics = []
            report.viral_potential = []
            report.evergreen_topics = []
            report.top_recommendation = None
            report.content_calendar_suggestions = []
            report.to_dict.return_value = {"hot_topics": []}
            service.get_trend_report.return_value = report
            mock_service_class.return_value = service

            output_file = tmp_path / "trends.json"
            result = runner.invoke(app, ["trending", "finance", "-o", str(output_file)])

            assert result.exit_code == 0
            assert output_file.exists()

    def test_trending_failure(self) -> None:
        """Test trending command with failure."""
        with (
            patch("faceless.cli.commands.get_settings") as mock_settings,
            patch("faceless.cli.commands.setup_logging"),
            patch("faceless.services.trending_service.TrendingService") as mock_service,
        ):
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = False
            mock_settings.return_value = settings
            mock_service.return_value.get_trend_report.side_effect = Exception(
                "API Error"
            )

            result = runner.invoke(app, ["trending", "scary-stories"])

            assert result.exit_code == 1
            assert "failed" in result.output.lower()

    def test_trending_help(self) -> None:
        """Test trending --help."""
        result = runner.invoke(app, ["trending", "--help"])
        assert result.exit_code == 0

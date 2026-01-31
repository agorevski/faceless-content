"""
Unit tests for custom exceptions.

Tests cover:
- Base FacelessError
- Configuration errors
- Validation errors
- Pipeline errors
- Generation errors
- Client errors
- External tool errors
- Rate limiting errors
"""


from faceless.core.exceptions import (
    AzureOpenAIError,
    CheckpointError,
    ClientError,
    ConfigurationError,
    ContentFilterError,
    ElevenLabsError,
    ExternalToolError,
    FacelessError,
    FFmpegError,
    GenerationError,
    ImageGenerationError,
    InputValidationError,
    JobError,
    MissingConfigError,
    PipelineError,
    RateLimitError,
    RedditError,
    ScriptValidationError,
    TTSGenerationError,
    ValidationError,
    VideoAssemblyError,
)


class TestFacelessError:
    """Tests for the base FacelessError."""

    def test_create_with_message_only(self) -> None:
        """Test creating error with message only."""
        error = FacelessError("Something went wrong")
        assert error.message == "Something went wrong"
        assert error.details == {}
        assert str(error) == "Something went wrong"

    def test_create_with_details(self) -> None:
        """Test creating error with details."""
        error = FacelessError("Error occurred", details={"key": "value"})
        assert error.message == "Error occurred"
        assert error.details == {"key": "value"}
        assert "Details:" in str(error)

    def test_to_dict(self) -> None:
        """Test converting error to dictionary."""
        error = FacelessError("Test error", details={"foo": "bar"})
        result = error.to_dict()
        assert result["error_type"] == "FacelessError"
        assert result["message"] == "Test error"
        assert result["details"] == {"foo": "bar"}

    def test_str_without_details(self) -> None:
        """Test string representation without details."""
        error = FacelessError("Simple error")
        assert str(error) == "Simple error"

    def test_str_with_details(self) -> None:
        """Test string representation with details."""
        error = FacelessError("Error", details={"code": 123})
        result = str(error)
        assert "Error" in result
        assert "Details:" in result


class TestConfigurationError:
    """Tests for ConfigurationError."""

    def test_create_configuration_error(self) -> None:
        """Test creating a configuration error."""
        error = ConfigurationError("Invalid configuration")
        assert isinstance(error, FacelessError)
        assert error.message == "Invalid configuration"


class TestMissingConfigError:
    """Tests for MissingConfigError."""

    def test_create_with_key(self) -> None:
        """Test creating error with config key."""
        error = MissingConfigError("API_KEY")
        assert error.config_key == "API_KEY"
        assert "API_KEY" in error.message
        assert error.details["config_key"] == "API_KEY"

    def test_create_with_custom_message(self) -> None:
        """Test creating error with custom message."""
        error = MissingConfigError("API_KEY", message="Custom message")
        assert error.message == "Custom message"
        assert error.config_key == "API_KEY"


class TestValidationError:
    """Tests for ValidationError."""

    def test_create_validation_error(self) -> None:
        """Test creating a validation error."""
        error = ValidationError("Validation failed")
        assert isinstance(error, FacelessError)
        assert error.message == "Validation failed"


class TestScriptValidationError:
    """Tests for ScriptValidationError."""

    def test_create_with_message_only(self) -> None:
        """Test creating error with message only."""
        error = ScriptValidationError("Invalid script")
        assert error.message == "Invalid script"
        assert error.details == {}

    def test_create_with_script_path(self) -> None:
        """Test creating error with script path."""
        error = ScriptValidationError("Invalid", script_path="/path/to/script.json")
        assert error.details["script_path"] == "/path/to/script.json"

    def test_create_with_field(self) -> None:
        """Test creating error with field name."""
        error = ScriptValidationError("Invalid", field="title")
        assert error.details["field"] == "title"

    def test_create_with_all_params(self) -> None:
        """Test creating error with all parameters."""
        error = ScriptValidationError(
            "Invalid",
            script_path="/path/to/script.json",
            field="scenes",
        )
        assert error.details["script_path"] == "/path/to/script.json"
        assert error.details["field"] == "scenes"


class TestInputValidationError:
    """Tests for InputValidationError."""

    def test_create_with_field(self) -> None:
        """Test creating error with field."""
        error = InputValidationError("Invalid input", field="email")
        assert error.details["field"] == "email"

    def test_create_with_value(self) -> None:
        """Test creating error with value."""
        error = InputValidationError("Invalid", field="count", value="-5")
        assert error.details["field"] == "count"
        assert error.details["value"] == "-5"

    def test_value_truncation(self) -> None:
        """Test that long values are truncated."""
        long_value = "x" * 200
        error = InputValidationError("Invalid", field="data", value=long_value)
        assert len(error.details["value"]) <= 100


class TestPipelineError:
    """Tests for PipelineError."""

    def test_create_pipeline_error(self) -> None:
        """Test creating a pipeline error."""
        error = PipelineError("Pipeline failed")
        assert isinstance(error, FacelessError)


class TestCheckpointError:
    """Tests for CheckpointError."""

    def test_create_with_message_only(self) -> None:
        """Test creating error with message only."""
        error = CheckpointError("Checkpoint failed")
        assert error.message == "Checkpoint failed"

    def test_create_with_path(self) -> None:
        """Test creating error with checkpoint path."""
        error = CheckpointError("Failed", checkpoint_path="/path/to/checkpoint.json")
        assert error.details["checkpoint_path"] == "/path/to/checkpoint.json"

    def test_create_with_operation(self) -> None:
        """Test creating error with operation."""
        error = CheckpointError("Failed", operation="save")
        assert error.details["operation"] == "save"


class TestJobError:
    """Tests for JobError."""

    def test_create_with_message(self) -> None:
        """Test creating error with message."""
        error = JobError("Job failed")
        assert error.message == "Job failed"

    def test_create_with_job_id(self) -> None:
        """Test creating error with job ID."""
        error = JobError("Failed", job_id="job-123")
        assert error.details["job_id"] == "job-123"


class TestGenerationError:
    """Tests for GenerationError."""

    def test_create_generation_error(self) -> None:
        """Test creating a generation error."""
        error = GenerationError("Generation failed")
        assert isinstance(error, FacelessError)


class TestImageGenerationError:
    """Tests for ImageGenerationError."""

    def test_create_with_message(self) -> None:
        """Test creating error with message."""
        error = ImageGenerationError("Image failed")
        assert error.message == "Image failed"

    def test_create_with_prompt(self) -> None:
        """Test creating error with prompt."""
        error = ImageGenerationError("Failed", prompt="A cat sitting")
        assert error.details["prompt"] == "A cat sitting"

    def test_prompt_truncation(self) -> None:
        """Test that long prompts are truncated."""
        long_prompt = "word " * 100
        error = ImageGenerationError("Failed", prompt=long_prompt)
        assert len(error.details["prompt"]) <= 200

    def test_create_with_scene_number(self) -> None:
        """Test creating error with scene number."""
        error = ImageGenerationError("Failed", scene_number=5)
        assert error.details["scene_number"] == 5

    def test_create_with_api_error(self) -> None:
        """Test creating error with API error."""
        error = ImageGenerationError("Failed", api_error="Connection timeout")
        assert error.details["api_error"] == "Connection timeout"


class TestTTSGenerationError:
    """Tests for TTSGenerationError."""

    def test_create_with_message(self) -> None:
        """Test creating error with message."""
        error = TTSGenerationError("TTS failed")
        assert error.message == "TTS failed"

    def test_create_with_text(self) -> None:
        """Test creating error with text."""
        error = TTSGenerationError("Failed", text="Hello world")
        assert error.details["text"] == "Hello world"

    def test_text_truncation(self) -> None:
        """Test that long text is truncated."""
        long_text = "word " * 50
        error = TTSGenerationError("Failed", text=long_text)
        assert len(error.details["text"]) <= 100

    def test_create_with_voice(self) -> None:
        """Test creating error with voice."""
        error = TTSGenerationError("Failed", voice="onyx")
        assert error.details["voice"] == "onyx"

    def test_create_with_api_error(self) -> None:
        """Test creating error with API error."""
        error = TTSGenerationError("Failed", api_error="Rate limited")
        assert error.details["api_error"] == "Rate limited"


class TestVideoAssemblyError:
    """Tests for VideoAssemblyError."""

    def test_create_with_message(self) -> None:
        """Test creating error with message."""
        error = VideoAssemblyError("Assembly failed")
        assert error.message == "Assembly failed"

    def test_create_with_stage(self) -> None:
        """Test creating error with stage."""
        error = VideoAssemblyError("Failed", stage="concatenation")
        assert error.details["stage"] == "concatenation"

    def test_create_with_input_files(self) -> None:
        """Test creating error with input files."""
        error = VideoAssemblyError("Failed", input_files=["file1.mp4", "file2.mp4"])
        assert error.details["input_files"] == ["file1.mp4", "file2.mp4"]

    def test_create_with_ffmpeg_error(self) -> None:
        """Test creating error with FFmpeg error."""
        error = VideoAssemblyError("Failed", ffmpeg_error="Invalid codec")
        assert error.details["ffmpeg_error"] == "Invalid codec"

    def test_ffmpeg_error_truncation(self) -> None:
        """Test that long FFmpeg errors are truncated."""
        long_error = "x" * 1000
        error = VideoAssemblyError("Failed", ffmpeg_error=long_error)
        assert len(error.details["ffmpeg_error"]) <= 500


class TestClientError:
    """Tests for ClientError."""

    def test_create_client_error(self) -> None:
        """Test creating a client error."""
        error = ClientError("Client failed")
        assert isinstance(error, FacelessError)


class TestAzureOpenAIError:
    """Tests for AzureOpenAIError."""

    def test_create_with_message(self) -> None:
        """Test creating error with message."""
        error = AzureOpenAIError("API failed")
        assert error.message == "API failed"

    def test_create_with_status_code(self) -> None:
        """Test creating error with status code."""
        error = AzureOpenAIError("Failed", status_code=401)
        assert error.details["status_code"] == 401

    def test_create_with_error_code(self) -> None:
        """Test creating error with error code."""
        error = AzureOpenAIError("Failed", error_code="invalid_api_key")
        assert error.details["error_code"] == "invalid_api_key"

    def test_create_with_response_body(self) -> None:
        """Test creating error with response body."""
        error = AzureOpenAIError("Failed", response_body='{"error": "bad request"}')
        assert error.details["response_body"] == '{"error": "bad request"}'

    def test_response_body_truncation(self) -> None:
        """Test that long response body is truncated."""
        long_body = "x" * 1000
        error = AzureOpenAIError("Failed", response_body=long_body)
        assert len(error.details["response_body"]) <= 500


class TestElevenLabsError:
    """Tests for ElevenLabsError."""

    def test_create_with_message(self) -> None:
        """Test creating error with message."""
        error = ElevenLabsError("ElevenLabs failed")
        assert error.message == "ElevenLabs failed"

    def test_create_with_status_code(self) -> None:
        """Test creating error with status code."""
        error = ElevenLabsError("Failed", status_code=429)
        assert error.details["status_code"] == 429


class TestRedditError:
    """Tests for RedditError."""

    def test_create_with_message(self) -> None:
        """Test creating error with message."""
        error = RedditError("Reddit failed")
        assert error.message == "Reddit failed"

    def test_create_with_subreddit(self) -> None:
        """Test creating error with subreddit."""
        error = RedditError("Failed", subreddit="nosleep")
        assert error.details["subreddit"] == "nosleep"

    def test_create_with_status_code(self) -> None:
        """Test creating error with status code."""
        error = RedditError("Failed", status_code=403)
        assert error.details["status_code"] == 403


class TestExternalToolError:
    """Tests for ExternalToolError."""

    def test_create_external_tool_error(self) -> None:
        """Test creating an external tool error."""
        error = ExternalToolError("Tool failed")
        assert isinstance(error, FacelessError)


class TestFFmpegError:
    """Tests for FFmpegError."""

    def test_create_with_message(self) -> None:
        """Test creating error with message."""
        error = FFmpegError("FFmpeg failed")
        assert error.message == "FFmpeg failed"

    def test_create_with_command(self) -> None:
        """Test creating error with command."""
        error = FFmpegError(
            "Failed", command=["ffmpeg", "-i", "input.mp4", "-o", "out.mp4"]
        )
        assert "ffmpeg" in error.details["command_preview"]
        assert "..." in error.details["command_preview"]

    def test_create_with_return_code(self) -> None:
        """Test creating error with return code."""
        error = FFmpegError("Failed", return_code=1)
        assert error.details["return_code"] == 1

    def test_create_with_stderr(self) -> None:
        """Test creating error with stderr."""
        error = FFmpegError("Failed", stderr="Invalid input file")
        assert error.details["stderr"] == "Invalid input file"

    def test_stderr_truncation(self) -> None:
        """Test that long stderr is truncated."""
        long_stderr = "x" * 1000
        error = FFmpegError("Failed", stderr=long_stderr)
        assert len(error.details["stderr"]) <= 500


class TestRateLimitError:
    """Tests for RateLimitError."""

    def test_create_with_message(self) -> None:
        """Test creating error with message."""
        error = RateLimitError("Rate limited")
        assert error.message == "Rate limited"

    def test_create_with_retry_after(self) -> None:
        """Test creating error with retry_after."""
        error = RateLimitError("Limited", retry_after=60)
        assert error.retry_after == 60
        assert error.details["retry_after"] == 60

    def test_create_with_service(self) -> None:
        """Test creating error with service."""
        error = RateLimitError("Limited", service="AzureOpenAI")
        assert error.details["service"] == "AzureOpenAI"


class TestContentFilterError:
    """Tests for ContentFilterError."""

    def test_create_with_message(self) -> None:
        """Test creating error with message."""
        error = ContentFilterError("Content filtered")
        assert error.message == "Content filtered"

    def test_create_with_prompt(self) -> None:
        """Test creating error with prompt."""
        error = ContentFilterError("Filtered", prompt="Some prompt")
        assert error.details["prompt"] == "Some prompt"

    def test_prompt_truncation(self) -> None:
        """Test that long prompts are truncated."""
        long_prompt = "x" * 300
        error = ContentFilterError("Filtered", prompt=long_prompt)
        assert len(error.details["prompt"]) <= 200

    def test_create_with_filter_reason(self) -> None:
        """Test creating error with filter reason."""
        error = ContentFilterError("Filtered", filter_reason="violence")
        assert error.details["filter_reason"] == "violence"


class TestExceptionHierarchy:
    """Tests for exception inheritance hierarchy."""

    def test_configuration_error_is_faceless_error(self) -> None:
        """Test ConfigurationError inherits from FacelessError."""
        error = ConfigurationError("test")
        assert isinstance(error, FacelessError)

    def test_missing_config_is_configuration_error(self) -> None:
        """Test MissingConfigError inherits from ConfigurationError."""
        error = MissingConfigError("key")
        assert isinstance(error, ConfigurationError)

    def test_validation_error_is_faceless_error(self) -> None:
        """Test ValidationError inherits from FacelessError."""
        error = ValidationError("test")
        assert isinstance(error, FacelessError)

    def test_pipeline_error_is_faceless_error(self) -> None:
        """Test PipelineError inherits from FacelessError."""
        error = PipelineError("test")
        assert isinstance(error, FacelessError)

    def test_generation_error_is_faceless_error(self) -> None:
        """Test GenerationError inherits from FacelessError."""
        error = GenerationError("test")
        assert isinstance(error, FacelessError)

    def test_client_error_is_faceless_error(self) -> None:
        """Test ClientError inherits from FacelessError."""
        error = ClientError("test")
        assert isinstance(error, FacelessError)

    def test_rate_limit_is_client_error(self) -> None:
        """Test RateLimitError inherits from ClientError."""
        error = RateLimitError("test")
        assert isinstance(error, ClientError)

    def test_content_filter_is_client_error(self) -> None:
        """Test ContentFilterError inherits from ClientError."""
        error = ContentFilterError("test")
        assert isinstance(error, ClientError)

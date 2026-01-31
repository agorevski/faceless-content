"""
Custom exception hierarchy for the Faceless Content Pipeline.

This module defines a structured exception hierarchy that allows for
precise error handling and meaningful error messages throughout the application.

Exception Hierarchy:
    FacelessError (base)
    ├── ConfigurationError
    │   └── MissingConfigError
    ├── ValidationError
    │   ├── ScriptValidationError
    │   └── InputValidationError
    ├── PipelineError
    │   ├── CheckpointError
    │   └── JobError
    ├── GenerationError
    │   ├── ImageGenerationError
    │   ├── TTSGenerationError
    │   └── VideoAssemblyError
    ├── ClientError
    │   ├── AzureOpenAIError
    │   ├── ElevenLabsError
    │   └── RedditError
    └── ExternalToolError
        └── FFmpegError
"""

from typing import Any


class FacelessError(Exception):
    """
    Base exception for all Faceless Content Pipeline errors.

    All custom exceptions in the pipeline inherit from this class,
    allowing for catch-all error handling when needed.

    Attributes:
        message: Human-readable error description.
        details: Optional dictionary with additional error context.
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to a dictionary for logging/serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


# =============================================================================
# Configuration Errors
# =============================================================================


class ConfigurationError(FacelessError):
    """
    Raised when there's an issue with application configuration.

    This includes missing environment variables, invalid settings,
    or configuration file issues.
    """

    pass


class MissingConfigError(ConfigurationError):
    """
    Raised when a required configuration value is missing.

    Attributes:
        config_key: The name of the missing configuration key.
    """

    def __init__(self, config_key: str, message: str | None = None) -> None:
        self.config_key = config_key
        msg = message or f"Missing required configuration: {config_key}"
        super().__init__(msg, details={"config_key": config_key})


# =============================================================================
# Validation Errors
# =============================================================================


class ValidationError(FacelessError):
    """
    Raised when input validation fails.

    This is used for validating user input, API responses,
    and internal data structures.
    """

    pass


class ScriptValidationError(ValidationError):
    """
    Raised when a script fails validation.

    This includes missing required fields, invalid scene structures,
    or content that doesn't meet requirements.
    """

    def __init__(
        self,
        message: str,
        script_path: str | None = None,
        field: str | None = None,
    ) -> None:
        details = {}
        if script_path:
            details["script_path"] = script_path
        if field:
            details["field"] = field
        super().__init__(message, details=details)


class InputValidationError(ValidationError):
    """
    Raised when user input fails validation.

    Attributes:
        field: The name of the field that failed validation.
        value: The invalid value (sanitized if sensitive).
    """

    def __init__(
        self,
        message: str,
        field: str,
        value: Any = None,
    ) -> None:
        details = {"field": field}
        if value is not None:
            details["value"] = str(value)[:100]  # Truncate for safety
        super().__init__(message, details=details)


# =============================================================================
# Pipeline Errors
# =============================================================================


class PipelineError(FacelessError):
    """
    Raised when there's an error in the pipeline orchestration.

    This includes job management issues, state transitions,
    and workflow coordination problems.
    """

    pass


class CheckpointError(PipelineError):
    """
    Raised when there's an issue with checkpointing.

    This includes failures to save, load, or resume from checkpoints.
    """

    def __init__(
        self,
        message: str,
        checkpoint_path: str | None = None,
        operation: str | None = None,
    ) -> None:
        details = {}
        if checkpoint_path:
            details["checkpoint_path"] = checkpoint_path
        if operation:
            details["operation"] = operation
        super().__init__(message, details=details)


class JobError(PipelineError):
    """
    Raised when there's an issue with a specific job.

    Attributes:
        job_id: The ID of the affected job.
    """

    def __init__(
        self,
        message: str,
        job_id: str | None = None,
    ) -> None:
        details = {}
        if job_id:
            details["job_id"] = job_id
        super().__init__(message, details=details)


# =============================================================================
# Generation Errors
# =============================================================================


class GenerationError(FacelessError):
    """
    Base class for content generation errors.

    This includes failures in image generation, TTS, and video assembly.
    """

    pass


class ImageGenerationError(GenerationError):
    """
    Raised when image generation fails.

    Attributes:
        prompt: The prompt that failed (truncated for logging).
        scene_number: The scene number if applicable.
    """

    def __init__(
        self,
        message: str,
        prompt: str | None = None,
        scene_number: int | None = None,
        api_error: str | None = None,
    ) -> None:
        details: dict[str, Any] = {}
        if prompt:
            details["prompt"] = prompt[:200]  # Truncate long prompts
        if scene_number is not None:
            details["scene_number"] = scene_number
        if api_error:
            details["api_error"] = api_error
        super().__init__(message, details=details)


class TTSGenerationError(GenerationError):
    """
    Raised when text-to-speech generation fails.

    Attributes:
        text: The text that failed to generate (truncated).
        voice: The voice that was being used.
    """

    def __init__(
        self,
        message: str,
        text: str | None = None,
        voice: str | None = None,
        api_error: str | None = None,
    ) -> None:
        details = {}
        if text:
            details["text"] = text[:100]
        if voice:
            details["voice"] = voice
        if api_error:
            details["api_error"] = api_error
        super().__init__(message, details=details)


class VideoAssemblyError(GenerationError):
    """
    Raised when video assembly fails.

    Attributes:
        stage: The assembly stage that failed.
        input_files: The input files involved.
    """

    def __init__(
        self,
        message: str,
        stage: str | None = None,
        input_files: list[str] | None = None,
        ffmpeg_error: str | None = None,
    ) -> None:
        details: dict[str, Any] = {}
        if stage:
            details["stage"] = stage
        if input_files:
            details["input_files"] = input_files
        if ffmpeg_error:
            details["ffmpeg_error"] = ffmpeg_error[:500]  # Truncate long errors
        super().__init__(message, details=details)


# =============================================================================
# Client Errors
# =============================================================================


class ClientError(FacelessError):
    """
    Base class for external API client errors.

    This includes errors from Azure OpenAI, ElevenLabs, and Reddit APIs.
    """

    pass


class AzureOpenAIError(ClientError):
    """
    Raised when Azure OpenAI API returns an error.

    Attributes:
        status_code: HTTP status code from the API.
        error_code: Azure-specific error code if available.
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        error_code: str | None = None,
        response_body: str | None = None,
    ) -> None:
        details: dict[str, Any] = {}
        if status_code:
            details["status_code"] = status_code
        if error_code:
            details["error_code"] = error_code
        if response_body:
            details["response_body"] = response_body[:500]
        super().__init__(message, details=details)


class ElevenLabsError(ClientError):
    """Raised when ElevenLabs API returns an error."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
    ) -> None:
        details = {}
        if status_code:
            details["status_code"] = status_code
        super().__init__(message, details=details)


class RedditError(ClientError):
    """Raised when Reddit API or scraping fails."""

    def __init__(
        self,
        message: str,
        subreddit: str | None = None,
        status_code: int | None = None,
    ) -> None:
        details: dict[str, Any] = {}
        if subreddit:
            details["subreddit"] = subreddit
        if status_code:
            details["status_code"] = status_code
        super().__init__(message, details=details)


# =============================================================================
# External Tool Errors
# =============================================================================


class ExternalToolError(FacelessError):
    """
    Base class for external tool errors.

    This includes errors from FFmpeg and other command-line tools.
    """

    pass


class FFmpegError(ExternalToolError):
    """
    Raised when FFmpeg command fails.

    Attributes:
        command: The FFmpeg command that failed.
        return_code: The process return code.
        stderr: Standard error output.
    """

    def __init__(
        self,
        message: str,
        command: list[str] | None = None,
        return_code: int | None = None,
        stderr: str | None = None,
    ) -> None:
        details: dict[str, Any] = {}
        if command:
            # Don't include full command in details (could be very long)
            details["command_preview"] = " ".join(command[:5]) + "..."
        if return_code is not None:
            details["return_code"] = return_code
        if stderr:
            details["stderr"] = stderr[:500]
        super().__init__(message, details=details)


# =============================================================================
# Rate Limiting
# =============================================================================


class RateLimitError(ClientError):
    """
    Raised when an API rate limit is exceeded.

    Attributes:
        retry_after: Seconds to wait before retrying (if provided by API).
    """

    def __init__(
        self,
        message: str,
        retry_after: int | None = None,
        service: str | None = None,
    ) -> None:
        details: dict[str, Any] = {}
        if retry_after:
            details["retry_after"] = retry_after
        if service:
            details["service"] = service
        super().__init__(message, details=details)
        self.retry_after = retry_after


class ContentFilterError(ClientError):
    """
    Raised when content is rejected by safety filters.

    This typically happens with image generation when prompts
    trigger content moderation.
    """

    def __init__(
        self,
        message: str,
        prompt: str | None = None,
        filter_reason: str | None = None,
    ) -> None:
        details = {}
        if prompt:
            details["prompt"] = prompt[:200]
        if filter_reason:
            details["filter_reason"] = filter_reason
        super().__init__(message, details=details)

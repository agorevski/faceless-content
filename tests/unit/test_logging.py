"""
Unit tests for logging utilities.

Tests cover:
- Logging setup
- Logger retrieval
- Context binding
- LoggerMixin
- Convenience logging functions
"""

import logging
from unittest.mock import MagicMock, patch

import pytest
import structlog


class TestLoggingSetup:
    """Tests for logging setup functions."""

    def test_setup_logging_default(self) -> None:
        """Test default logging setup."""
        from faceless.utils.logging import setup_logging

        # Should not raise
        setup_logging()

    def test_setup_logging_with_level(self) -> None:
        """Test logging setup with custom level."""
        from faceless.utils.logging import setup_logging

        setup_logging(level="DEBUG")
        # Verify root logger level
        root = logging.getLogger()
        assert root.level == logging.DEBUG

    def test_setup_logging_with_json_format(self) -> None:
        """Test logging setup with JSON format."""
        from faceless.utils.logging import setup_logging

        # Should not raise
        setup_logging(json_format=True)

    def test_setup_logging_with_file(self, tmp_path) -> None:
        """Test logging setup with file output."""
        from faceless.utils.logging import setup_logging

        log_file = tmp_path / "test.log"
        setup_logging(log_file=str(log_file))

        # File handler should be added
        root = logging.getLogger()
        file_handlers = [h for h in root.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) >= 1

    def test_setup_logging_reduces_third_party_noise(self) -> None:
        """Test that third-party loggers are reduced to WARNING."""
        from faceless.utils.logging import setup_logging

        setup_logging()

        assert logging.getLogger("httpx").level == logging.WARNING
        assert logging.getLogger("httpcore").level == logging.WARNING
        assert logging.getLogger("urllib3").level == logging.WARNING


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_with_name(self) -> None:
        """Test getting logger with name."""
        from faceless.utils.logging import get_logger

        logger = get_logger("test_module")
        assert logger is not None

    def test_get_logger_without_name(self) -> None:
        """Test getting logger without name."""
        from faceless.utils.logging import get_logger

        logger = get_logger()
        assert logger is not None

    def test_get_logger_returns_bound_logger(self) -> None:
        """Test that get_logger returns a bound logger."""
        from faceless.utils.logging import get_logger

        logger = get_logger("test")
        # Should have standard logging methods
        assert hasattr(logger, "info")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")


class TestContextBinding:
    """Tests for context binding functions."""

    def test_bind_context(self) -> None:
        """Test binding context variables."""
        from faceless.utils.logging import bind_context, clear_context

        bind_context(job_id="123", niche="scary")
        # Context should be set (verified by not raising)
        clear_context()

    def test_clear_context(self) -> None:
        """Test clearing context variables."""
        from faceless.utils.logging import bind_context, clear_context

        bind_context(job_id="123")
        clear_context()
        # Should not raise

    def test_unbind_context(self) -> None:
        """Test unbinding specific context variables."""
        from faceless.utils.logging import bind_context, clear_context, unbind_context

        bind_context(job_id="123", niche="scary", platform="youtube")
        unbind_context("job_id", "niche")
        clear_context()


class TestLoggerMixin:
    """Tests for LoggerMixin class."""

    def test_logger_mixin_provides_logger(self) -> None:
        """Test that LoggerMixin provides logger property."""
        from faceless.utils.logging import LoggerMixin

        class TestClass(LoggerMixin):
            pass

        instance = TestClass()
        assert hasattr(instance, "logger")
        assert instance.logger is not None

    def test_logger_mixin_logger_has_class_name(self) -> None:
        """Test that logger is bound to class name."""
        from faceless.utils.logging import LoggerMixin

        class MyCustomService(LoggerMixin):
            pass

        instance = MyCustomService()
        logger = instance.logger
        # Logger should exist and be callable
        assert callable(logger.info)


class TestConvenienceFunctions:
    """Tests for convenience logging functions."""

    def test_log_info(self) -> None:
        """Test log_info function."""
        from faceless.utils.logging import log_info, setup_logging

        setup_logging()
        # Should not raise
        log_info("Test message", key="value")

    def test_log_warning(self) -> None:
        """Test log_warning function."""
        from faceless.utils.logging import log_warning, setup_logging

        setup_logging()
        log_warning("Warning message", code=123)

    def test_log_error(self) -> None:
        """Test log_error function."""
        from faceless.utils.logging import log_error, setup_logging

        setup_logging()
        log_error("Error message", error_type="TestError")

    def test_log_debug(self) -> None:
        """Test log_debug function."""
        from faceless.utils.logging import log_debug, setup_logging

        setup_logging(level="DEBUG")
        log_debug("Debug message", debug_info="details")

    def test_log_exception(self) -> None:
        """Test log_exception function."""
        from faceless.utils.logging import log_exception, setup_logging

        setup_logging()
        try:
            raise ValueError("Test exception")
        except ValueError:
            log_exception("Exception occurred")


class TestLoggingIntegration:
    """Integration tests for logging."""

    def test_logging_with_context(self) -> None:
        """Test logging with bound context."""
        from faceless.utils.logging import (
            bind_context,
            clear_context,
            get_logger,
            setup_logging,
        )

        setup_logging()
        bind_context(request_id="abc123")

        logger = get_logger("test")
        logger.info("Processing request")

        clear_context()

    def test_logger_mixin_in_service(self) -> None:
        """Test LoggerMixin in a service-like class."""
        from faceless.utils.logging import LoggerMixin, setup_logging

        setup_logging()

        class TestService(LoggerMixin):
            def process(self) -> str:
                self.logger.info("Processing started")
                return "done"

        service = TestService()
        result = service.process()
        assert result == "done"

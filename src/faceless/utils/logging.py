"""
Logging configuration using structlog.

This module provides structured logging with support for both
development (pretty console output) and production (JSON) formats.

Usage:
    >>> from faceless.utils.logging import get_logger, setup_logging
    >>> setup_logging()  # Call once at application startup
    >>> logger = get_logger(__name__)
    >>> logger.info("Processing started", niche="scary-stories", count=5)
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

def setup_logging(
    level: str = "INFO",
    json_format: bool = False,
    log_file: str | None = None,
) -> None:
    """
    Configure structured logging for the application.

    Should be called once at application startup, before any logging occurs.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: If True, output JSON logs (for production)
        log_file: Optional file path for log output
    """
    # Convert level string to logging constant
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Shared processors for both development and production
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if json_format:
        # Production: JSON output
        processors: list[Processor] = [
            *shared_processors,
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
        formatter = structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.JSONRenderer(),
            ],
            foreign_pre_chain=shared_processors,
        )
    else:
        # Development: Pretty console output
        processors = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.rich_traceback,
            ),
        ]
        formatter = structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.dev.ConsoleRenderer(colors=True),
            ],
            foreign_pre_chain=shared_processors,
        )

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging to use structlog
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__ of the calling module)

    Returns:
        A bound structlog logger with context support.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing scene", scene_number=1, duration=15.5)
    """
    return structlog.get_logger(name)

def bind_context(**kwargs: Any) -> None:
    """
    Bind context variables that will be included in all subsequent logs.

    Useful for adding request-scoped or job-scoped context.

    Args:
        **kwargs: Context key-value pairs to bind

    Example:
        >>> bind_context(job_id="abc123", niche="scary-stories")
        >>> logger.info("Processing")  # Will include job_id and niche
    """
    structlog.contextvars.bind_contextvars(**kwargs)

def clear_context() -> None:
    """
    Clear all bound context variables.

    Should be called at the end of a request or job to prevent
    context leakage.
    """
    structlog.contextvars.clear_contextvars()

def unbind_context(*keys: str) -> None:
    """
    Remove specific context variables.

    Args:
        *keys: Keys to remove from context
    """
    structlog.contextvars.unbind_contextvars(*keys)

class LoggerMixin:
    """
    Mixin class that provides a logger property.

    Use this as a base class for services and other classes
    that need logging.

    Example:
        >>> class MyService(LoggerMixin):
        ...     def process(self):
        ...         self.logger.info("Processing started")
    """

    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """Get logger bound to this class."""
        return get_logger(self.__class__.__name__)

# Convenience functions for quick logging without getting a logger first

def log_info(message: str, **kwargs: Any) -> None:
    """Log an info message with optional context."""
    get_logger().info(message, **kwargs)

def log_warning(message: str, **kwargs: Any) -> None:
    """Log a warning message with optional context."""
    get_logger().warning(message, **kwargs)

def log_error(message: str, **kwargs: Any) -> None:
    """Log an error message with optional context."""
    get_logger().error(message, **kwargs)

def log_debug(message: str, **kwargs: Any) -> None:
    """Log a debug message with optional context."""
    get_logger().debug(message, **kwargs)

def log_exception(message: str, **kwargs: Any) -> None:
    """Log an exception with traceback."""
    get_logger().exception(message, **kwargs)
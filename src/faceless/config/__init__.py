"""
Configuration management for the Faceless Content Pipeline.

This module provides centralized configuration using pydantic-settings,
supporting environment variables, .env files, and runtime configuration.

Usage:
    >>> from faceless.config import get_settings
    >>> settings = get_settings()
    >>> print(settings.azure_openai_endpoint)
"""

from faceless.config.settings import Settings, get_settings

__all__ = [
    "Settings",
    "get_settings",
]

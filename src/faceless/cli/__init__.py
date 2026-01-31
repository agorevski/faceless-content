"""
Command-line interface for the Faceless Content Pipeline.

This module provides the CLI using Typer, with commands for:
- Generating content
- Validating configuration
- Testing API connections
"""

from faceless.cli.commands import app

__all__ = ["app"]
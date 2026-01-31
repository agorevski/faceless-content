"""
Entry point for running faceless as a module.

Usage:
    python -m faceless --help
    python -m faceless generate --niche scary-stories --count 1
"""

from faceless.cli import app

if __name__ == "__main__":
    app()

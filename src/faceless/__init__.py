"""
Faceless Content Pipeline
=========================

AI-powered content production pipeline for creating faceless videos with
AI-generated images, text-to-speech narration, and automated video assembly.

This package provides a complete solution for producing short-form video content
for platforms like YouTube Shorts and TikTok across multiple content niches:
- Scary Stories
- Finance
- Luxury

Example Usage:
    >>> from faceless.pipeline import Orchestrator
    >>> from faceless.core.enums import Niche, Platform
    >>>
    >>> orchestrator = Orchestrator()
    >>> result = orchestrator.run(
    ...     niche=Niche.SCARY_STORIES,
    ...     platforms=[Platform.YOUTUBE, Platform.TIKTOK],
    ...     count=1,
    ... )
"""

__version__ = "1.0.0"
__author__ = "Faceless Content Team"

from faceless.core.enums import Niche, Platform
from faceless.core.models import Scene, Script

__all__ = [
    "__version__",
    "Niche",
    "Platform",
    "Scene",
    "Script",
]

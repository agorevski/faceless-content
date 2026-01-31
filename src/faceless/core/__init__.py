"""
Core domain models, enums, and exceptions for the Faceless Content Pipeline.

This module contains the fundamental building blocks:
- Enums: Niche, Platform, JobStatus
- Models: Scene, Script, Job, VisualStyle
- Exceptions: Custom exception hierarchy
"""

from faceless.core.enums import JobStatus, Niche, Platform
from faceless.core.exceptions import (
    ConfigurationError,
    FacelessError,
    GenerationError,
    ImageGenerationError,
    PipelineError,
    TTSGenerationError,
    ValidationError,
    VideoAssemblyError,
)
from faceless.core.models import Job, Scene, Script, VisualStyle

__all__ = [
    # Enums
    "Niche",
    "Platform",
    "JobStatus",
    # Models
    "Scene",
    "Script",
    "VisualStyle",
    "Job",
    # Exceptions
    "FacelessError",
    "ConfigurationError",
    "ValidationError",
    "PipelineError",
    "GenerationError",
    "ImageGenerationError",
    "TTSGenerationError",
    "VideoAssemblyError",
]

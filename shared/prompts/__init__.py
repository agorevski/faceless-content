"""
Shared prompt templates for the Faceless Content Pipeline.

This module contains prompt templates for various AI generation tasks,
organized by niche and purpose.
"""

from .image_prompts import (
    FINANCE_IMAGE_SETTINGS,
    LUXURY_IMAGE_SETTINGS,
    SCARY_STORIES_IMAGE_SETTINGS,
    build_enhanced_prompt,
    get_image_settings,
)

__all__ = [
    "SCARY_STORIES_IMAGE_SETTINGS",
    "FINANCE_IMAGE_SETTINGS",
    "LUXURY_IMAGE_SETTINGS",
    "get_image_settings",
    "build_enhanced_prompt",
]

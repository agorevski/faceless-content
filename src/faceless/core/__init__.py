"""
Core domain models, enums, and exceptions for the Faceless Content Pipeline.

This module contains the fundamental building blocks:
- Enums: Niche, Platform, JobStatus
- Models: Scene, Script, Job, VisualStyle
- Exceptions: Custom exception hierarchy
- Hooks: TikTok engagement hooks and retention strategies
- Hashtags: Hashtag ladder system for content discovery
- TikTok Formats: Content format definitions
- Posting Schedule: Optimal posting time strategies
- Text Overlay: Text overlay models for video
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
from faceless.core.hashtags import (
    HASHTAG_LADDER,
    TRENDING_TOPICS,
    analyze_hashtag_coverage,
    generate_hashtag_set,
    generate_hashtag_string,
    get_all_hashtags,
    get_format_specific_hashtags,
    get_series_suggestions,
)
from faceless.core.hooks import (
    COMMENT_TRIGGERS,
    FIRST_FRAME_HOOKS,
    LOOP_STRUCTURES,
    MID_VIDEO_HOOKS,
    PATTERN_INTERRUPTS,
    PINNED_COMMENTS,
    generate_engagement_package,
    get_comment_trigger,
    get_first_frame_hook,
    get_loop_structure,
    get_mid_video_hook,
    get_pattern_interrupt,
    get_pinned_comment,
)
from faceless.core.models import Job, Scene, Script, VisualStyle
from faceless.core.posting_schedule import (
    DAY_PATTERNS,
    FREQUENCY_RECOMMENDATIONS,
    POSTING_WINDOWS,
    format_schedule_for_display,
    generate_weekly_schedule,
    get_day_rating,
    get_next_optimal_slot,
    get_optimal_posting_time,
)
from faceless.core.text_overlay import (
    PRESET_STYLES,
    TextAnimation,
    TextOverlay,
    TextPosition,
    TextStyle,
    create_countdown_overlays,
    create_cta_overlay,
    create_hook_overlay,
    create_mid_video_overlay,
    create_pov_overlay,
    generate_overlay_filter_chain,
    overlay_to_ffmpeg_filter,
    position_to_xy,
)
from faceless.core.tiktok_formats import (
    ALL_FORMATS,
    FINANCE_FORMATS,
    LUXURY_FORMATS,
    SCARY_FORMATS,
    TikTokFormat,
    format_to_prompt_guidance,
    get_all_formats_for_niche,
    get_format,
    get_format_names,
    get_random_format,
)

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
    # Hooks
    "FIRST_FRAME_HOOKS",
    "PATTERN_INTERRUPTS",
    "MID_VIDEO_HOOKS",
    "COMMENT_TRIGGERS",
    "PINNED_COMMENTS",
    "LOOP_STRUCTURES",
    "get_first_frame_hook",
    "get_pattern_interrupt",
    "get_mid_video_hook",
    "get_comment_trigger",
    "get_pinned_comment",
    "get_loop_structure",
    "generate_engagement_package",
    # Hashtags
    "HASHTAG_LADDER",
    "TRENDING_TOPICS",
    "generate_hashtag_set",
    "generate_hashtag_string",
    "get_all_hashtags",
    "get_format_specific_hashtags",
    "get_series_suggestions",
    "analyze_hashtag_coverage",
    # TikTok Formats
    "TikTokFormat",
    "SCARY_FORMATS",
    "FINANCE_FORMATS",
    "LUXURY_FORMATS",
    "ALL_FORMATS",
    "get_format",
    "get_all_formats_for_niche",
    "get_format_names",
    "get_random_format",
    "format_to_prompt_guidance",
    # Posting Schedule
    "POSTING_WINDOWS",
    "DAY_PATTERNS",
    "FREQUENCY_RECOMMENDATIONS",
    "get_optimal_posting_time",
    "get_day_rating",
    "generate_weekly_schedule",
    "get_next_optimal_slot",
    "format_schedule_for_display",
    # Text Overlay
    "TextPosition",
    "TextAnimation",
    "TextStyle",
    "TextOverlay",
    "PRESET_STYLES",
    "create_hook_overlay",
    "create_mid_video_overlay",
    "create_cta_overlay",
    "create_countdown_overlays",
    "create_pov_overlay",
    "position_to_xy",
    "overlay_to_ffmpeg_filter",
    "generate_overlay_filter_chain",
]

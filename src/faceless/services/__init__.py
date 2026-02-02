"""
Services for the Faceless Content Pipeline.

This module provides the business logic services for content generation:
- EnhancerService: Enhance scripts with GPT
- ImageService: Generate images for scenes
- TTSService: Generate audio narration
- VideoService: Assemble videos with FFmpeg
- DeepResearchService: Conduct deep research on topics
- QualityService: Evaluate script quality and hooks
- TrendingService: Discover trending topics
- SubtitleService: Generate subtitles (SRT/VTT)
- ThumbnailService: Generate thumbnails
- ScraperService: Fetch content from sources
- MetadataService: Generate posting metadata
"""

from faceless.services.enhancer_service import EnhancerService
from faceless.services.image_service import ImageService
from faceless.services.metadata_service import (
    format_metadata_for_display,
    generate_content_metadata,
    generate_series_metadata,
    load_metadata,
    save_metadata,
)
from faceless.services.quality_service import QualityService
from faceless.services.research_service import DeepResearchService, ResearchDepth
from faceless.services.scraper_service import (
    clean_text,
    fetch_and_process_stories,
    fetch_creepypasta,
    fetch_reddit_stories,
    generate_image_prompt,
    save_story,
    story_to_script,
)
from faceless.services.subtitle_service import (
    SUBTITLE_STYLES,
    burn_subtitles_to_video,
    create_subtitles_from_audio,
    create_subtitles_from_script,
    generate_all_subtitle_formats,
    generate_animated_captions,
)
from faceless.services.thumbnail_service import (
    THUMBNAIL_CONCEPTS,
    THUMBNAIL_TEMPLATES,
    create_text_overlay_instructions,
    generate_thumbnail,
    generate_thumbnail_prompt,
    generate_thumbnail_variants,
)
from faceless.services.trending_service import TrendingService
from faceless.services.tts_service import TTSService
from faceless.services.video_service import VideoService

__all__ = [
    # Main Services
    "EnhancerService",
    "ImageService",
    "TTSService",
    "VideoService",
    "DeepResearchService",
    "ResearchDepth",
    "QualityService",
    "TrendingService",
    # Subtitle Service
    "SUBTITLE_STYLES",
    "create_subtitles_from_script",
    "create_subtitles_from_audio",
    "burn_subtitles_to_video",
    "generate_animated_captions",
    "generate_all_subtitle_formats",
    # Thumbnail Service
    "THUMBNAIL_TEMPLATES",
    "THUMBNAIL_CONCEPTS",
    "generate_thumbnail_prompt",
    "generate_thumbnail",
    "generate_thumbnail_variants",
    "create_text_overlay_instructions",
    # Scraper Service
    "clean_text",
    "fetch_reddit_stories",
    "fetch_creepypasta",
    "save_story",
    "story_to_script",
    "generate_image_prompt",
    "fetch_and_process_stories",
    # Metadata Service
    "generate_content_metadata",
    "generate_series_metadata",
    "save_metadata",
    "load_metadata",
    "format_metadata_for_display",
]

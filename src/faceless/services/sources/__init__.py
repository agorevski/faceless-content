"""
Content source adapters for the Faceless Content Pipeline.

This module provides pluggable content sources for fetching raw content
from various platforms (Reddit, Wikipedia, YouTube, News APIs, etc.).

Usage:
    from faceless.services.sources import RedditSource, WikipediaSource

    reddit = RedditSource(settings)
    content = await reddit.fetch_content(Niche.SCARY_STORIES, limit=10)
"""

from faceless.services.sources.base import (
    ContentSource,
    RawContent,
    SourceCapabilities,
)
from faceless.services.sources.hackernews_source import HackerNewsSource
from faceless.services.sources.news_source import NewsSource
from faceless.services.sources.openlibrary_source import OpenLibrarySource
from faceless.services.sources.reddit_source import RedditSource
from faceless.services.sources.wikipedia_source import WikipediaSource
from faceless.services.sources.youtube_source import YouTubeSource

__all__ = [
    "ContentSource",
    "RawContent",
    "SourceCapabilities",
    "RedditSource",
    "WikipediaSource",
    "HackerNewsSource",
    "OpenLibrarySource",
    "NewsSource",
    "YouTubeSource",
]

"""
Abstract base class for content sources.

All content source adapters inherit from ContentSource and implement
a consistent interface for fetching content from various platforms.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from faceless.core.enums import ContentSourceType, Niche
from faceless.utils.logging import LoggerMixin


@dataclass
class SourceCapabilities:
    """Describes what a content source can do."""

    supports_search: bool = True
    supports_trending: bool = False
    supports_pagination: bool = True
    requires_api_key: bool = False
    rate_limit_per_minute: int = 60
    max_results_per_request: int = 100


@dataclass
class RawContent:
    """
    Unified content from any source.

    This is the common format returned by all content sources,
    allowing the pipeline to process content uniformly regardless
    of its origin.

    Attributes:
        title: Content title or headline
        content: Main text content (article body, post text, etc.)
        source_type: Type of source (reddit, wikipedia, etc.)
        source_url: Original URL of the content
        source_id: Unique identifier from the source (post ID, article ID, etc.)
        author: Content author if available
        published_at: Original publication date if available
        fetched_at: When this content was fetched
        score: Normalized engagement score (0-100)
        metadata: Source-specific additional data
    """

    title: str
    content: str
    source_type: ContentSourceType
    source_url: str
    source_id: str = ""
    author: str | None = None
    published_at: datetime | None = None
    fetched_at: datetime = field(default_factory=datetime.now)
    score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "title": self.title,
            "content": self.content,
            "source_type": self.source_type.value,
            "source_url": self.source_url,
            "source_id": self.source_id,
            "author": self.author,
            "published_at": (
                self.published_at.isoformat() if self.published_at else None
            ),
            "fetched_at": self.fetched_at.isoformat(),
            "score": self.score,
            "metadata": self.metadata,
        }

    @property
    def word_count(self) -> int:
        """Number of words in the content."""
        return len(self.content.split())

    @property
    def has_sufficient_content(self) -> bool:
        """Check if content has enough words for video (min 100 words)."""
        return self.word_count >= 100


class ContentSource(ABC, LoggerMixin):
    """
    Abstract base class for content sources.

    All content source adapters must inherit from this class and implement
    the required methods for fetching content.

    Example:
        class RedditSource(ContentSource):
            @property
            def source_type(self) -> ContentSourceType:
                return ContentSourceType.REDDIT

            async def fetch_content(self, niche, query, limit):
                # Implementation here
                ...
    """

    @property
    @abstractmethod
    def source_type(self) -> ContentSourceType:
        """Return the type of this content source."""
        ...

    @property
    @abstractmethod
    def capabilities(self) -> SourceCapabilities:
        """Return the capabilities of this source."""
        ...

    @abstractmethod
    def supports_niche(self, niche: Niche) -> bool:
        """
        Check if this source supports the given niche.

        Args:
            niche: The content niche to check

        Returns:
            True if this source can provide content for the niche
        """
        ...

    @abstractmethod
    async def fetch_content(
        self,
        niche: Niche,
        query: str | None = None,
        limit: int = 10,
    ) -> list[RawContent]:
        """
        Fetch content from this source.

        Args:
            niche: The content niche to fetch for
            query: Optional search query to filter content
            limit: Maximum number of items to fetch

        Returns:
            List of RawContent items

        Raises:
            ContentFetchError: If fetching fails
            SourceUnavailableError: If the source is unavailable
        """
        ...

    async def fetch_trending(
        self,
        niche: Niche,
        limit: int = 10,
    ) -> list[RawContent]:
        """
        Fetch trending content from this source.

        Default implementation falls back to fetch_content.
        Override in sources that support trending.

        Args:
            niche: The content niche
            limit: Maximum number of items

        Returns:
            List of trending RawContent items
        """
        if not self.capabilities.supports_trending:
            return await self.fetch_content(niche, limit=limit)
        return []

    async def search(
        self,
        query: str,
        niche: Niche | None = None,
        limit: int = 10,
    ) -> list[RawContent]:
        """
        Search for content matching a query.

        Default implementation uses fetch_content with query.

        Args:
            query: Search query
            niche: Optional niche filter
            limit: Maximum number of items

        Returns:
            List of matching RawContent items
        """
        if niche:
            return await self.fetch_content(niche, query=query, limit=limit)
        return []

    def is_available(self) -> bool:
        """
        Check if this source is available (API key configured, etc.).

        Default implementation returns True.
        Override for sources requiring API keys.
        """
        return True

    def get_supported_niches(self) -> list[Niche]:
        """
        Get list of all niches this source supports.

        Returns:
            List of supported Niche enums
        """
        return [niche for niche in Niche if self.supports_niche(niche)]

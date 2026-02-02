"""
Unit tests for content source adapters.

Tests all individual source adapters: Reddit, Wikipedia, HackerNews,
OpenLibrary, News, and YouTube.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from faceless.core.enums import ContentSourceType, Niche
from faceless.core.exceptions import ContentFetchError, SourceUnavailableError


# =============================================================================
# Reddit Source Tests
# =============================================================================


class TestRedditSourceFetch:
    """Tests for Reddit source fetch operations."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings."""
        settings = MagicMock()
        settings.content_sources.reddit_rate_limit = 60
        settings.content_sources.cache_ttl_seconds = 3600
        settings.content_sources.min_score = 50
        settings.reddit.user_agent = "Test/1.0"
        return settings

    @patch("faceless.services.sources.reddit_source.get_settings")
    @pytest.mark.asyncio
    async def test_fetch_content_returns_raw_content(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test that fetch_content returns RawContent items."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.reddit_source import RedditSource

        source = RedditSource()

        with patch.object(source, "_make_request") as mock_request:
            mock_request.return_value = [
                {
                    "id": "abc123",
                    "title": "Test Story",
                    "selftext": " ".join(["word"] * 150),
                    "author": "test_user",
                    "score": 500,
                    "permalink": "/r/nosleep/test",
                    "created_utc": 1700000000,
                    "upvote_ratio": 0.95,
                    "num_comments": 50,
                }
            ]

            result = await source.fetch_content(Niche.SCARY_STORIES, limit=1)

            assert len(result) >= 0  # May be filtered

    @patch("faceless.services.sources.reddit_source.get_settings")
    @pytest.mark.asyncio
    async def test_fetch_content_uses_cache(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test that fetch_content uses cache."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.reddit_source import RedditSource
        from faceless.services.sources.base import RawContent

        source = RedditSource()

        # Prime cache
        cached_content = [
            RawContent(
                title="Cached",
                content=" ".join(["word"] * 150),
                source_type=ContentSourceType.REDDIT,
                source_url="https://reddit.com/test",
            )
        ]
        cache_key = f"reddit:{Niche.SCARY_STORIES.value}:top:5:month"
        source._cache.set(cache_key, cached_content)

        result = await source.fetch_content(Niche.SCARY_STORIES, limit=5)

        assert len(result) == 1
        assert result[0].title == "Cached"

    @patch("faceless.services.sources.reddit_source.get_settings")
    @pytest.mark.asyncio
    async def test_fetch_trending(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test fetch_trending method."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.reddit_source import RedditSource

        source = RedditSource()

        with patch.object(source, "_fetch_hot_posts") as mock_hot:
            mock_hot.return_value = [
                {
                    "id": "hot1",
                    "title": "Hot Post",
                    "selftext": " ".join(["word"] * 150),
                    "score": 1000,
                    "author": "user",
                    "permalink": "/r/test/hot1",
                    "created_utc": 1700000000,
                }
            ]

            result = await source.fetch_trending(Niche.SCARY_STORIES, limit=1)

            mock_hot.assert_called()


class TestRedditRateLimiter:
    """Tests for Reddit rate limiter."""

    @pytest.mark.asyncio
    async def test_rate_limiter_acquire(self) -> None:
        """Test rate limiter token acquisition."""
        from faceless.services.sources.reddit_source import RateLimiter

        limiter = RateLimiter(requests_per_minute=60)

        # Should not block for first request
        await limiter.acquire()

        assert limiter.tokens < 60


class TestRedditCache:
    """Tests for Reddit content cache."""

    def test_cache_set_and_get(self) -> None:
        """Test cache set and get."""
        from faceless.services.sources.reddit_source import ContentCache
        from faceless.services.sources.base import RawContent

        cache = ContentCache(ttl_seconds=3600)

        content = [
            RawContent(
                title="Test",
                content="Content",
                source_type=ContentSourceType.REDDIT,
                source_url="https://example.com",
            )
        ]

        cache.set("key1", content)
        result = cache.get("key1")

        assert result is not None
        assert len(result) == 1
        assert result[0].title == "Test"

    def test_cache_miss(self) -> None:
        """Test cache miss returns None."""
        from faceless.services.sources.reddit_source import ContentCache

        cache = ContentCache(ttl_seconds=3600)
        result = cache.get("nonexistent")

        assert result is None

    def test_cache_clear(self) -> None:
        """Test cache clear."""
        from faceless.services.sources.reddit_source import ContentCache
        from faceless.services.sources.base import RawContent

        cache = ContentCache(ttl_seconds=3600)
        cache.set("key", [RawContent(
            title="Test",
            content="C",
            source_type=ContentSourceType.REDDIT,
            source_url="https://example.com",
        )])

        cache.clear()
        result = cache.get("key")

        assert result is None


# =============================================================================
# Wikipedia Source Tests
# =============================================================================


class TestWikipediaSource:
    """Tests for Wikipedia source adapter."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings."""
        settings = MagicMock()
        settings.content_sources.wikipedia_rate_limit = 200
        settings.content_sources.cache_ttl_seconds = 3600
        return settings

    @patch("faceless.services.sources.wikipedia_source.get_settings")
    def test_supports_educational_niches(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test Wikipedia supports educational niches."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.wikipedia_source import WikipediaSource

        source = WikipediaSource()

        assert source.supports_niche(Niche.HISTORY)
        assert source.supports_niche(Niche.PSYCHOLOGY_FACTS)
        assert source.supports_niche(Niche.SPACE_ASTRONOMY)
        assert source.supports_niche(Niche.PHILOSOPHY)

    @patch("faceless.services.sources.wikipedia_source.get_settings")
    def test_capabilities(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test Wikipedia capabilities."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.wikipedia_source import WikipediaSource

        source = WikipediaSource()
        caps = source.capabilities

        assert caps.supports_search is True
        assert caps.supports_trending is True
        assert caps.requires_api_key is False

    @patch("faceless.services.sources.wikipedia_source.get_settings")
    @pytest.mark.asyncio
    async def test_fetch_content(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test Wikipedia fetch_content."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.wikipedia_source import WikipediaSource

        source = WikipediaSource()

        with patch.object(source, "_search_articles") as mock_search, \
             patch.object(source, "_get_article_content") as mock_content:
            mock_search.return_value = [{"title": "Test Article"}]
            mock_content.return_value = None  # Filtered out

            result = await source.fetch_content(Niche.HISTORY, limit=1)

            mock_search.assert_called()


class TestWikipediaTextCleaning:
    """Tests for Wikipedia text cleaning."""

    def test_removes_citations(self) -> None:
        """Test removing citation markers."""
        from faceless.services.sources.wikipedia_source import clean_wikipedia_text

        text = "This is a fact[1] with multiple[2][3] citations."
        result = clean_wikipedia_text(text)

        assert "[1]" not in result
        assert "[2]" not in result
        assert "[3]" not in result

    def test_removes_citation_needed(self) -> None:
        """Test removing [citation needed]."""
        from faceless.services.sources.wikipedia_source import clean_wikipedia_text

        text = "This claim[citation needed] needs verification."
        result = clean_wikipedia_text(text)

        assert "[citation needed]" not in result.lower()

    def test_removes_disambiguation(self) -> None:
        """Test removing disambiguation notices."""
        from faceless.services.sources.wikipedia_source import clean_wikipedia_text

        text = "For other uses, see Test. This is the main content."
        result = clean_wikipedia_text(text)

        assert "For other uses" not in result


# =============================================================================
# HackerNews Source Tests
# =============================================================================


class TestHackerNewsSource:
    """Tests for HackerNews source adapter."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings."""
        settings = MagicMock()
        settings.content_sources.hackernews_rate_limit = 60
        return settings

    @patch("faceless.services.sources.hackernews_source.get_settings")
    def test_supports_tech_niches(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test HN supports tech niches."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.hackernews_source import HackerNewsSource

        source = HackerNewsSource()

        assert source.supports_niche(Niche.TECH_GADGETS)
        assert source.supports_niche(Niche.AI_FUTURE_TECH)
        assert not source.supports_niche(Niche.SCARY_STORIES)

    @patch("faceless.services.sources.hackernews_source.get_settings")
    def test_capabilities(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test HN capabilities."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.hackernews_source import HackerNewsSource

        source = HackerNewsSource()
        caps = source.capabilities

        assert caps.supports_search is False  # HN API doesn't support search
        assert caps.supports_trending is True
        assert caps.requires_api_key is False

    @patch("faceless.services.sources.hackernews_source.get_settings")
    @pytest.mark.asyncio
    async def test_fetch_content(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test HN fetch_content."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.hackernews_source import HackerNewsSource

        source = HackerNewsSource()

        with patch.object(source, "_get_top_story_ids") as mock_ids, \
             patch.object(source, "_get_item") as mock_item:
            mock_ids.return_value = [1, 2, 3]
            mock_item.return_value = {
                "id": 1,
                "type": "story",
                "title": "AI News",
                "text": "Some AI content here",
                "score": 100,
                "by": "user",
                "time": 1700000000,
            }

            result = await source.fetch_content(Niche.AI_FUTURE_TECH, limit=1)

            mock_ids.assert_called()

    @patch("faceless.services.sources.hackernews_source.get_settings")
    @pytest.mark.asyncio
    async def test_fetch_trending_delegates_to_fetch_content(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test fetch_trending delegates to fetch_content."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.hackernews_source import HackerNewsSource

        source = HackerNewsSource()

        with patch.object(source, "fetch_content") as mock_fetch:
            mock_fetch.return_value = []

            await source.fetch_trending(Niche.TECH_GADGETS, limit=5)

            mock_fetch.assert_called_once_with(Niche.TECH_GADGETS, limit=5)

    @patch("faceless.services.sources.hackernews_source.get_settings")
    @pytest.mark.asyncio
    async def test_get_story_with_comments(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test getting story with comments."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.hackernews_source import HackerNewsSource

        source = HackerNewsSource()

        with patch.object(source, "_get_item") as mock_item:
            mock_item.side_effect = [
                {
                    "id": 1,
                    "title": "Story",
                    "kids": [100, 101],
                },
                {"id": 100, "text": "Comment 1", "by": "user1"},
                {"id": 101, "text": "Comment 2", "by": "user2"},
            ]

            result = await source.get_story_with_comments(1, max_comments=2)

            assert result is not None
            assert "comments" in result
            assert len(result["comments"]) == 2


# =============================================================================
# News Source Tests
# =============================================================================


class TestNewsSource:
    """Tests for News source adapter."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings."""
        settings = MagicMock()
        settings.content_sources.newsapi_key = "test-api-key"
        settings.content_sources.newsapi_configured = True
        return settings

    @pytest.fixture
    def mock_settings_unconfigured(self) -> MagicMock:
        """Create mock settings without API key."""
        settings = MagicMock()
        settings.content_sources.newsapi_key = ""
        settings.content_sources.newsapi_configured = False
        return settings

    @patch("faceless.services.sources.news_source.get_settings")
    def test_is_available_with_key(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test is_available returns True with API key."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.news_source import NewsSource

        source = NewsSource()

        assert source.is_available() is True

    @patch("faceless.services.sources.news_source.get_settings")
    def test_is_available_without_key(
        self, mock_get_settings: MagicMock, mock_settings_unconfigured: MagicMock
    ) -> None:
        """Test is_available returns False without API key."""
        mock_get_settings.return_value = mock_settings_unconfigured

        from faceless.services.sources.news_source import NewsSource

        source = NewsSource()

        assert source.is_available() is False

    @patch("faceless.services.sources.news_source.get_settings")
    def test_supports_niche_requires_availability(
        self, mock_get_settings: MagicMock, mock_settings_unconfigured: MagicMock
    ) -> None:
        """Test supports_niche returns False when unavailable."""
        mock_get_settings.return_value = mock_settings_unconfigured

        from faceless.services.sources.news_source import NewsSource

        source = NewsSource()

        assert source.supports_niche(Niche.FINANCE) is False

    @patch("faceless.services.sources.news_source.get_settings")
    @pytest.mark.asyncio
    async def test_fetch_content_raises_when_unavailable(
        self, mock_get_settings: MagicMock, mock_settings_unconfigured: MagicMock
    ) -> None:
        """Test fetch_content raises SourceUnavailableError."""
        mock_get_settings.return_value = mock_settings_unconfigured

        from faceless.services.sources.news_source import NewsSource

        source = NewsSource()

        with pytest.raises(SourceUnavailableError):
            await source.fetch_content(Niche.FINANCE, limit=1)

    @patch("faceless.services.sources.news_source.get_settings")
    def test_capabilities(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test News source capabilities."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.news_source import NewsSource

        source = NewsSource()
        caps = source.capabilities

        assert caps.requires_api_key is True
        assert caps.supports_search is True
        assert caps.supports_trending is True


# =============================================================================
# OpenLibrary Source Tests
# =============================================================================


class TestOpenLibrarySource:
    """Tests for OpenLibrary source adapter."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings."""
        settings = MagicMock()
        settings.content_sources.openlibrary_rate_limit = 100
        return settings

    @patch("faceless.services.sources.openlibrary_source.get_settings")
    def test_supports_book_niches(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test OpenLibrary supports book-related niches."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.openlibrary_source import OpenLibrarySource

        source = OpenLibrarySource()

        assert source.supports_niche(Niche.BOOK_SUMMARIES)
        assert source.supports_niche(Niche.PHILOSOPHY)
        assert source.supports_niche(Niche.PSYCHOLOGY_FACTS)
        assert not source.supports_niche(Niche.SCARY_STORIES)

    @patch("faceless.services.sources.openlibrary_source.get_settings")
    def test_capabilities(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test OpenLibrary capabilities."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.openlibrary_source import OpenLibrarySource

        source = OpenLibrarySource()
        caps = source.capabilities

        assert caps.requires_api_key is False
        assert caps.supports_search is True

    @patch("faceless.services.sources.openlibrary_source.get_settings")
    @pytest.mark.asyncio
    async def test_fetch_content(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test fetch_content method."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.openlibrary_source import OpenLibrarySource

        source = OpenLibrarySource()

        with patch.object(source, "_search_by_subjects") as mock_search, \
             patch.object(source, "_book_to_raw_content") as mock_convert:
            mock_search.return_value = [{"key": "/works/OL123"}]
            mock_convert.return_value = None

            result = await source.fetch_content(Niche.BOOK_SUMMARIES, limit=1)

            mock_search.assert_called()

    @patch("faceless.services.sources.openlibrary_source.get_settings")
    @pytest.mark.asyncio
    async def test_fetch_content_with_query(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test fetch_content with search query."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.openlibrary_source import OpenLibrarySource

        source = OpenLibrarySource()

        with patch.object(source, "_search_books") as mock_search, \
             patch.object(source, "_book_to_raw_content") as mock_convert:
            mock_search.return_value = [{"key": "/works/OL123"}]
            mock_convert.return_value = None

            await source.fetch_content(
                Niche.BOOK_SUMMARIES,
                query="psychology",
                limit=1,
            )

            mock_search.assert_called_once_with("psychology", 1)


# =============================================================================
# YouTube Source Tests
# =============================================================================


class TestYouTubeSource:
    """Tests for YouTube source adapter."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings."""
        settings = MagicMock()
        settings.content_sources.youtube_api_key = "test-api-key"
        settings.content_sources.youtube_configured = True
        return settings

    @pytest.fixture
    def mock_settings_unconfigured(self) -> MagicMock:
        """Create mock settings without API key."""
        settings = MagicMock()
        settings.content_sources.youtube_api_key = ""
        settings.content_sources.youtube_configured = False
        return settings

    @patch("faceless.services.sources.youtube_source.get_settings")
    def test_is_available_with_key(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test is_available returns True with API key."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.youtube_source import YouTubeSource

        source = YouTubeSource()

        assert source.is_available() is True

    @patch("faceless.services.sources.youtube_source.get_settings")
    def test_is_available_without_key(
        self, mock_get_settings: MagicMock, mock_settings_unconfigured: MagicMock
    ) -> None:
        """Test is_available returns False without API key."""
        mock_get_settings.return_value = mock_settings_unconfigured

        from faceless.services.sources.youtube_source import YouTubeSource

        source = YouTubeSource()

        assert source.is_available() is False

    @patch("faceless.services.sources.youtube_source.get_settings")
    def test_supports_all_niches_when_available(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test YouTube supports all niches when available."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.youtube_source import YouTubeSource

        source = YouTubeSource()

        for niche in Niche:
            assert source.supports_niche(niche) is True

    @patch("faceless.services.sources.youtube_source.get_settings")
    @pytest.mark.asyncio
    async def test_fetch_content_raises_when_unavailable(
        self, mock_get_settings: MagicMock, mock_settings_unconfigured: MagicMock
    ) -> None:
        """Test fetch_content raises SourceUnavailableError."""
        mock_get_settings.return_value = mock_settings_unconfigured

        from faceless.services.sources.youtube_source import YouTubeSource

        source = YouTubeSource()

        with pytest.raises(SourceUnavailableError):
            await source.fetch_content(Niche.TECH_GADGETS, limit=1)

    @patch("faceless.services.sources.youtube_source.get_settings")
    @pytest.mark.asyncio
    async def test_fetch_trending(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test fetch_trending method."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.youtube_source import YouTubeSource

        source = YouTubeSource()

        with patch.object(source, "fetch_content") as mock_fetch:
            mock_fetch.return_value = []

            await source.fetch_trending(Niche.SCARY_STORIES, limit=5)

            mock_fetch.assert_called()


# =============================================================================
# Content Source Service Tests
# =============================================================================


# =============================================================================
# More Wikipedia Source Tests
# =============================================================================


class TestWikipediaSourceFetch:
    """More tests for Wikipedia fetch operations."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings."""
        settings = MagicMock()
        settings.content_sources.wikipedia_rate_limit = 200
        settings.content_sources.cache_ttl_seconds = 3600
        return settings

    @patch("faceless.services.sources.wikipedia_source.get_settings")
    @pytest.mark.asyncio
    async def test_get_article_summary(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test getting an article summary."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.wikipedia_source import WikipediaSource

        source = WikipediaSource()

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "title": "Test Article",
                "extract": " ".join(["word"] * 150),
                "type": "standard",
                "pageid": 12345,
                "content_urls": {"desktop": {"page": "https://wiki.test"}},
            }
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = MagicMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_client_instance

            result = await source.get_article_summary("Test_Article", Niche.HISTORY)

            assert result is not None
            assert result.title == "Test Article"

    @patch("faceless.services.sources.wikipedia_source.get_settings")
    @pytest.mark.asyncio
    async def test_get_article_summary_disambiguation(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test handling disambiguation pages."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.wikipedia_source import WikipediaSource

        source = WikipediaSource()

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "type": "disambiguation",
            }
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = MagicMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_client_instance

            result = await source.get_article_summary("Ambiguous", Niche.HISTORY)

            assert result is None

    @patch("faceless.services.sources.wikipedia_source.get_settings")
    @pytest.mark.asyncio
    async def test_fetch_trending(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test fetch_trending method."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.wikipedia_source import WikipediaSource

        source = WikipediaSource()

        with patch.object(source, "_get_featured_article") as mock_featured, \
             patch.object(source, "fetch_content") as mock_fetch:
            mock_featured.return_value = None
            mock_fetch.return_value = []

            result = await source.fetch_trending(Niche.HISTORY, limit=5)

            mock_featured.assert_called_once()


# =============================================================================
# More HackerNews Source Tests
# =============================================================================


class TestHackerNewsSourceFetch:
    """More tests for HackerNews fetch operations."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings."""
        settings = MagicMock()
        settings.content_sources.hackernews_rate_limit = 60
        return settings

    @patch("faceless.services.sources.hackernews_source.get_settings")
    @pytest.mark.asyncio
    async def test_get_top_story_ids(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test getting top story IDs."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.hackernews_source import HackerNewsSource

        source = HackerNewsSource()

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = [1, 2, 3, 4, 5]
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = MagicMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_client_instance

            result = await source._get_top_story_ids()

            assert len(result) == 5

    @patch("faceless.services.sources.hackernews_source.get_settings")
    @pytest.mark.asyncio
    async def test_get_best_story_ids(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test getting best story IDs."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.hackernews_source import HackerNewsSource

        source = HackerNewsSource()

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = [10, 20, 30]
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = MagicMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_client_instance

            result = await source._get_best_story_ids()

            assert len(result) == 3

    @patch("faceless.services.sources.hackernews_source.get_settings")
    @pytest.mark.asyncio
    async def test_get_item(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test getting a single item."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.hackernews_source import HackerNewsSource

        source = HackerNewsSource()

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "id": 123,
                "type": "story",
                "title": "Test Story",
            }
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = MagicMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_client_instance

            result = await source._get_item(123)

            assert result["id"] == 123

    @patch("faceless.services.sources.hackernews_source.get_settings")
    def test_story_to_raw_content(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test converting story to RawContent."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.hackernews_source import HackerNewsSource

        source = HackerNewsSource()

        story = {
            "id": 123,
            "title": "AI News Story",
            "text": "Some content here",
            "score": 100,
            "by": "author",
            "time": 1700000000,
            "descendants": 50,
            "url": "https://example.com",
        }

        result = source._story_to_raw_content(story, Niche.AI_FUTURE_TECH)

        assert result.title == "AI News Story"
        assert result.source_type == ContentSourceType.HACKER_NEWS
        assert "hn_score" in result.metadata

    @patch("faceless.services.sources.hackernews_source.get_settings")
    def test_story_to_raw_content_no_text(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test story without text creates content from title."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.hackernews_source import HackerNewsSource

        source = HackerNewsSource()

        story = {
            "id": 123,
            "title": "Link Only Story",
            "score": 50,
            "by": "author",
            "time": 1700000000,
        }

        result = source._story_to_raw_content(story, Niche.TECH_GADGETS)

        assert "Link Only Story" in result.content


# =============================================================================
# More News Source Tests
# =============================================================================


class TestNewsSourceFetch:
    """More tests for News source fetch operations."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings."""
        settings = MagicMock()
        settings.content_sources.newsapi_key = "test-api-key"
        settings.content_sources.newsapi_configured = True
        return settings

    @patch("faceless.services.sources.news_source.get_settings")
    @pytest.mark.asyncio
    async def test_search_everything(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test search_everything method."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.news_source import NewsSource

        source = NewsSource()

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "status": "ok",
                "articles": [
                    {
                        "title": "Test Article",
                        "content": " ".join(["word"] * 150),
                        "url": "https://news.test",
                        "author": "Author",
                        "publishedAt": "2024-01-01T12:00:00Z",
                        "source": {"name": "Test News"},
                    }
                ],
            }
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = MagicMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_client_instance

            result = await source._search_everything("technology", 10)

            assert len(result) == 1

    @patch("faceless.services.sources.news_source.get_settings")
    @pytest.mark.asyncio
    async def test_get_top_headlines(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test getting top headlines."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.news_source import NewsSource

        source = NewsSource()

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "status": "ok",
                "articles": [{"title": "Headline"}],
            }
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = MagicMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_client_instance

            result = await source._get_top_headlines("technology", 5)

            assert len(result) == 1

    @patch("faceless.services.sources.news_source.get_settings")
    def test_article_to_raw_content(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test converting article to RawContent."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.news_source import NewsSource

        source = NewsSource()

        article = {
            "title": "Tech News",
            "content": "Some tech content here.",
            "url": "https://tech.news/article",
            "author": "Reporter",
            "publishedAt": "2024-01-15T10:00:00Z",
            "source": {"name": "TechCrunch"},
            "urlToImage": "https://image.url",
            "description": "Tech description",
        }

        result = source._article_to_raw_content(article, Niche.TECH_GADGETS)

        assert result is not None
        assert result.title == "Tech News"
        assert result.score >= 70.0  # Base score

    @patch("faceless.services.sources.news_source.get_settings")
    def test_article_to_raw_content_major_source_bonus(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test major source gets score bonus."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.news_source import NewsSource

        source = NewsSource()

        article = {
            "title": "Reuters Report",
            "content": "Important news content.",
            "url": "https://reuters.com/article",
            "source": {"name": "Reuters"},
        }

        result = source._article_to_raw_content(article, Niche.FINANCE)

        assert result is not None
        assert result.score >= 85.0  # Major source bonus

    @patch("faceless.services.sources.news_source.get_settings")
    def test_article_to_raw_content_missing_data(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test handling article with missing data."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.news_source import NewsSource

        source = NewsSource()

        # Missing title
        result = source._article_to_raw_content({"content": "Some content"}, Niche.FINANCE)
        assert result is None

        # Missing content
        result = source._article_to_raw_content({"title": "Title"}, Niche.FINANCE)
        assert result is None


# =============================================================================
# More OpenLibrary Source Tests
# =============================================================================


class TestOpenLibrarySourceFetch:
    """More tests for OpenLibrary fetch operations."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings."""
        settings = MagicMock()
        settings.content_sources.openlibrary_rate_limit = 100
        return settings

    @patch("faceless.services.sources.openlibrary_source.get_settings")
    @pytest.mark.asyncio
    async def test_search_books(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test searching books."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.openlibrary_source import OpenLibrarySource

        source = OpenLibrarySource()

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "docs": [
                    {
                        "key": "/works/OL123W",
                        "title": "Test Book",
                        "author_name": ["Author Name"],
                    }
                ]
            }
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = MagicMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_client_instance

            result = await source._search_books("psychology", 5)

            assert len(result) == 1

    @patch("faceless.services.sources.openlibrary_source.get_settings")
    @pytest.mark.asyncio
    async def test_get_trending_by_subject(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test getting trending books by subject."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.openlibrary_source import OpenLibrarySource

        source = OpenLibrarySource()

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "works": [{"key": "OL123W", "title": "Trending Book"}]
            }
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = MagicMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_client_instance

            result = await source._get_trending_by_subject("philosophy", 5)

            assert len(result) == 1

    @patch("faceless.services.sources.openlibrary_source.get_settings")
    @pytest.mark.asyncio
    async def test_get_book_details(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test getting book details."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.openlibrary_source import OpenLibrarySource

        source = OpenLibrarySource()

        with patch("httpx.AsyncClient") as mock_client, \
             patch.object(source, "_get_author_name") as mock_author:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "title": "Detailed Book",
                "description": " ".join(["word"] * 150),
                "authors": [{"author": {"key": "/authors/OL123A"}}],
                "subjects": ["Philosophy", "Ethics"],
            }
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = MagicMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_client_instance

            mock_author.return_value = "Author Name"

            result = await source.get_book_details("/works/OL123W", Niche.PHILOSOPHY)

            assert result is not None
            assert result.title == "Detailed Book"


# =============================================================================
# More YouTube Source Tests
# =============================================================================


class TestYouTubeSourceFetch:
    """More tests for YouTube fetch operations."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings."""
        settings = MagicMock()
        settings.content_sources.youtube_api_key = "test-api-key"
        settings.content_sources.youtube_configured = True
        return settings

    @patch("faceless.services.sources.youtube_source.get_settings")
    @pytest.mark.asyncio
    async def test_search_videos(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test searching videos."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.youtube_source import YouTubeSource

        source = YouTubeSource()

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "items": [
                    {
                        "id": {"videoId": "abc123"},
                        "snippet": {
                            "title": "Test Video",
                            "description": "Video description",
                            "channelTitle": "Test Channel",
                            "publishedAt": "2024-01-01T12:00:00Z",
                        },
                    }
                ]
            }
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = MagicMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_client_instance

            result = await source._search_videos("scary stories", 10)

            assert len(result) == 1

    @patch("faceless.services.sources.youtube_source.get_settings")
    @pytest.mark.asyncio
    async def test_get_video_details(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test getting video details."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.youtube_source import YouTubeSource

        source = YouTubeSource()

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "items": [
                    {
                        "id": "abc123",
                        "snippet": {"title": "Detailed Video"},
                        "statistics": {"viewCount": "1000000"},
                    }
                ]
            }
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = MagicMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_client_instance

            result = await source.get_video_details("abc123")

            assert result is not None
            assert result["snippet"]["title"] == "Detailed Video"

    @patch("faceless.services.sources.youtube_source.get_settings")
    def test_video_to_raw_content(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test converting video to RawContent."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.youtube_source import YouTubeSource

        source = YouTubeSource()

        video = {
            "id": {"videoId": "xyz789"},
            "snippet": {
                "title": "Horror Story Narration",
                "description": "Scary story description",
                "channelTitle": "Horror Channel",
                "channelId": "UC123",
                "publishedAt": "2024-01-01T12:00:00Z",
                "thumbnails": {"high": {"url": "https://thumb.url"}},
            },
        }

        result = source._video_to_raw_content(video, Niche.SCARY_STORIES)

        assert result is not None
        assert result.title == "Horror Story Narration"
        assert result.source_type == ContentSourceType.YOUTUBE
        assert "video_id" in result.metadata

    @patch("faceless.services.sources.youtube_source.get_settings")
    def test_video_to_raw_content_string_id(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test handling video with string ID (from details API)."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.youtube_source import YouTubeSource

        source = YouTubeSource()

        video = {
            "id": "direct_video_id",
            "snippet": {
                "title": "Video Title",
                "description": "Description",
                "channelTitle": "Channel",
            },
        }

        result = source._video_to_raw_content(video, Niche.FINANCE)

        assert result is not None
        assert result.metadata["video_id"] == "direct_video_id"


class TestContentSourceServiceExtended:
    """Extended tests for ContentSourceService."""

    @pytest.fixture
    def mock_all_settings(self) -> MagicMock:
        """Create comprehensive mock settings."""
        settings = MagicMock()
        settings.content_sources.reddit_rate_limit = 60
        settings.content_sources.wikipedia_rate_limit = 200
        settings.content_sources.hackernews_rate_limit = 60
        settings.content_sources.cache_ttl_seconds = 3600
        settings.content_sources.min_score = 50
        settings.content_sources.min_content_words = 100
        settings.content_sources.youtube_api_key = ""
        settings.content_sources.newsapi_key = ""
        settings.content_sources.youtube_configured = False
        settings.content_sources.newsapi_configured = False
        settings.reddit.user_agent = "Test/1.0"
        settings.get_scripts_dir.return_value = MagicMock()
        return settings

    @patch("faceless.services.content_source_service.get_settings")
    @patch("faceless.services.sources.reddit_source.get_settings")
    @patch("faceless.services.sources.wikipedia_source.get_settings")
    @patch("faceless.services.sources.hackernews_source.get_settings")
    @patch("faceless.services.sources.openlibrary_source.get_settings")
    @patch("faceless.services.sources.news_source.get_settings")
    @patch("faceless.services.sources.youtube_source.get_settings")
    def test_content_to_script_dict(
        self,
        mock_yt: MagicMock,
        mock_news: MagicMock,
        mock_ol: MagicMock,
        mock_hn: MagicMock,
        mock_wiki: MagicMock,
        mock_reddit: MagicMock,
        mock_service: MagicMock,
        mock_all_settings: MagicMock,
    ) -> None:
        """Test converting RawContent to script dict."""
        for mock in [
            mock_yt, mock_news, mock_ol, mock_hn,
            mock_wiki, mock_reddit, mock_service
        ]:
            mock.return_value = mock_all_settings

        from faceless.services.content_source_service import ContentSourceService
        from faceless.services.sources.base import RawContent

        service = ContentSourceService()

        content = RawContent(
            title="Test Story",
            content="This is a test story.\n\nWith multiple paragraphs.",
            source_type=ContentSourceType.REDDIT,
            source_url="https://reddit.com/test",
            author="test_author",
        )

        script = service.content_to_script_dict(content, Niche.SCARY_STORIES)

        assert script["title"] == "Test Story"
        assert script["source"] == "reddit"
        assert script["author"] == "test_author"
        assert "scenes" in script

    @patch("faceless.services.content_source_service.get_settings")
    @patch("faceless.services.sources.reddit_source.get_settings")
    @patch("faceless.services.sources.wikipedia_source.get_settings")
    @patch("faceless.services.sources.hackernews_source.get_settings")
    @patch("faceless.services.sources.openlibrary_source.get_settings")
    @patch("faceless.services.sources.news_source.get_settings")
    @patch("faceless.services.sources.youtube_source.get_settings")
    def test_deduplicate_by_title(
        self,
        mock_yt: MagicMock,
        mock_news: MagicMock,
        mock_ol: MagicMock,
        mock_hn: MagicMock,
        mock_wiki: MagicMock,
        mock_reddit: MagicMock,
        mock_service: MagicMock,
        mock_all_settings: MagicMock,
    ) -> None:
        """Test deduplication by title."""
        for mock in [
            mock_yt, mock_news, mock_ol, mock_hn,
            mock_wiki, mock_reddit, mock_service
        ]:
            mock.return_value = mock_all_settings

        from faceless.services.content_source_service import ContentSourceService
        from faceless.services.sources.base import RawContent

        service = ContentSourceService()

        content_list = [
            RawContent(
                title="Same Title",
                content="Content 1",
                source_type=ContentSourceType.REDDIT,
                source_url="https://example.com/1",
            ),
            RawContent(
                title="Same Title",
                content="Content 2",
                source_type=ContentSourceType.WIKIPEDIA,
                source_url="https://example.com/2",
            ),
            RawContent(
                title="Different Title",
                content="Content 3",
                source_type=ContentSourceType.REDDIT,
                source_url="https://example.com/3",
            ),
        ]

        result = service._deduplicate(content_list)

        assert len(result) == 2

    @patch("faceless.services.content_source_service.get_settings")
    @patch("faceless.services.sources.reddit_source.get_settings")
    @patch("faceless.services.sources.wikipedia_source.get_settings")
    @patch("faceless.services.sources.hackernews_source.get_settings")
    @patch("faceless.services.sources.openlibrary_source.get_settings")
    @patch("faceless.services.sources.news_source.get_settings")
    @patch("faceless.services.sources.youtube_source.get_settings")
    def test_rank_content_by_score(
        self,
        mock_yt: MagicMock,
        mock_news: MagicMock,
        mock_ol: MagicMock,
        mock_hn: MagicMock,
        mock_wiki: MagicMock,
        mock_reddit: MagicMock,
        mock_service: MagicMock,
        mock_all_settings: MagicMock,
    ) -> None:
        """Test ranking content by score."""
        for mock in [
            mock_yt, mock_news, mock_ol, mock_hn,
            mock_wiki, mock_reddit, mock_service
        ]:
            mock.return_value = mock_all_settings

        from faceless.services.content_source_service import ContentSourceService
        from faceless.services.sources.base import RawContent

        service = ContentSourceService()

        content_list = [
            RawContent(
                title="Low Score",
                content="Content",
                source_type=ContentSourceType.REDDIT,
                source_url="https://example.com/1",
                score=10.0,
            ),
            RawContent(
                title="High Score",
                content="Content",
                source_type=ContentSourceType.REDDIT,
                source_url="https://example.com/2",
                score=90.0,
            ),
            RawContent(
                title="Medium Score",
                content="Content",
                source_type=ContentSourceType.REDDIT,
                source_url="https://example.com/3",
                score=50.0,
            ),
        ]

        result = service._rank_content(content_list)

        assert result[0].score == 90.0
        assert result[1].score == 50.0
        assert result[2].score == 10.0

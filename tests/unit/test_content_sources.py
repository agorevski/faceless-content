"""
Unit tests for content source service and source adapters.

Tests the multi-source content fetching functionality.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from faceless.core.enums import ContentSourceType, Niche
from faceless.services.sources.base import RawContent, SourceCapabilities

# =============================================================================
# RawContent Tests
# =============================================================================


class TestRawContent:
    """Tests for the RawContent dataclass."""

    def test_raw_content_creation(self) -> None:
        """Test creating a RawContent instance."""
        content = RawContent(
            title="Test Title",
            content="This is test content with enough words to pass validation.",
            source_type=ContentSourceType.REDDIT,
            source_url="https://reddit.com/test",
            source_id="abc123",
            author="test_author",
            score=75.0,
        )

        assert content.title == "Test Title"
        assert content.source_type == ContentSourceType.REDDIT
        assert content.score == 75.0
        assert content.author == "test_author"

    def test_word_count(self) -> None:
        """Test word count property."""
        content = RawContent(
            title="Test",
            content="One two three four five",
            source_type=ContentSourceType.REDDIT,
            source_url="https://example.com",
        )

        assert content.word_count == 5

    def test_has_sufficient_content(self) -> None:
        """Test content sufficiency check."""
        short_content = RawContent(
            title="Test",
            content="Too short",
            source_type=ContentSourceType.REDDIT,
            source_url="https://example.com",
        )
        assert not short_content.has_sufficient_content

        # Create content with 100+ words
        long_text = " ".join(["word"] * 150)
        long_content = RawContent(
            title="Test",
            content=long_text,
            source_type=ContentSourceType.REDDIT,
            source_url="https://example.com",
        )
        assert long_content.has_sufficient_content

    def test_to_dict(self) -> None:
        """Test serialization to dictionary."""
        content = RawContent(
            title="Test Title",
            content="Test content",
            source_type=ContentSourceType.WIKIPEDIA,
            source_url="https://wikipedia.org/test",
            source_id="wiki123",
            author="wiki_author",
            score=85.0,
        )

        data = content.to_dict()

        assert data["title"] == "Test Title"
        assert data["source_type"] == "wikipedia"
        assert data["source_id"] == "wiki123"
        assert "fetched_at" in data


# =============================================================================
# SourceCapabilities Tests
# =============================================================================


class TestSourceCapabilities:
    """Tests for the SourceCapabilities dataclass."""

    def test_default_capabilities(self) -> None:
        """Test default capability values."""
        caps = SourceCapabilities()

        assert caps.supports_search is True
        assert caps.supports_trending is False
        assert caps.supports_pagination is True
        assert caps.requires_api_key is False
        assert caps.rate_limit_per_minute == 60

    def test_custom_capabilities(self) -> None:
        """Test custom capability values."""
        caps = SourceCapabilities(
            supports_search=False,
            supports_trending=True,
            requires_api_key=True,
            rate_limit_per_minute=30,
        )

        assert caps.supports_search is False
        assert caps.supports_trending is True
        assert caps.requires_api_key is True
        assert caps.rate_limit_per_minute == 30


# =============================================================================
# ContentSourceType Tests
# =============================================================================


class TestContentSourceType:
    """Tests for the ContentSourceType enum."""

    def test_all_source_types_exist(self) -> None:
        """Test that all expected source types exist."""
        expected_types = [
            "reddit",
            "wikipedia",
            "youtube",
            "news",
            "hacker_news",
            "open_library",
            "ai_generated",
        ]

        for source_type in expected_types:
            assert hasattr(ContentSourceType, source_type.upper())

    def test_display_names(self) -> None:
        """Test display names for source types."""
        assert ContentSourceType.REDDIT.display_name == "Reddit"
        assert ContentSourceType.WIKIPEDIA.display_name == "Wikipedia"
        assert ContentSourceType.HACKER_NEWS.display_name == "Hacker News"

    def test_requires_api_key(self) -> None:
        """Test API key requirements."""
        assert ContentSourceType.YOUTUBE.requires_api_key is True
        assert ContentSourceType.NEWS.requires_api_key is True
        assert ContentSourceType.REDDIT.requires_api_key is False
        assert ContentSourceType.WIKIPEDIA.requires_api_key is False


# =============================================================================
# RedditSource Tests
# =============================================================================


class TestRedditSource:
    """Tests for the Reddit content source."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings for testing."""
        settings = MagicMock()
        settings.content_sources.reddit_rate_limit = 60
        settings.content_sources.cache_ttl_seconds = 3600
        settings.content_sources.min_score = 50
        settings.reddit.user_agent = "Test/1.0"
        return settings

    @patch("faceless.services.sources.reddit_source.get_settings")
    def test_source_type(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test that source type is correct."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.reddit_source import RedditSource

        source = RedditSource()
        assert source.source_type == ContentSourceType.REDDIT

    @patch("faceless.services.sources.reddit_source.get_settings")
    def test_supports_all_niches(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test that Reddit supports all niches."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.reddit_source import RedditSource

        source = RedditSource()

        # Reddit should support all niches
        for niche in Niche:
            assert source.supports_niche(niche) is True

    @patch("faceless.services.sources.reddit_source.get_settings")
    def test_capabilities(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test Reddit source capabilities."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.reddit_source import RedditSource

        source = RedditSource()
        caps = source.capabilities

        assert caps.supports_search is True
        assert caps.supports_trending is True
        assert caps.requires_api_key is False


# =============================================================================
# WikipediaSource Tests
# =============================================================================


class TestWikipediaSource:
    """Tests for the Wikipedia content source."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings for testing."""
        settings = MagicMock()
        settings.content_sources.wikipedia_rate_limit = 200
        settings.content_sources.cache_ttl_seconds = 3600
        return settings

    @patch("faceless.services.sources.wikipedia_source.get_settings")
    def test_source_type(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test that source type is correct."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.wikipedia_source import WikipediaSource

        source = WikipediaSource()
        assert source.source_type == ContentSourceType.WIKIPEDIA

    @patch("faceless.services.sources.wikipedia_source.get_settings")
    def test_supports_educational_niches(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test that Wikipedia supports educational niches."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.wikipedia_source import WikipediaSource

        source = WikipediaSource()

        # Wikipedia should support these educational niches
        educational_niches = [
            Niche.HISTORY,
            Niche.PSYCHOLOGY_FACTS,
            Niche.MYTHOLOGY_FOLKLORE,
            Niche.GEOGRAPHY_FACTS,
            Niche.PHILOSOPHY,
        ]

        for niche in educational_niches:
            assert source.supports_niche(niche) is True


# =============================================================================
# HackerNewsSource Tests
# =============================================================================


class TestHackerNewsSource:
    """Tests for the Hacker News content source."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings for testing."""
        settings = MagicMock()
        settings.content_sources.hackernews_rate_limit = 60
        return settings

    @patch("faceless.services.sources.hackernews_source.get_settings")
    def test_source_type(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test that source type is correct."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.hackernews_source import HackerNewsSource

        source = HackerNewsSource()
        assert source.source_type == ContentSourceType.HACKER_NEWS

    @patch("faceless.services.sources.hackernews_source.get_settings")
    def test_supports_tech_niches(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test that HN supports tech niches."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.hackernews_source import HackerNewsSource

        source = HackerNewsSource()

        # HN should support tech niches
        assert source.supports_niche(Niche.TECH_GADGETS) is True
        assert source.supports_niche(Niche.AI_FUTURE_TECH) is True

        # HN should not support non-tech niches
        assert source.supports_niche(Niche.SCARY_STORIES) is False


# =============================================================================
# ContentSourceService Tests
# =============================================================================


class TestContentSourceService:
    """Tests for the main ContentSourceService orchestrator."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
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
    def test_get_available_sources(
        self,
        mock_yt: MagicMock,
        mock_news: MagicMock,
        mock_ol: MagicMock,
        mock_hn: MagicMock,
        mock_wiki: MagicMock,
        mock_reddit: MagicMock,
        mock_service: MagicMock,
        mock_settings: MagicMock,
    ) -> None:
        """Test getting available sources."""
        # Set all mocks to return the same settings
        for mock in [
            mock_yt,
            mock_news,
            mock_ol,
            mock_hn,
            mock_wiki,
            mock_reddit,
            mock_service,
        ]:
            mock.return_value = mock_settings

        from faceless.services.content_source_service import ContentSourceService

        service = ContentSourceService()
        available = service.get_available_sources()

        # Reddit, Wikipedia, HackerNews, OpenLibrary should be available (no API key needed)
        assert ContentSourceType.REDDIT in available
        assert ContentSourceType.WIKIPEDIA in available
        assert ContentSourceType.HACKER_NEWS in available
        assert ContentSourceType.OPEN_LIBRARY in available

        # YouTube and News require API keys (not configured in mock)
        assert ContentSourceType.YOUTUBE not in available
        assert ContentSourceType.NEWS not in available

    @patch("faceless.services.content_source_service.get_settings")
    @patch("faceless.services.sources.reddit_source.get_settings")
    @patch("faceless.services.sources.wikipedia_source.get_settings")
    @patch("faceless.services.sources.hackernews_source.get_settings")
    @patch("faceless.services.sources.openlibrary_source.get_settings")
    @patch("faceless.services.sources.news_source.get_settings")
    @patch("faceless.services.sources.youtube_source.get_settings")
    def test_get_sources_for_niche(
        self,
        mock_yt: MagicMock,
        mock_news: MagicMock,
        mock_ol: MagicMock,
        mock_hn: MagicMock,
        mock_wiki: MagicMock,
        mock_reddit: MagicMock,
        mock_service: MagicMock,
        mock_settings: MagicMock,
    ) -> None:
        """Test getting sources for a specific niche."""
        for mock in [
            mock_yt,
            mock_news,
            mock_ol,
            mock_hn,
            mock_wiki,
            mock_reddit,
            mock_service,
        ]:
            mock.return_value = mock_settings

        from faceless.services.content_source_service import ContentSourceService

        service = ContentSourceService()

        # Scary stories should prioritize Reddit
        scary_sources = service.get_sources_for_niche(Niche.SCARY_STORIES)
        assert ContentSourceType.REDDIT in scary_sources

        # History should prioritize Wikipedia
        history_sources = service.get_sources_for_niche(Niche.HISTORY)
        assert ContentSourceType.WIKIPEDIA in history_sources

        # Tech should include HackerNews
        tech_sources = service.get_sources_for_niche(Niche.TECH_GADGETS)
        assert ContentSourceType.HACKER_NEWS in tech_sources


# =============================================================================
# Text Cleaning Tests
# =============================================================================


class TestRedditTextCleaning:
    """Tests for Reddit text cleaning functions."""

    def test_clean_markdown_bold(self) -> None:
        """Test removing markdown bold formatting."""
        from faceless.services.sources.reddit_source import clean_reddit_text

        text = "This is **bold** text"
        cleaned = clean_reddit_text(text)
        assert cleaned == "This is bold text"

    def test_clean_markdown_italic(self) -> None:
        """Test removing markdown italic formatting."""
        from faceless.services.sources.reddit_source import clean_reddit_text

        text = "This is *italic* text"
        cleaned = clean_reddit_text(text)
        assert cleaned == "This is italic text"

    def test_clean_markdown_links(self) -> None:
        """Test removing markdown links but keeping text."""
        from faceless.services.sources.reddit_source import clean_reddit_text

        text = "Check out [this link](https://example.com) here"
        cleaned = clean_reddit_text(text)
        assert cleaned == "Check out this link here"

    def test_clean_html_entities(self) -> None:
        """Test converting HTML entities."""
        from faceless.services.sources.reddit_source import clean_reddit_text

        text = "Tom &amp; Jerry &lt;3 &gt;_&gt;"
        cleaned = clean_reddit_text(text)
        assert "&" in cleaned
        assert "<" in cleaned
        assert ">" in cleaned

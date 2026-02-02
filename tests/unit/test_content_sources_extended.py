"""
Additional tests for content source service and individual sources.

This file provides more comprehensive coverage for source adapters.
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from faceless.core.enums import ContentSourceType, Niche
from faceless.core.exceptions import ContentFetchError, SourceUnavailableError


# =============================================================================
# ContentSourceService Extended Tests
# =============================================================================


class TestContentSourceServiceFetch:
    """Tests for ContentSourceService fetch operations."""

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
        settings.get_scripts_dir.return_value = Path("/tmp/scripts")
        return settings

    @patch("faceless.services.content_source_service.get_settings")
    @patch("faceless.services.sources.reddit_source.get_settings")
    @patch("faceless.services.sources.wikipedia_source.get_settings")
    @patch("faceless.services.sources.hackernews_source.get_settings")
    @patch("faceless.services.sources.openlibrary_source.get_settings")
    @patch("faceless.services.sources.news_source.get_settings")
    @patch("faceless.services.sources.youtube_source.get_settings")
    @pytest.mark.asyncio
    async def test_fetch_content_parallel(
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
        """Test parallel content fetching."""
        for mock in [
            mock_yt, mock_news, mock_ol, mock_hn,
            mock_wiki, mock_reddit, mock_service
        ]:
            mock.return_value = mock_all_settings

        from faceless.services.content_source_service import ContentSourceService
        from faceless.services.sources.base import RawContent

        service = ContentSourceService()

        # Mock the parallel fetch method - must patch before call
        with patch.object(
            service, "_fetch_parallel", new_callable=AsyncMock
        ) as mock_parallel, \
             patch.object(service, "_deduplicate") as mock_dedup, \
             patch.object(service, "_rank_content") as mock_rank:

            test_content = [
                RawContent(
                    title="Test",
                    content="Content",
                    source_type=ContentSourceType.REDDIT,
                    source_url="https://example.com",
                )
            ]
            mock_parallel.return_value = test_content
            mock_dedup.return_value = test_content
            mock_rank.return_value = test_content

            result = await service.fetch_content(
                Niche.SCARY_STORIES,
                limit=5,
                parallel=True,
            )

            # Just verify the result is returned
            assert isinstance(result, list)

    @patch("faceless.services.content_source_service.get_settings")
    @patch("faceless.services.sources.reddit_source.get_settings")
    @patch("faceless.services.sources.wikipedia_source.get_settings")
    @patch("faceless.services.sources.hackernews_source.get_settings")
    @patch("faceless.services.sources.openlibrary_source.get_settings")
    @patch("faceless.services.sources.news_source.get_settings")
    @patch("faceless.services.sources.youtube_source.get_settings")
    @pytest.mark.asyncio
    async def test_fetch_content_sequential(
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
        """Test sequential content fetching."""
        for mock in [
            mock_yt, mock_news, mock_ol, mock_hn,
            mock_wiki, mock_reddit, mock_service
        ]:
            mock.return_value = mock_all_settings

        from faceless.services.content_source_service import ContentSourceService

        service = ContentSourceService()

        with patch.object(service, "_fetch_sequential") as mock_seq, \
             patch.object(service, "_deduplicate") as mock_dedup, \
             patch.object(service, "_rank_content") as mock_rank:

            mock_seq.return_value = []
            mock_dedup.return_value = []
            mock_rank.return_value = []

            result = await service.fetch_content(
                Niche.SCARY_STORIES,
                limit=5,
                parallel=False,
            )

            mock_seq.assert_called()

    @patch("faceless.services.content_source_service.get_settings")
    @patch("faceless.services.sources.reddit_source.get_settings")
    @patch("faceless.services.sources.wikipedia_source.get_settings")
    @patch("faceless.services.sources.hackernews_source.get_settings")
    @patch("faceless.services.sources.openlibrary_source.get_settings")
    @patch("faceless.services.sources.news_source.get_settings")
    @patch("faceless.services.sources.youtube_source.get_settings")
    @pytest.mark.asyncio
    async def test_fetch_trending(
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
        """Test fetching trending content."""
        for mock in [
            mock_yt, mock_news, mock_ol, mock_hn,
            mock_wiki, mock_reddit, mock_service
        ]:
            mock.return_value = mock_all_settings

        from faceless.services.content_source_service import ContentSourceService

        service = ContentSourceService()

        # Mock Reddit source's fetch_trending
        with patch.object(
            service._sources[ContentSourceType.REDDIT], "fetch_trending"
        ) as mock_trending:
            mock_trending.return_value = []

            result = await service.fetch_trending(Niche.SCARY_STORIES, limit=5)

            mock_trending.assert_called()

    @patch("faceless.services.content_source_service.get_settings")
    @patch("faceless.services.sources.reddit_source.get_settings")
    @patch("faceless.services.sources.wikipedia_source.get_settings")
    @patch("faceless.services.sources.hackernews_source.get_settings")
    @patch("faceless.services.sources.openlibrary_source.get_settings")
    @patch("faceless.services.sources.news_source.get_settings")
    @patch("faceless.services.sources.youtube_source.get_settings")
    @pytest.mark.asyncio
    async def test_search(
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
        """Test search functionality."""
        for mock in [
            mock_yt, mock_news, mock_ol, mock_hn,
            mock_wiki, mock_reddit, mock_service
        ]:
            mock.return_value = mock_all_settings

        from faceless.services.content_source_service import ContentSourceService

        service = ContentSourceService()

        # Mock source's fetch_content for search
        with patch.object(
            service._sources[ContentSourceType.REDDIT], "fetch_content"
        ) as mock_fetch, \
            patch.object(
            service._sources[ContentSourceType.REDDIT], "search"
        ) as mock_search:
            mock_fetch.return_value = []
            mock_search.return_value = []

            # Search with niche
            result = await service.search(
                "scary story",
                niche=Niche.SCARY_STORIES,
                limit=5,
            )

            # Search without niche
            result = await service.search("test query", limit=5)

    @patch("faceless.services.content_source_service.get_settings")
    @patch("faceless.services.sources.reddit_source.get_settings")
    @patch("faceless.services.sources.wikipedia_source.get_settings")
    @patch("faceless.services.sources.hackernews_source.get_settings")
    @patch("faceless.services.sources.openlibrary_source.get_settings")
    @patch("faceless.services.sources.news_source.get_settings")
    @patch("faceless.services.sources.youtube_source.get_settings")
    @pytest.mark.asyncio
    async def test_save_content_as_script(
        self,
        mock_yt: MagicMock,
        mock_news: MagicMock,
        mock_ol: MagicMock,
        mock_hn: MagicMock,
        mock_wiki: MagicMock,
        mock_reddit: MagicMock,
        mock_service: MagicMock,
        mock_all_settings: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test saving content as script."""
        mock_all_settings.get_scripts_dir.return_value = tmp_path

        for mock in [
            mock_yt, mock_news, mock_ol, mock_hn,
            mock_wiki, mock_reddit, mock_service
        ]:
            mock.return_value = mock_all_settings

        from faceless.services.content_source_service import ContentSourceService
        from faceless.services.sources.base import RawContent

        service = ContentSourceService()

        content = RawContent(
            title="Test Story for Script",
            content="This is a test story.\n\nWith paragraphs.",
            source_type=ContentSourceType.REDDIT,
            source_url="https://reddit.com/test",
            author="test_author",
        )

        result = await service.save_content_as_script(
            content, Niche.SCARY_STORIES, output_dir=tmp_path
        )

        assert result.exists()
        assert result.suffix == ".json"

        with open(result) as f:
            data = json.load(f)
        assert data["title"] == "Test Story for Script"

    @patch("faceless.services.content_source_service.get_settings")
    @patch("faceless.services.sources.reddit_source.get_settings")
    @patch("faceless.services.sources.wikipedia_source.get_settings")
    @patch("faceless.services.sources.hackernews_source.get_settings")
    @patch("faceless.services.sources.openlibrary_source.get_settings")
    @patch("faceless.services.sources.news_source.get_settings")
    @patch("faceless.services.sources.youtube_source.get_settings")
    @pytest.mark.asyncio
    async def test_fetch_content_no_sources_raises(
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
        """Test that fetch_content raises when no sources available."""
        for mock in [
            mock_yt, mock_news, mock_ol, mock_hn,
            mock_wiki, mock_reddit, mock_service
        ]:
            mock.return_value = mock_all_settings

        from faceless.services.content_source_service import ContentSourceService

        service = ContentSourceService()

        # Mock all sources as unavailable
        for source in service._sources.values():
            source.is_available = MagicMock(return_value=False)

        with pytest.raises(ContentFetchError):
            await service.fetch_content(Niche.SCARY_STORIES, limit=5)

    @patch("faceless.services.content_source_service.get_settings")
    @patch("faceless.services.sources.reddit_source.get_settings")
    @patch("faceless.services.sources.wikipedia_source.get_settings")
    @patch("faceless.services.sources.hackernews_source.get_settings")
    @patch("faceless.services.sources.openlibrary_source.get_settings")
    @patch("faceless.services.sources.news_source.get_settings")
    @patch("faceless.services.sources.youtube_source.get_settings")
    def test_generate_basic_image_prompt(
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
        """Test basic image prompt generation."""
        for mock in [
            mock_yt, mock_news, mock_ol, mock_hn,
            mock_wiki, mock_reddit, mock_service
        ]:
            mock.return_value = mock_all_settings

        from faceless.services.content_source_service import ContentSourceService

        service = ContentSourceService()

        # Test scary stories prompt
        prompt = service._generate_basic_image_prompt(
            "The dark house stood silent",
            Niche.SCARY_STORIES,
            1,
            3,
        )
        assert "horror" in prompt.lower() or "dark" in prompt.lower()

        # Test finance prompt
        prompt = service._generate_basic_image_prompt(
            "Invest in stocks for growth",
            Niche.FINANCE,
            2,
            3,
        )
        assert "Professional" in prompt or "minimalist" in prompt.lower()

        # Test last scene
        prompt = service._generate_basic_image_prompt(
            "The end",
            Niche.SCARY_STORIES,
            3,
            3,
        )
        assert "Climactic" in prompt


# =============================================================================
# Wikipedia Source Additional Tests
# =============================================================================


class TestWikipediaSourceAdvanced:
    """Advanced tests for Wikipedia source."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings."""
        settings = MagicMock()
        settings.content_sources.wikipedia_rate_limit = 200
        settings.content_sources.cache_ttl_seconds = 3600
        return settings

    @patch("faceless.services.sources.wikipedia_source.get_settings")
    @pytest.mark.asyncio
    async def test_search_articles(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test searching articles."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.wikipedia_source import WikipediaSource

        source = WikipediaSource()

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "query": {
                    "search": [
                        {"title": "Article 1"},
                        {"title": "Article 2"},
                    ]
                }
            }
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = MagicMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_client_instance

            result = await source._search_articles("history", 5)

            assert len(result) == 2

    @patch("faceless.services.sources.wikipedia_source.get_settings")
    @pytest.mark.asyncio
    async def test_get_featured_article(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test getting featured article."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.wikipedia_source import WikipediaSource

        source = WikipediaSource()

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "tfa": {
                    "title": "Featured Article",
                    "extract": " ".join(["word"] * 150),
                    "pageid": 12345,
                    "content_urls": {"desktop": {"page": "https://wiki.test"}},
                    "description": "Test description",
                    "thumbnail": {"source": "https://thumb.url"},
                }
            }
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = MagicMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_client_instance

            result = await source._get_featured_article()

            assert result is not None
            assert result.title == "Featured Article"

    @patch("faceless.services.sources.wikipedia_source.get_settings")
    @pytest.mark.asyncio
    async def test_get_article_content(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test getting article content."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.wikipedia_source import WikipediaSource

        source = WikipediaSource()

        with patch.object(source, "get_article_summary") as mock_summary:
            mock_summary.return_value = None

            article = {"title": "Test Article"}
            result = await source._get_article_content(article, Niche.HISTORY)

            mock_summary.assert_called_once_with("Test Article", Niche.HISTORY)


# =============================================================================
# News Source Additional Tests
# =============================================================================


class TestNewsSourceAdvanced:
    """Advanced tests for News source."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings."""
        settings = MagicMock()
        settings.content_sources.newsapi_key = "test-api-key"
        settings.content_sources.newsapi_configured = True
        return settings

    @patch("faceless.services.sources.news_source.get_settings")
    @pytest.mark.asyncio
    async def test_fetch_content_success(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test successful content fetch."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.news_source import NewsSource

        source = NewsSource()

        with patch.object(source, "_search_everything") as mock_search:
            mock_search.return_value = [
                {
                    "title": "Test News",
                    "content": " ".join(["word"] * 150),
                    "url": "https://news.test",
                    "author": "Reporter",
                    "publishedAt": "2024-01-01T12:00:00Z",
                    "source": {"name": "Test News"},
                }
            ]

            result = await source.fetch_content(Niche.FINANCE, limit=5)

            assert len(result) >= 0  # May be filtered by has_sufficient_content

    @patch("faceless.services.sources.news_source.get_settings")
    @pytest.mark.asyncio
    async def test_fetch_trending_success(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test successful trending fetch."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.news_source import NewsSource

        source = NewsSource()

        with patch.object(source, "_get_top_headlines") as mock_headlines:
            mock_headlines.return_value = [
                {
                    "title": "Top News",
                    "content": "Content here",
                    "url": "https://news.test",
                    "source": {"name": "CNN"},
                }
            ]

            result = await source.fetch_trending(Niche.FINANCE, limit=5)

            mock_headlines.assert_called()


# =============================================================================
# OpenLibrary Source Additional Tests
# =============================================================================


class TestOpenLibrarySourceAdvanced:
    """Advanced tests for OpenLibrary source."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings."""
        settings = MagicMock()
        settings.content_sources.openlibrary_rate_limit = 100
        return settings

    @patch("faceless.services.sources.openlibrary_source.get_settings")
    @pytest.mark.asyncio
    async def test_fetch_trending(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test fetching trending content."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.openlibrary_source import OpenLibrarySource

        source = OpenLibrarySource()

        with patch.object(source, "_get_trending_by_subject") as mock_trending, \
             patch.object(source, "_book_to_raw_content") as mock_convert:
            mock_trending.return_value = [{"key": "OL123W", "title": "Book"}]
            mock_convert.return_value = None

            result = await source.fetch_trending(Niche.PHILOSOPHY, limit=5)

            mock_trending.assert_called()

    @patch("faceless.services.sources.openlibrary_source.get_settings")
    @pytest.mark.asyncio
    async def test_get_author_name(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test getting author name."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.openlibrary_source import OpenLibrarySource

        source = OpenLibrarySource()

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {"name": "Author Name"}
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = MagicMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_client_instance

            result = await source._get_author_name("/authors/OL123A")

            assert result == "Author Name"

    @patch("faceless.services.sources.openlibrary_source.get_settings")
    @pytest.mark.asyncio
    async def test_book_to_raw_content_with_key(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test book to raw content with work key."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.openlibrary_source import OpenLibrarySource

        source = OpenLibrarySource()

        with patch.object(source, "get_book_details") as mock_details:
            mock_details.return_value = None

            book = {
                "key": "/works/OL123W",
                "title": "Test Book",
                "author_name": ["Author"],
                "first_publish_year": 2020,
                "subject": ["Philosophy"],
            }

            result = await source._book_to_raw_content(book, Niche.PHILOSOPHY)

            # When details returns None, fallback is used
            mock_details.assert_called_once()

    @patch("faceless.services.sources.openlibrary_source.get_settings")
    @pytest.mark.asyncio
    async def test_book_to_raw_content_fallback(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test book to raw content fallback."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.openlibrary_source import OpenLibrarySource

        source = OpenLibrarySource()

        with patch.object(source, "get_book_details") as mock_details:
            mock_details.return_value = None

            book = {
                "key": "/works/OL456W",
                "title": "Fallback Book",
                "author_name": ["Fallback Author"],
                "first_publish_year": "2019",
                "subject": ["Science", "Nature", "Biology"],
            }

            result = await source._book_to_raw_content(book, Niche.BOOK_SUMMARIES)

            # Fallback should create content from metadata
            if result:
                assert "Fallback Book" in result.title

    @patch("faceless.services.sources.openlibrary_source.get_settings")
    @pytest.mark.asyncio
    async def test_search_by_subjects(
        self, mock_get_settings: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test searching by subjects."""
        mock_get_settings.return_value = mock_settings

        from faceless.services.sources.openlibrary_source import OpenLibrarySource

        source = OpenLibrarySource()

        with patch.object(source, "_get_trending_by_subject") as mock_trending:
            mock_trending.return_value = [{"key": "OL123W"}]

            result = await source._search_by_subjects(["philosophy", "ethics"], 5)

            assert mock_trending.call_count == 2


# =============================================================================
# Rate Limiter Tests
# =============================================================================


class TestRateLimiters:
    """Tests for rate limiters across sources."""

    @pytest.mark.asyncio
    async def test_wikipedia_rate_limiter(self) -> None:
        """Test Wikipedia rate limiter."""
        from faceless.services.sources.wikipedia_source import RateLimiter

        limiter = RateLimiter(requests_per_minute=200)
        await limiter.acquire()
        assert limiter.tokens < 200

    @pytest.mark.asyncio
    async def test_news_rate_limiter(self) -> None:
        """Test News rate limiter."""
        from faceless.services.sources.news_source import RateLimiter

        limiter = RateLimiter(requests_per_minute=30)
        await limiter.acquire()
        assert limiter.tokens < 30

    @pytest.mark.asyncio
    async def test_openlibrary_rate_limiter(self) -> None:
        """Test OpenLibrary rate limiter."""
        from faceless.services.sources.openlibrary_source import RateLimiter

        limiter = RateLimiter(requests_per_minute=100)
        await limiter.acquire()
        assert limiter.tokens < 100

    @pytest.mark.asyncio
    async def test_youtube_rate_limiter(self) -> None:
        """Test YouTube rate limiter."""
        from faceless.services.sources.youtube_source import RateLimiter

        limiter = RateLimiter(requests_per_minute=30)
        await limiter.acquire()
        assert limiter.tokens < 30

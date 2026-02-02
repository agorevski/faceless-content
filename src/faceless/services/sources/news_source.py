"""
News content source adapter.

Fetches news articles from NewsAPI (with API key) or GNews (free tier).
Best for current events, finance, tech, and celebrity niches.
"""

import asyncio
import contextlib
import time
from datetime import datetime, timedelta
from typing import Any

import httpx

from faceless.config import get_settings
from faceless.core.enums import ContentSourceType, Niche
from faceless.core.exceptions import ContentFetchError, SourceUnavailableError
from faceless.services.sources.base import (
    ContentSource,
    RawContent,
    SourceCapabilities,
)

# Niches that news sources are good for
NEWS_SUPPORTED_NICHES = {
    Niche.FINANCE,
    Niche.TECH_GADGETS,
    Niche.AI_FUTURE_TECH,
    Niche.CELEBRITY_NET_WORTH,
    Niche.TRUE_CRIME,
    Niche.HEALTH_WELLNESS,
    Niche.SPACE_ASTRONOMY,
}

# Keywords for each niche when searching news
NICHE_KEYWORDS: dict[Niche, list[str]] = {
    Niche.FINANCE: [
        "stock market",
        "economy",
        "investing",
        "cryptocurrency",
        "federal reserve",
    ],
    Niche.TECH_GADGETS: [
        "technology",
        "gadgets",
        "smartphone",
        "Apple",
        "Google",
        "Microsoft",
    ],
    Niche.AI_FUTURE_TECH: [
        "artificial intelligence",
        "ChatGPT",
        "machine learning",
        "OpenAI",
        "robotics",
    ],
    Niche.CELEBRITY_NET_WORTH: [
        "celebrity",
        "billionaire",
        "net worth",
        "richest",
        "Hollywood",
    ],
    Niche.TRUE_CRIME: [
        "crime",
        "murder",
        "investigation",
        "arrest",
        "trial",
    ],
    Niche.HEALTH_WELLNESS: [
        "health",
        "medicine",
        "wellness",
        "fitness",
        "nutrition",
    ],
    Niche.SPACE_ASTRONOMY: [
        "NASA",
        "SpaceX",
        "space",
        "astronomy",
        "Mars",
        "telescope",
    ],
}


class RateLimiter:
    """Simple token bucket rate limiter."""

    def __init__(self, requests_per_minute: int = 30) -> None:
        self.requests_per_minute = requests_per_minute
        self.tokens: float = float(requests_per_minute)
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire a token, waiting if necessary."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            refill = elapsed * (self.requests_per_minute / 60.0)
            self.tokens = min(float(self.requests_per_minute), self.tokens + refill)
            self.last_refill = now

            if self.tokens < 1:
                wait_time = (1 - self.tokens) / (self.requests_per_minute / 60.0)
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


class NewsSource(ContentSource):
    """
    News content source adapter.

    Fetches news from NewsAPI.org (requires API key) or falls back
    to alternative free sources.

    Features:
    - NewsAPI.org integration (100 requests/day free)
    - Keyword-based search by niche
    - Trending/top headlines
    - Date range filtering

    Example:
        >>> source = NewsSource()
        >>> if source.is_available():
        ...     content = await source.fetch_content(Niche.TECH_GADGETS, limit=10)
    """

    NEWSAPI_URL = "https://newsapi.org/v2"

    def __init__(self) -> None:
        """Initialize News source."""
        settings = get_settings()
        self._settings = settings.content_sources
        self._api_key = self._settings.newsapi_key
        self._rate_limiter = RateLimiter(30)  # Conservative for free tier
        self._timeout = httpx.Timeout(30.0)

    @property
    def source_type(self) -> ContentSourceType:
        """Return the source type."""
        return ContentSourceType.NEWS

    @property
    def capabilities(self) -> SourceCapabilities:
        """Return source capabilities."""
        return SourceCapabilities(
            supports_search=True,
            supports_trending=True,
            supports_pagination=True,
            requires_api_key=True,
            rate_limit_per_minute=30,
            max_results_per_request=100,
        )

    def is_available(self) -> bool:
        """Check if NewsAPI is configured."""
        return self._settings.newsapi_configured

    def supports_niche(self, niche: Niche) -> bool:
        """Check if this source supports the given niche."""
        return niche in NEWS_SUPPORTED_NICHES and self.is_available()

    async def fetch_content(
        self,
        niche: Niche,
        query: str | None = None,
        limit: int = 10,
    ) -> list[RawContent]:
        """
        Fetch content from news sources for a niche.

        Args:
            niche: Content niche to fetch
            query: Optional search query
            limit: Maximum number of articles to fetch

        Returns:
            List of RawContent items

        Raises:
            SourceUnavailableError: If API key is not configured
            ContentFetchError: If fetching fails
        """
        if not self.is_available():
            raise SourceUnavailableError(
                "NewsAPI key not configured",
                source="news",
                reason="missing_api_key",
            )

        self.logger.info(
            "Fetching news content",
            niche=niche.value,
            query=query,
            limit=limit,
        )

        # Build search query
        if query:
            search_terms = [query]
        else:
            search_terms = NICHE_KEYWORDS.get(niche, [niche.display_name])

        # Combine terms with OR for broader results
        combined_query = " OR ".join(search_terms[:3])

        articles = await self._search_everything(combined_query, limit)

        # Convert to RawContent
        all_content: list[RawContent] = []
        for article in articles:
            content = self._article_to_raw_content(article, niche)
            if content and content.has_sufficient_content:
                all_content.append(content)

        self.logger.info(
            "News fetch complete",
            niche=niche.value,
            count=len(all_content),
        )

        return all_content[:limit]

    async def fetch_trending(
        self,
        niche: Niche,
        limit: int = 10,
    ) -> list[RawContent]:
        """Fetch top headlines (trending news)."""
        if not self.is_available():
            raise SourceUnavailableError(
                "NewsAPI key not configured",
                source="news",
                reason="missing_api_key",
            )

        # Map niche to NewsAPI category
        category_map = {
            Niche.FINANCE: "business",
            Niche.TECH_GADGETS: "technology",
            Niche.AI_FUTURE_TECH: "technology",
            Niche.HEALTH_WELLNESS: "health",
            Niche.SPACE_ASTRONOMY: "science",
            Niche.CELEBRITY_NET_WORTH: "entertainment",
        }

        category = category_map.get(niche, "general")
        articles = await self._get_top_headlines(category, limit)

        all_content: list[RawContent] = []
        for article in articles:
            content = self._article_to_raw_content(article, niche)
            if content:
                all_content.append(content)

        return all_content[:limit]

    async def _search_everything(
        self,
        query: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Search all news articles."""
        await self._rate_limiter.acquire()

        # Search from past week for freshness
        from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        url = f"{self.NEWSAPI_URL}/everything"
        params: dict[str, str | int] = {
            "q": query,
            "from": from_date,
            "sortBy": "relevancy",
            "pageSize": min(limit, 100),
            "language": "en",
        }
        headers = {"X-Api-Key": self._api_key}

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()

                if data.get("status") != "ok":
                    raise ContentFetchError(
                        f"NewsAPI error: {data.get('message', 'Unknown error')}",
                        source="news",
                    )

                result: list[dict[str, Any]] = data.get("articles", [])
                return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise SourceUnavailableError(
                    "NewsAPI key is invalid",
                    source="news",
                    reason="invalid_api_key",
                ) from e
            if e.response.status_code == 429:
                raise ContentFetchError(
                    "NewsAPI rate limit exceeded",
                    source="news",
                    status_code=429,
                ) from e
            raise ContentFetchError(
                f"NewsAPI error: {e.response.status_code}",
                source="news",
                status_code=e.response.status_code,
            ) from e
        except httpx.RequestError as e:
            raise ContentFetchError(
                f"News request failed: {e}",
                source="news",
            ) from e

    async def _get_top_headlines(
        self,
        category: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Get top headlines for a category."""
        await self._rate_limiter.acquire()

        url = f"{self.NEWSAPI_URL}/top-headlines"
        params: dict[str, str | int] = {
            "category": category,
            "country": "us",
            "pageSize": min(limit, 100),
        }
        headers = {"X-Api-Key": self._api_key}

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()

                if data.get("status") != "ok":
                    return []

                result: list[dict[str, Any]] = data.get("articles", [])
                return result

        except (httpx.HTTPStatusError, httpx.RequestError):
            return []

    def _article_to_raw_content(
        self,
        article: dict[str, Any],
        niche: Niche,
    ) -> RawContent | None:
        """Convert a news article to RawContent."""
        title = article.get("title", "")
        content = article.get("content", "") or article.get("description", "")

        if not title or not content:
            return None

        # NewsAPI truncates content with "[+N chars]" - clean it
        content = content.split("[+")[0].strip()

        # Parse published date
        published_str = article.get("publishedAt", "")
        published_at = None
        if published_str:
            with contextlib.suppress(ValueError):
                published_at = datetime.fromisoformat(
                    published_str.replace("Z", "+00:00")
                )

        # Score based on source reputation and recency
        source_name = article.get("source", {}).get("name", "")
        base_score = 70.0

        # Boost major sources
        major_sources = [
            "Reuters",
            "BBC",
            "CNN",
            "The Guardian",
            "Bloomberg",
            "CNBC",
            "TechCrunch",
            "Wired",
        ]
        if any(ms.lower() in source_name.lower() for ms in major_sources):
            base_score = 85.0

        return RawContent(
            title=title,
            content=content,
            source_type=ContentSourceType.NEWS,
            source_url=article.get("url", ""),
            source_id=article.get("url", ""),  # Use URL as ID
            author=article.get("author"),
            published_at=published_at,
            score=base_score,
            metadata={
                "niche": niche.value,
                "source_name": source_name,
                "description": article.get("description", ""),
                "image_url": article.get("urlToImage"),
            },
        )

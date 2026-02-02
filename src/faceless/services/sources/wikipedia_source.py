"""
Wikipedia content source adapter.

Fetches content from Wikipedia using the REST API.
Best for factual, educational niches like history, science, geography.
"""

import asyncio
import re
import time
from datetime import datetime
from typing import Any

import httpx

from faceless.config import get_settings
from faceless.core.enums import ContentSourceType, Niche
from faceless.core.exceptions import ContentFetchError
from faceless.services.sources.base import (
    ContentSource,
    RawContent,
    SourceCapabilities,
)

# Niches that Wikipedia is particularly good for
WIKIPEDIA_PRIORITY_NICHES = {
    Niche.HISTORY,
    Niche.PSYCHOLOGY_FACTS,
    Niche.SPACE_ASTRONOMY,
    Niche.ANIMAL_FACTS,
    Niche.MYTHOLOGY_FOLKLORE,
    Niche.GEOGRAPHY_FACTS,
    Niche.PHILOSOPHY,
    Niche.TRUE_CRIME,
    Niche.UNSOLVED_MYSTERIES,
    Niche.CONSPIRACY_MYSTERIES,
}

# Search terms for each niche to find relevant Wikipedia articles
NICHE_SEARCH_TERMS: dict[Niche, list[str]] = {
    Niche.HISTORY: [
        "historical event",
        "ancient civilization",
        "world war",
        "historical figure",
    ],
    Niche.PSYCHOLOGY_FACTS: [
        "psychology",
        "cognitive bias",
        "mental health",
        "psychological phenomenon",
    ],
    Niche.SPACE_ASTRONOMY: ["astronomy", "planet", "galaxy", "space exploration"],
    Niche.ANIMAL_FACTS: ["animal behavior", "endangered species", "marine life"],
    Niche.MYTHOLOGY_FOLKLORE: ["mythology", "folklore", "legend", "ancient deity"],
    Niche.GEOGRAPHY_FACTS: [
        "geography",
        "natural wonder",
        "country",
        "geographical feature",
    ],
    Niche.PHILOSOPHY: ["philosophy", "philosopher", "ethics", "metaphysics"],
    Niche.TRUE_CRIME: ["murder case", "serial killer", "crime", "criminal case"],
    Niche.UNSOLVED_MYSTERIES: ["unsolved mystery", "disappearance", "unexplained"],
    Niche.CONSPIRACY_MYSTERIES: ["conspiracy theory", "mystery", "unexplained event"],
    Niche.TECH_GADGETS: ["technology", "invention", "computer science"],
    Niche.AI_FUTURE_TECH: ["artificial intelligence", "robotics", "future technology"],
    Niche.HEALTH_WELLNESS: ["health", "medicine", "disease", "nutrition"],
}


class RateLimiter:
    """Simple token bucket rate limiter."""

    def __init__(self, requests_per_minute: int = 200) -> None:
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


def clean_wikipedia_text(text: str) -> str:
    """Clean Wikipedia article text for narration."""
    # Remove citation markers like [1], [2], [citation needed]
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"\[citation needed\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\[.*?\]", "", text)

    # Remove disambiguation notices
    text = re.sub(r"For other uses.*?\.", "", text)
    text = re.sub(r"This article is about.*?\.", "", text)

    # Clean up whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)

    return text.strip()


class WikipediaSource(ContentSource):
    """
    Wikipedia content source adapter.

    Fetches content from Wikipedia using the REST API.
    Excellent for factual, educational content.

    Features:
    - Summary extraction
    - Full article fetching
    - Random article discovery
    - Featured article access
    - Search by keyword

    Example:
        >>> source = WikipediaSource()
        >>> content = await source.fetch_content(Niche.HISTORY, limit=5)
    """

    BASE_URL = "https://en.wikipedia.org/api/rest_v1"
    API_URL = "https://en.wikipedia.org/w/api.php"

    def __init__(self) -> None:
        """Initialize Wikipedia source."""
        settings = get_settings()
        self._settings = settings.content_sources
        self._rate_limiter = RateLimiter(self._settings.wikipedia_rate_limit)
        self._timeout = httpx.Timeout(30.0)
        self._cache: dict[str, tuple[float, list[RawContent]]] = {}

    @property
    def source_type(self) -> ContentSourceType:
        """Return the source type."""
        return ContentSourceType.WIKIPEDIA

    @property
    def capabilities(self) -> SourceCapabilities:
        """Return source capabilities."""
        return SourceCapabilities(
            supports_search=True,
            supports_trending=True,  # Via featured/random articles
            supports_pagination=True,
            requires_api_key=False,
            rate_limit_per_minute=self._settings.wikipedia_rate_limit,
            max_results_per_request=50,
        )

    def supports_niche(self, niche: Niche) -> bool:
        """Check if this source supports the given niche."""
        # Wikipedia supports most educational/factual niches
        return niche in NICHE_SEARCH_TERMS or niche in WIKIPEDIA_PRIORITY_NICHES

    async def fetch_content(
        self,
        niche: Niche,
        query: str | None = None,
        limit: int = 10,
    ) -> list[RawContent]:
        """
        Fetch content from Wikipedia for a niche.

        Args:
            niche: Content niche to fetch
            query: Optional search query
            limit: Maximum number of articles to fetch

        Returns:
            List of RawContent items
        """
        self.logger.info(
            "Fetching Wikipedia content",
            niche=niche.value,
            query=query,
            limit=limit,
        )

        if query:
            # Use provided query
            search_terms = [query]
        else:
            # Use niche-specific search terms
            search_terms = NICHE_SEARCH_TERMS.get(niche, [niche.display_name])

        all_content: list[RawContent] = []
        articles_per_term = max(1, limit // len(search_terms) + 1)

        for term in search_terms:
            try:
                articles = await self._search_articles(term, articles_per_term)
                for article in articles:
                    content = await self._get_article_content(article, niche)
                    if content and content.has_sufficient_content:
                        all_content.append(content)
                        if len(all_content) >= limit:
                            break
            except ContentFetchError as e:
                self.logger.warning("Wikipedia search failed", term=term, error=str(e))
                continue

            if len(all_content) >= limit:
                break

        self.logger.info(
            "Wikipedia fetch complete",
            niche=niche.value,
            count=len(all_content),
        )

        return all_content[:limit]

    async def fetch_trending(
        self,
        niche: Niche,
        limit: int = 10,
    ) -> list[RawContent]:
        """Fetch trending/featured content from Wikipedia."""
        # Get today's featured article and random articles
        content: list[RawContent] = []

        # Get featured article
        try:
            featured = await self._get_featured_article()
            if featured:
                content.append(featured)
        except ContentFetchError:
            pass

        # Fill with random articles related to niche
        remaining = limit - len(content)
        if remaining > 0:
            search_terms = NICHE_SEARCH_TERMS.get(niche, [niche.display_name])
            random_content = await self.fetch_content(
                niche, query=search_terms[0], limit=remaining
            )
            content.extend(random_content)

        return content[:limit]

    async def get_article_summary(self, title: str, niche: Niche) -> RawContent | None:
        """Get a summary of a specific Wikipedia article."""
        await self._rate_limiter.acquire()

        url = f"{self.BASE_URL}/page/summary/{title}"
        headers = {"User-Agent": "FacelessContent/1.0 (Educational Project)"}

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

                if data.get("type") == "disambiguation":
                    return None

                return RawContent(
                    title=data.get("title", title),
                    content=clean_wikipedia_text(data.get("extract", "")),
                    source_type=ContentSourceType.WIKIPEDIA,
                    source_url=data.get("content_urls", {})
                    .get("desktop", {})
                    .get("page", ""),
                    source_id=str(data.get("pageid", "")),
                    published_at=None,
                    score=75.0,  # Wikipedia is high quality
                    metadata={
                        "niche": niche.value,
                        "description": data.get("description", ""),
                        "thumbnail": data.get("thumbnail", {}).get("source", ""),
                    },
                )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise ContentFetchError(
                f"Wikipedia API error: {e.response.status_code}",
                source="wikipedia",
                status_code=e.response.status_code,
            ) from e
        except httpx.RequestError as e:
            raise ContentFetchError(
                f"Wikipedia request failed: {e}",
                source="wikipedia",
            ) from e

    async def _search_articles(
        self,
        query: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Search Wikipedia for articles matching a query."""
        await self._rate_limiter.acquire()

        params: dict[str, str | int] = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "srprop": "snippet|titlesnippet",
        }
        headers = {"User-Agent": "FacelessContent/1.0 (Educational Project)"}

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(
                    self.API_URL, params=params, headers=headers
                )
                response.raise_for_status()
                data = response.json()
                result: list[dict[str, Any]] = data.get("query", {}).get("search", [])
                return result

        except httpx.HTTPStatusError as e:
            raise ContentFetchError(
                f"Wikipedia search error: {e.response.status_code}",
                source="wikipedia",
                status_code=e.response.status_code,
            ) from e
        except httpx.RequestError as e:
            raise ContentFetchError(
                f"Wikipedia search failed: {e}",
                source="wikipedia",
            ) from e

    async def _get_article_content(
        self,
        article: dict[str, Any],
        niche: Niche,
    ) -> RawContent | None:
        """Get full content for a search result article."""
        title = article.get("title", "")
        if not title:
            return None

        # Get summary via REST API (cleaner text)
        return await self.get_article_summary(title, niche)

    async def _get_featured_article(self) -> RawContent | None:
        """Get today's featured article."""
        await self._rate_limiter.acquire()

        today = datetime.now()
        url = f"{self.BASE_URL}/feed/featured/{today.year}/{today.month:02d}/{today.day:02d}"
        headers = {"User-Agent": "FacelessContent/1.0 (Educational Project)"}

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

                tfa = data.get("tfa")  # Today's featured article
                if not tfa:
                    return None

                return RawContent(
                    title=tfa.get("title", "Featured Article"),
                    content=clean_wikipedia_text(tfa.get("extract", "")),
                    source_type=ContentSourceType.WIKIPEDIA,
                    source_url=tfa.get("content_urls", {})
                    .get("desktop", {})
                    .get("page", ""),
                    source_id=str(tfa.get("pageid", "")),
                    published_at=datetime.now(),
                    score=95.0,  # Featured articles are premium quality
                    metadata={
                        "featured": True,
                        "description": tfa.get("description", ""),
                        "thumbnail": tfa.get("thumbnail", {}).get("source", ""),
                    },
                )

        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            self.logger.warning("Failed to fetch featured article", error=str(e))
            return None

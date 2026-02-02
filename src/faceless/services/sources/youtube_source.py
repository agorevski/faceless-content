"""
YouTube content source adapter.

Fetches video metadata and trending topics from YouTube Data API v3.
Requires API key but provides valuable competitive research data.
"""

import asyncio
import contextlib
import time
from datetime import datetime
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

# All niches can benefit from YouTube research
YOUTUBE_SUPPORTED_NICHES = set(Niche)

# Search queries for each niche to find competitor content
NICHE_SEARCH_QUERIES: dict[Niche, list[str]] = {
    Niche.SCARY_STORIES: ["scary stories", "horror stories", "creepypasta narration"],
    Niche.FINANCE: ["personal finance", "investing tips", "money advice"],
    Niche.LUXURY: ["luxury lifestyle", "expensive things", "billionaire lifestyle"],
    Niche.TRUE_CRIME: ["true crime documentary", "murder mystery", "crime story"],
    Niche.PSYCHOLOGY_FACTS: [
        "psychology facts",
        "mind tricks",
        "psychological phenomena",
    ],
    Niche.HISTORY: ["history documentary", "historical events", "ancient history"],
    Niche.MOTIVATION: ["motivation speech", "success mindset", "self improvement"],
    Niche.SPACE_ASTRONOMY: [
        "space documentary",
        "astronomy facts",
        "universe explained",
    ],
    Niche.CONSPIRACY_MYSTERIES: [
        "conspiracy theories",
        "unsolved mysteries",
        "strange events",
    ],
    Niche.ANIMAL_FACTS: ["animal facts", "nature documentary", "wildlife"],
    Niche.HEALTH_WELLNESS: ["health tips", "wellness advice", "fitness motivation"],
    Niche.RELATIONSHIP_ADVICE: ["relationship advice", "dating tips", "love advice"],
    Niche.TECH_GADGETS: ["tech review", "gadgets", "technology news"],
    Niche.LIFE_HACKS: ["life hacks", "tips and tricks", "productivity hacks"],
    Niche.MYTHOLOGY_FOLKLORE: [
        "mythology explained",
        "folklore stories",
        "ancient legends",
    ],
    Niche.UNSOLVED_MYSTERIES: [
        "unsolved mysteries",
        "cold cases",
        "unexplained events",
    ],
    Niche.GEOGRAPHY_FACTS: [
        "geography facts",
        "countries explained",
        "world geography",
    ],
    Niche.AI_FUTURE_TECH: ["AI news", "future technology", "artificial intelligence"],
    Niche.PHILOSOPHY: ["philosophy explained", "philosophical ideas", "deep thinking"],
    Niche.BOOK_SUMMARIES: ["book summary", "book review", "books explained"],
    Niche.CELEBRITY_NET_WORTH: [
        "celebrity net worth",
        "richest celebrities",
        "how rich",
    ],
    Niche.SURVIVAL_TIPS: ["survival tips", "wilderness survival", "prepper guide"],
    Niche.SLEEP_RELAXATION: ["sleep music", "relaxation", "calm stories"],
    Niche.NETFLIX_RECOMMENDATIONS: [
        "netflix review",
        "what to watch",
        "movie recommendations",
    ],
    Niche.MOCKUMENTARY_HOWMADE: ["how its made", "mockumentary", "parody documentary"],
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


class YouTubeSource(ContentSource):
    """
    YouTube content source adapter.

    Fetches video metadata from YouTube Data API v3.
    Requires API key (free quota: 10,000 units/day).

    Features:
    - Video search by keywords
    - Trending videos
    - Video metadata extraction
    - Competitor content research

    Note:
        This source provides video metadata for research purposes.
        The content is video titles and descriptions, useful for
        understanding what topics perform well.

    Example:
        >>> source = YouTubeSource()
        >>> if source.is_available():
        ...     content = await source.fetch_content(Niche.SCARY_STORIES, limit=10)
    """

    API_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(self) -> None:
        """Initialize YouTube source."""
        settings = get_settings()
        self._settings = settings.content_sources
        self._api_key = self._settings.youtube_api_key
        self._rate_limiter = RateLimiter(30)  # Conservative
        self._timeout = httpx.Timeout(30.0)

    @property
    def source_type(self) -> ContentSourceType:
        """Return the source type."""
        return ContentSourceType.YOUTUBE

    @property
    def capabilities(self) -> SourceCapabilities:
        """Return source capabilities."""
        return SourceCapabilities(
            supports_search=True,
            supports_trending=True,
            supports_pagination=True,
            requires_api_key=True,
            rate_limit_per_minute=30,
            max_results_per_request=50,
        )

    def is_available(self) -> bool:
        """Check if YouTube API is configured."""
        return self._settings.youtube_configured

    def supports_niche(self, niche: Niche) -> bool:
        """Check if this source supports the given niche."""
        return niche in YOUTUBE_SUPPORTED_NICHES and self.is_available()

    async def fetch_content(
        self,
        niche: Niche,
        query: str | None = None,
        limit: int = 10,
    ) -> list[RawContent]:
        """
        Fetch video metadata from YouTube for a niche.

        Args:
            niche: Content niche to fetch
            query: Optional search query
            limit: Maximum number of videos to fetch

        Returns:
            List of RawContent items (video metadata)

        Raises:
            SourceUnavailableError: If API key is not configured
            ContentFetchError: If fetching fails
        """
        if not self.is_available():
            raise SourceUnavailableError(
                "YouTube API key not configured",
                source="youtube",
                reason="missing_api_key",
            )

        self.logger.info(
            "Fetching YouTube content",
            niche=niche.value,
            query=query,
            limit=limit,
        )

        # Build search query
        if query:
            search_query = query
        else:
            queries = NICHE_SEARCH_QUERIES.get(niche, [niche.display_name])
            search_query = queries[0]  # Use primary query

        videos = await self._search_videos(search_query, limit)

        # Convert to RawContent
        all_content: list[RawContent] = []
        for video in videos:
            content = self._video_to_raw_content(video, niche)
            if content:
                all_content.append(content)

        self.logger.info(
            "YouTube fetch complete",
            niche=niche.value,
            count=len(all_content),
        )

        return all_content[:limit]

    async def fetch_trending(
        self,
        niche: Niche,
        limit: int = 10,
    ) -> list[RawContent]:
        """Fetch trending videos."""
        if not self.is_available():
            raise SourceUnavailableError(
                "YouTube API key not configured",
                source="youtube",
                reason="missing_api_key",
            )

        # YouTube trending doesn't support niche filtering well
        # So we search with "trending" + niche terms
        queries = NICHE_SEARCH_QUERIES.get(niche, [niche.display_name])
        search_query = f"{queries[0]} 2024"  # Add year for freshness

        return await self.fetch_content(niche, query=search_query, limit=limit)

    async def get_video_details(self, video_id: str) -> dict[str, Any] | None:
        """Get detailed information about a specific video."""
        await self._rate_limiter.acquire()

        params = {
            "key": self._api_key,
            "id": video_id,
            "part": "snippet,statistics,contentDetails",
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(f"{self.API_URL}/videos", params=params)
                response.raise_for_status()
                data = response.json()

                items = data.get("items", [])
                return items[0] if items else None

        except (httpx.HTTPStatusError, httpx.RequestError):
            return None

    async def _search_videos(
        self,
        query: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Search for videos by query."""
        await self._rate_limiter.acquire()

        params: dict[str, str | int] = {
            "key": self._api_key,
            "q": query,
            "part": "snippet",
            "type": "video",
            "maxResults": min(limit, 50),
            "order": "relevance",
            "relevanceLanguage": "en",
            "safeSearch": "moderate",
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(f"{self.API_URL}/search", params=params)
                response.raise_for_status()
                data = response.json()

                if "error" in data:
                    error_msg = data["error"].get("message", "Unknown error")
                    raise ContentFetchError(
                        f"YouTube API error: {error_msg}",
                        source="youtube",
                    )

                result: list[dict[str, Any]] = data.get("items", [])
                return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                raise SourceUnavailableError(
                    "YouTube API quota exceeded or key invalid",
                    source="youtube",
                    reason="quota_or_key_issue",
                ) from e
            raise ContentFetchError(
                f"YouTube API error: {e.response.status_code}",
                source="youtube",
                status_code=e.response.status_code,
            ) from e
        except httpx.RequestError as e:
            raise ContentFetchError(
                f"YouTube request failed: {e}",
                source="youtube",
            ) from e

    def _video_to_raw_content(
        self,
        video: dict[str, Any],
        niche: Niche,
    ) -> RawContent | None:
        """Convert a YouTube video to RawContent."""
        snippet = video.get("snippet", {})
        video_id = video.get("id", {})

        # Handle both search results and video details format
        if isinstance(video_id, dict):
            video_id = video_id.get("videoId", "")
        else:
            video_id = str(video_id)

        title = snippet.get("title", "")
        description = snippet.get("description", "")

        if not title:
            return None

        # Parse published date
        published_str = snippet.get("publishedAt", "")
        published_at = None
        if published_str:
            with contextlib.suppress(ValueError):
                published_at = datetime.fromisoformat(
                    published_str.replace("Z", "+00:00")
                )

        # Build content from title and description
        content = f"{title}\n\n{description}"

        # Score based on channel and engagement (we don't have view counts in search)
        base_score = 65.0
        channel_title = snippet.get("channelTitle", "")

        return RawContent(
            title=title,
            content=content,
            source_type=ContentSourceType.YOUTUBE,
            source_url=f"https://www.youtube.com/watch?v={video_id}",
            source_id=video_id,
            author=channel_title,
            published_at=published_at,
            score=base_score,
            metadata={
                "niche": niche.value,
                "channel_id": snippet.get("channelId", ""),
                "channel_title": channel_title,
                "thumbnail": snippet.get("thumbnails", {})
                .get("high", {})
                .get("url", ""),
                "video_id": video_id,
            },
        )

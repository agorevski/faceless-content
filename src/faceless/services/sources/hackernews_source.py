"""
Hacker News content source adapter.

Fetches content from Hacker News using the Firebase API.
Best for tech, AI, and programming-related niches.
"""

import asyncio
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

# Niches that Hacker News is particularly good for
HN_PRIORITY_NICHES = {
    Niche.TECH_GADGETS,
    Niche.AI_FUTURE_TECH,
}

# Secondary niches that can benefit from HN
HN_SUPPORTED_NICHES = {
    Niche.TECH_GADGETS,
    Niche.AI_FUTURE_TECH,
    Niche.FINANCE,
    Niche.PHILOSOPHY,
    Niche.SPACE_ASTRONOMY,
}

# Keywords to filter HN stories by niche
NICHE_KEYWORDS: dict[Niche, list[str]] = {
    Niche.TECH_GADGETS: [
        "technology",
        "gadget",
        "hardware",
        "device",
        "smartphone",
        "computer",
    ],
    Niche.AI_FUTURE_TECH: [
        "ai",
        "artificial intelligence",
        "machine learning",
        "gpt",
        "llm",
        "neural",
        "robot",
        "future",
        "automation",
    ],
    Niche.FINANCE: [
        "finance",
        "stock",
        "crypto",
        "bitcoin",
        "economy",
        "startup",
        "vc",
        "funding",
    ],
    Niche.PHILOSOPHY: [
        "philosophy",
        "ethics",
        "consciousness",
        "mind",
        "existence",
    ],
    Niche.SPACE_ASTRONOMY: [
        "space",
        "nasa",
        "mars",
        "rocket",
        "satellite",
        "astronomy",
        "telescope",
    ],
}


class RateLimiter:
    """Simple token bucket rate limiter."""

    def __init__(self, requests_per_minute: int = 60) -> None:
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


class HackerNewsSource(ContentSource):
    """
    Hacker News content source adapter.

    Fetches content from Hacker News using the Firebase API.
    Free, no API key required.

    Features:
    - Top, new, best, ask, show stories
    - Story and comment fetching
    - Keyword filtering by niche
    - Full async support

    Example:
        >>> source = HackerNewsSource()
        >>> content = await source.fetch_content(Niche.AI_FUTURE_TECH, limit=10)
    """

    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def __init__(self) -> None:
        """Initialize Hacker News source."""
        settings = get_settings()
        self._settings = settings.content_sources
        self._rate_limiter = RateLimiter(self._settings.hackernews_rate_limit)
        self._timeout = httpx.Timeout(30.0)

    @property
    def source_type(self) -> ContentSourceType:
        """Return the source type."""
        return ContentSourceType.HACKER_NEWS

    @property
    def capabilities(self) -> SourceCapabilities:
        """Return source capabilities."""
        return SourceCapabilities(
            supports_search=False,  # HN API doesn't support search
            supports_trending=True,
            supports_pagination=True,
            requires_api_key=False,
            rate_limit_per_minute=self._settings.hackernews_rate_limit,
            max_results_per_request=500,
        )

    def supports_niche(self, niche: Niche) -> bool:
        """Check if this source supports the given niche."""
        return niche in HN_SUPPORTED_NICHES

    async def fetch_content(
        self,
        niche: Niche,
        query: str | None = None,
        limit: int = 10,
    ) -> list[RawContent]:
        """
        Fetch content from Hacker News for a niche.

        Args:
            niche: Content niche to fetch
            query: Optional keyword to filter (used in addition to niche keywords)
            limit: Maximum number of stories to fetch

        Returns:
            List of RawContent items
        """
        self.logger.info(
            "Fetching Hacker News content",
            niche=niche.value,
            limit=limit,
        )

        # Get story IDs
        story_ids = await self._get_top_story_ids()

        # Get niche keywords for filtering
        keywords = NICHE_KEYWORDS.get(niche, [])
        if query:
            keywords = [query] + keywords

        # Fetch stories and filter by niche
        all_content: list[RawContent] = []
        fetch_count = 0
        max_fetch = min(len(story_ids), limit * 5)  # Fetch more to filter

        for story_id in story_ids[:max_fetch]:
            try:
                story = await self._get_item(story_id)
                if not story:
                    continue

                # Skip if not a story or no title
                if story.get("type") != "story" or not story.get("title"):
                    continue

                # Filter by keywords if we have them
                if keywords:
                    title_lower = story.get("title", "").lower()
                    text_lower = story.get("text", "").lower()
                    combined = f"{title_lower} {text_lower}"

                    if not any(kw.lower() in combined for kw in keywords):
                        continue

                content = self._story_to_raw_content(story, niche)
                all_content.append(content)
                fetch_count += 1

                if fetch_count >= limit:
                    break

            except ContentFetchError:
                continue

        # Sort by score
        all_content.sort(key=lambda x: x.score, reverse=True)

        self.logger.info(
            "Hacker News fetch complete",
            niche=niche.value,
            count=len(all_content),
        )

        return all_content[:limit]

    async def fetch_trending(
        self,
        niche: Niche,
        limit: int = 10,
    ) -> list[RawContent]:
        """Fetch trending (top) content from Hacker News."""
        return await self.fetch_content(niche, limit=limit)

    async def get_story_with_comments(
        self,
        story_id: int,
        max_comments: int = 10,
    ) -> dict[str, Any] | None:
        """
        Get a story with its top comments.

        Useful for research-oriented content gathering.
        """
        story = await self._get_item(story_id)
        if not story:
            return None

        comments: list[dict[str, Any]] = []
        comment_ids = story.get("kids", [])[:max_comments]

        for comment_id in comment_ids:
            comment = await self._get_item(comment_id)
            if comment and comment.get("text"):
                comments.append(
                    {
                        "id": comment.get("id"),
                        "text": comment.get("text", ""),
                        "by": comment.get("by", ""),
                    }
                )

        story["comments"] = comments
        return story

    async def _get_top_story_ids(self) -> list[int]:
        """Get IDs of top stories."""
        await self._rate_limiter.acquire()

        url = f"{self.BASE_URL}/topstories.json"

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json() or []

        except httpx.HTTPStatusError as e:
            raise ContentFetchError(
                f"Hacker News API error: {e.response.status_code}",
                source="hacker_news",
                status_code=e.response.status_code,
            ) from e
        except httpx.RequestError as e:
            raise ContentFetchError(
                f"Hacker News request failed: {e}",
                source="hacker_news",
            ) from e

    async def _get_best_story_ids(self) -> list[int]:
        """Get IDs of best stories."""
        await self._rate_limiter.acquire()

        url = f"{self.BASE_URL}/beststories.json"

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json() or []

        except (httpx.HTTPStatusError, httpx.RequestError):
            return []

    async def _get_item(self, item_id: int) -> dict[str, Any] | None:
        """Get a single item (story or comment) by ID."""
        await self._rate_limiter.acquire()

        url = f"{self.BASE_URL}/item/{item_id}.json"

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                result: dict[str, Any] | None = response.json()
                return result

        except (httpx.HTTPStatusError, httpx.RequestError):
            return None

    def _story_to_raw_content(
        self,
        story: dict[str, Any],
        niche: Niche,
    ) -> RawContent:
        """Convert a HN story to RawContent."""
        # Parse timestamp
        timestamp = story.get("time", 0)
        published_at = datetime.fromtimestamp(timestamp) if timestamp else None

        # HN stories often don't have body text (just links)
        # Use title and any text, plus the URL as metadata
        title = story.get("title", "")
        text = story.get("text", "")

        # For stories without text, create content from title
        if not text:
            text = f"{title}. This is a link to external content."

        # Normalize score (HN scores are typically 1-5000+)
        raw_score = story.get("score", 0)
        if raw_score > 0:
            import math

            normalized_score = min(100, math.log10(raw_score + 1) * 30)
        else:
            normalized_score = 0

        return RawContent(
            title=title,
            content=text,
            source_type=ContentSourceType.HACKER_NEWS,
            source_url=story.get(
                "url", f"https://news.ycombinator.com/item?id={story.get('id', '')}"
            ),
            source_id=str(story.get("id", "")),
            author=story.get("by", ""),
            published_at=published_at,
            score=normalized_score,
            metadata={
                "niche": niche.value,
                "hn_score": story.get("score", 0),
                "num_comments": story.get("descendants", 0),
                "type": story.get("type", "story"),
                "hn_url": f"https://news.ycombinator.com/item?id={story.get('id', '')}",
            },
        )

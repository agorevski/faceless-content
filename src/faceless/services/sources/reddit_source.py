"""
Reddit content source adapter.

Fetches content from Reddit using the public JSON API.
Supports all 25 niches with intelligent subreddit mapping.
"""

import asyncio
import re
import time
from datetime import datetime
from typing import Any

import httpx

from faceless.config import get_settings
from faceless.core.enums import ContentSourceType, Niche
from faceless.core.exceptions import ContentFetchError, RateLimitError
from faceless.services.sources.base import (
    ContentSource,
    RawContent,
    SourceCapabilities,
)


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

            # Refill tokens based on elapsed time
            refill = elapsed * (self.requests_per_minute / 60.0)
            self.tokens = min(float(self.requests_per_minute), self.tokens + refill)
            self.last_refill = now

            if self.tokens < 1:
                wait_time = (1 - self.tokens) / (self.requests_per_minute / 60.0)
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


class ContentCache:
    """Simple TTL-based content cache."""

    def __init__(self, ttl_seconds: int = 3600) -> None:
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, tuple[float, list[RawContent]]] = {}

    def get(self, key: str) -> list[RawContent] | None:
        """Get cached content if not expired."""
        if key in self._cache:
            timestamp, content = self._cache[key]
            if time.time() - timestamp < self.ttl_seconds:
                return content
            del self._cache[key]
        return None

    def set(self, key: str, content: list[RawContent]) -> None:
        """Cache content with current timestamp."""
        self._cache[key] = (time.time(), content)

    def clear(self) -> None:
        """Clear all cached content."""
        self._cache.clear()


def clean_reddit_text(text: str) -> str:
    """Clean and normalize text from Reddit posts."""
    # Remove markdown formatting
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)
    text = re.sub(r"~~(.+?)~~", r"\1", text)

    # Remove links but keep text
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)

    # Remove Reddit-specific formatting
    text = re.sub(r"\^(.+)", r"\1", text)  # Superscript
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&#x200B;", "", text)  # Zero-width space

    # Remove excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)

    # Remove edit notices
    text = re.sub(r"\n*Edit:.*$", "", text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r"\n*Update:.*$", "", text, flags=re.IGNORECASE | re.MULTILINE)

    return text.strip()


class RedditSource(ContentSource):
    """
    Reddit content source adapter.

    Fetches content from Reddit using the public JSON API.
    Supports all 25 niches with intelligent subreddit mapping.

    Features:
    - Async HTTP with httpx
    - Rate limiting (respects Reddit's 60 req/min)
    - TTL-based caching
    - Text cleaning and normalization
    - All 25 niches supported via Niche.subreddits property

    Example:
        >>> source = RedditSource()
        >>> content = await source.fetch_content(Niche.SCARY_STORIES, limit=10)
    """

    def __init__(self) -> None:
        """Initialize Reddit source."""
        settings = get_settings()
        self._settings = settings.content_sources
        self._reddit_settings = settings.reddit

        # Rate limiter
        self._rate_limiter = RateLimiter(self._settings.reddit_rate_limit)

        # Cache
        self._cache = ContentCache(self._settings.cache_ttl_seconds)

        # HTTP client config
        self._timeout = httpx.Timeout(30.0)
        self._user_agent = self._reddit_settings.user_agent

    @property
    def source_type(self) -> ContentSourceType:
        """Return the source type."""
        return ContentSourceType.REDDIT

    @property
    def capabilities(self) -> SourceCapabilities:
        """Return source capabilities."""
        return SourceCapabilities(
            supports_search=True,
            supports_trending=True,
            supports_pagination=True,
            requires_api_key=False,
            rate_limit_per_minute=self._settings.reddit_rate_limit,
            max_results_per_request=100,
        )

    def supports_niche(self, niche: Niche) -> bool:  # noqa: ARG002
        """Check if this source supports the given niche."""
        # Reddit supports all niches via the subreddits property
        return True

    async def fetch_content(
        self,
        niche: Niche,
        query: str | None = None,
        limit: int = 10,
        time_filter: str = "month",
        min_score: int | None = None,
    ) -> list[RawContent]:
        """
        Fetch content from Reddit for a niche.

        Args:
            niche: Content niche to fetch
            query: Optional search query (searches within niche subreddits)
            limit: Maximum number of posts to fetch
            time_filter: Time filter for top posts (hour, day, week, month, year, all)
            min_score: Minimum upvote score (defaults to settings value)

        Returns:
            List of RawContent items

        Raises:
            ContentFetchError: If fetching fails
        """
        if min_score is None:
            min_score = self._settings.min_score

        # Check cache
        cache_key = f"reddit:{niche.value}:{query or 'top'}:{limit}:{time_filter}"
        cached = self._cache.get(cache_key)
        if cached:
            self.logger.debug("Cache hit", niche=niche.value, key=cache_key)
            return cached

        # Get subreddits for this niche
        subreddits = niche.subreddits
        if not subreddits:
            self.logger.warning("No subreddits for niche", niche=niche.value)
            return []

        self.logger.info(
            "Fetching Reddit content",
            niche=niche.value,
            subreddits=subreddits,
            limit=limit,
        )

        # Fetch from each subreddit
        all_content: list[RawContent] = []
        posts_per_sub = max(1, limit // len(subreddits) + 1)

        for subreddit in subreddits:
            try:
                if query:
                    posts = await self._search_subreddit(
                        subreddit, query, posts_per_sub, time_filter
                    )
                else:
                    posts = await self._fetch_top_posts(
                        subreddit, posts_per_sub, time_filter
                    )

                # Filter and convert to RawContent
                for post in posts:
                    if post.get("score", 0) < min_score:
                        continue
                    if not post.get("selftext"):
                        continue

                    content = self._post_to_raw_content(post, subreddit, niche)
                    if content.has_sufficient_content:
                        all_content.append(content)

            except ContentFetchError as e:
                self.logger.warning(
                    "Failed to fetch from subreddit",
                    subreddit=subreddit,
                    error=str(e),
                )
                continue

        # Sort by score and limit
        all_content.sort(key=lambda x: x.score, reverse=True)
        result = all_content[:limit]

        # Cache results
        if result:
            self._cache.set(cache_key, result)

        self.logger.info(
            "Reddit fetch complete",
            niche=niche.value,
            count=len(result),
        )

        return result

    async def fetch_trending(
        self,
        niche: Niche,
        limit: int = 10,
    ) -> list[RawContent]:
        """Fetch trending (hot) content from Reddit."""
        subreddits = niche.subreddits
        if not subreddits:
            return []

        all_content: list[RawContent] = []
        posts_per_sub = max(1, limit // len(subreddits) + 1)

        for subreddit in subreddits:
            try:
                posts = await self._fetch_hot_posts(subreddit, posts_per_sub)
                for post in posts:
                    if not post.get("selftext"):
                        continue
                    content = self._post_to_raw_content(post, subreddit, niche)
                    if content.has_sufficient_content:
                        all_content.append(content)
            except ContentFetchError:
                continue

        all_content.sort(key=lambda x: x.score, reverse=True)
        return all_content[:limit]

    async def _fetch_top_posts(
        self,
        subreddit: str,
        limit: int,
        time_filter: str,
    ) -> list[dict[str, Any]]:
        """Fetch top posts from a subreddit."""
        url = f"https://www.reddit.com/r/{subreddit}/top.json"
        params = {"limit": min(limit * 2, 100), "t": time_filter}
        return await self._make_request(url, params)

    async def _fetch_hot_posts(
        self,
        subreddit: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Fetch hot posts from a subreddit."""
        url = f"https://www.reddit.com/r/{subreddit}/hot.json"
        params = {"limit": min(limit * 2, 100)}
        return await self._make_request(url, params)

    async def _search_subreddit(
        self,
        subreddit: str,
        query: str,
        limit: int,
        time_filter: str,
    ) -> list[dict[str, Any]]:
        """Search within a subreddit."""
        url = f"https://www.reddit.com/r/{subreddit}/search.json"
        params = {
            "q": query,
            "restrict_sr": "on",
            "limit": min(limit * 2, 100),
            "t": time_filter,
            "sort": "relevance",
        }
        return await self._make_request(url, params)

    async def _make_request(
        self,
        url: str,
        params: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Make a rate-limited request to Reddit API."""
        await self._rate_limiter.acquire()

        headers = {"User-Agent": self._user_agent}

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, params=params, headers=headers)

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    raise RateLimitError(
                        "Reddit rate limit exceeded",
                        retry_after=retry_after,
                        service="reddit",
                    )

                response.raise_for_status()
                data = response.json()

                posts = []
                for child in data.get("data", {}).get("children", []):
                    if child.get("kind") == "t3":  # Link/post
                        posts.append(child.get("data", {}))
                return posts

        except httpx.HTTPStatusError as e:
            raise ContentFetchError(
                f"Reddit API error: {e.response.status_code}",
                source="reddit",
                status_code=e.response.status_code,
            ) from e
        except httpx.RequestError as e:
            raise ContentFetchError(
                f"Reddit request failed: {e}",
                source="reddit",
            ) from e

    def _post_to_raw_content(
        self,
        post: dict[str, Any],
        subreddit: str,
        niche: Niche,
    ) -> RawContent:
        """Convert a Reddit post to RawContent."""
        # Parse created_utc to datetime
        created_utc = post.get("created_utc", 0)
        published_at = datetime.fromtimestamp(created_utc) if created_utc else None

        # Normalize score to 0-100 scale (log scale for Reddit's wide range)
        raw_score = post.get("score", 0)
        if raw_score > 0:
            import math

            normalized_score = min(100, math.log10(raw_score + 1) * 25)
        else:
            normalized_score = 0

        return RawContent(
            title=post.get("title", ""),
            content=clean_reddit_text(post.get("selftext", "")),
            source_type=ContentSourceType.REDDIT,
            source_url=f"https://reddit.com{post.get('permalink', '')}",
            source_id=post.get("id", ""),
            author=post.get("author", "[deleted]"),
            published_at=published_at,
            score=normalized_score,
            metadata={
                "subreddit": subreddit,
                "niche": niche.value,
                "upvotes": post.get("score", 0),
                "upvote_ratio": post.get("upvote_ratio", 0),
                "num_comments": post.get("num_comments", 0),
                "is_original_content": post.get("is_original_content", False),
                "over_18": post.get("over_18", False),
            },
        )

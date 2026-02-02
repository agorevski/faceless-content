"""
OpenLibrary content source adapter.

Fetches book information from OpenLibrary API.
Best for book summaries, philosophy, and psychology niches.
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

# Niches that OpenLibrary is good for
OPENLIBRARY_SUPPORTED_NICHES = {
    Niche.BOOK_SUMMARIES,
    Niche.PHILOSOPHY,
    Niche.PSYCHOLOGY_FACTS,
    Niche.HISTORY,
    Niche.MOTIVATION,
    Niche.FINANCE,
}

# Search subjects for each niche
NICHE_SUBJECTS: dict[Niche, list[str]] = {
    Niche.BOOK_SUMMARIES: [
        "bestseller",
        "popular_science",
        "self_help",
        "business",
    ],
    Niche.PHILOSOPHY: [
        "philosophy",
        "ethics",
        "stoicism",
        "existentialism",
        "metaphysics",
    ],
    Niche.PSYCHOLOGY_FACTS: [
        "psychology",
        "cognitive_science",
        "behavioral_science",
        "neuroscience",
    ],
    Niche.HISTORY: [
        "history",
        "world_history",
        "biography",
        "historical_events",
    ],
    Niche.MOTIVATION: [
        "self_improvement",
        "success",
        "motivation",
        "leadership",
        "personal_development",
    ],
    Niche.FINANCE: [
        "finance",
        "investing",
        "economics",
        "money",
        "wealth",
    ],
}


class RateLimiter:
    """Simple token bucket rate limiter."""

    def __init__(self, requests_per_minute: int = 100) -> None:
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


class OpenLibrarySource(ContentSource):
    """
    OpenLibrary content source adapter.

    Fetches book information from OpenLibrary API.
    Free, no API key required.

    Features:
    - Book search by subject
    - Author information
    - Book descriptions and summaries
    - Trending/popular books

    Example:
        >>> source = OpenLibrarySource()
        >>> content = await source.fetch_content(Niche.BOOK_SUMMARIES, limit=10)
    """

    BASE_URL = "https://openlibrary.org"

    def __init__(self) -> None:
        """Initialize OpenLibrary source."""
        settings = get_settings()
        self._settings = settings.content_sources
        self._rate_limiter = RateLimiter(100)  # OpenLibrary is generous
        self._timeout = httpx.Timeout(30.0)

    @property
    def source_type(self) -> ContentSourceType:
        """Return the source type."""
        return ContentSourceType.OPEN_LIBRARY

    @property
    def capabilities(self) -> SourceCapabilities:
        """Return source capabilities."""
        return SourceCapabilities(
            supports_search=True,
            supports_trending=True,  # Via trending subjects
            supports_pagination=True,
            requires_api_key=False,
            rate_limit_per_minute=100,
            max_results_per_request=100,
        )

    def supports_niche(self, niche: Niche) -> bool:
        """Check if this source supports the given niche."""
        return niche in OPENLIBRARY_SUPPORTED_NICHES

    async def fetch_content(
        self,
        niche: Niche,
        query: str | None = None,
        limit: int = 10,
    ) -> list[RawContent]:
        """
        Fetch content from OpenLibrary for a niche.

        Args:
            niche: Content niche to fetch
            query: Optional search query
            limit: Maximum number of books to fetch

        Returns:
            List of RawContent items
        """
        self.logger.info(
            "Fetching OpenLibrary content",
            niche=niche.value,
            query=query,
            limit=limit,
        )

        if query:
            # Search by query
            books = await self._search_books(query, limit)
        else:
            # Search by niche subjects
            subjects = NICHE_SUBJECTS.get(niche, ["popular"])
            books = await self._search_by_subjects(subjects, limit)

        # Convert to RawContent
        all_content: list[RawContent] = []

        for book in books:
            content = await self._book_to_raw_content(book, niche)
            if content and content.has_sufficient_content:
                all_content.append(content)

        self.logger.info(
            "OpenLibrary fetch complete",
            niche=niche.value,
            count=len(all_content),
        )

        return all_content[:limit]

    async def fetch_trending(
        self,
        niche: Niche,
        limit: int = 10,
    ) -> list[RawContent]:
        """Fetch trending books from OpenLibrary."""
        # Use trending subjects endpoint
        subjects = NICHE_SUBJECTS.get(niche, ["popular"])

        all_content: list[RawContent] = []
        for subject in subjects[:2]:  # Limit subjects
            try:
                books = await self._get_trending_by_subject(subject, limit)
                for book in books:
                    content = await self._book_to_raw_content(book, niche)
                    if content and content.has_sufficient_content:
                        all_content.append(content)
                        if len(all_content) >= limit:
                            break
            except ContentFetchError:
                continue
            if len(all_content) >= limit:
                break

        return all_content[:limit]

    async def get_book_details(
        self,
        work_key: str,
        niche: Niche,
    ) -> RawContent | None:
        """Get detailed information about a specific book."""
        await self._rate_limiter.acquire()

        url = f"{self.BASE_URL}{work_key}.json"

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                work = response.json()

                # Get description
                description = work.get("description", "")
                if isinstance(description, dict):
                    description = description.get("value", "")

                if not description:
                    return None

                # Get author names
                authors = []
                for author_ref in work.get("authors", []):
                    author_key = author_ref.get("author", {}).get("key", "")
                    if author_key:
                        author_name = await self._get_author_name(author_key)
                        if author_name:
                            authors.append(author_name)

                return RawContent(
                    title=work.get("title", "Unknown Book"),
                    content=description,
                    source_type=ContentSourceType.OPEN_LIBRARY,
                    source_url=f"{self.BASE_URL}{work_key}",
                    source_id=work_key,
                    author=", ".join(authors) if authors else None,
                    published_at=None,
                    score=70.0,
                    metadata={
                        "niche": niche.value,
                        "subjects": work.get("subjects", [])[:5],
                        "first_publish_year": work.get("first_publish_date", ""),
                    },
                )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise ContentFetchError(
                f"OpenLibrary API error: {e.response.status_code}",
                source="open_library",
                status_code=e.response.status_code,
            ) from e
        except httpx.RequestError as e:
            raise ContentFetchError(
                f"OpenLibrary request failed: {e}",
                source="open_library",
            ) from e

    async def _search_books(
        self,
        query: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Search for books by query."""
        await self._rate_limiter.acquire()

        url = f"{self.BASE_URL}/search.json"
        params: dict[str, str | int] = {
            "q": query,
            "limit": limit,
            "fields": "key,title,author_name,first_publish_year,subject,cover_i",
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                result: list[dict[str, Any]] = data.get("docs", [])
                return result

        except httpx.HTTPStatusError as e:
            raise ContentFetchError(
                f"OpenLibrary search error: {e.response.status_code}",
                source="open_library",
                status_code=e.response.status_code,
            ) from e
        except httpx.RequestError as e:
            raise ContentFetchError(
                f"OpenLibrary search failed: {e}",
                source="open_library",
            ) from e

    async def _search_by_subjects(
        self,
        subjects: list[str],
        limit: int,
    ) -> list[dict[str, Any]]:
        """Search books by multiple subjects."""
        all_books: list[dict[str, Any]] = []
        books_per_subject = max(1, limit // len(subjects) + 1)

        for subject in subjects:
            try:
                books = await self._get_trending_by_subject(subject, books_per_subject)
                all_books.extend(books)
            except ContentFetchError:
                continue

        return all_books[:limit]

    async def _get_trending_by_subject(
        self,
        subject: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Get trending books for a subject."""
        await self._rate_limiter.acquire()

        url = f"{self.BASE_URL}/subjects/{subject}.json"
        params: dict[str, int] = {"limit": limit}

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                result: list[dict[str, Any]] = data.get("works", [])
                return result

        except (httpx.HTTPStatusError, httpx.RequestError):
            return []

    async def _get_author_name(self, author_key: str) -> str | None:
        """Get author name from author key."""
        await self._rate_limiter.acquire()

        url = f"{self.BASE_URL}{author_key}.json"

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                result: str | None = data.get("name")
                return result

        except (httpx.HTTPStatusError, httpx.RequestError):
            return None

    async def _book_to_raw_content(
        self,
        book: dict[str, Any],
        niche: Niche,
    ) -> RawContent | None:
        """Convert a book search result to RawContent."""
        # Try to get the work details for description
        work_key = book.get("key", "")

        # For search results, key is like "/works/OL12345W"
        # For subject results, it might be just the ID
        if not work_key.startswith("/works/"):
            work_key = f"/works/{work_key}" if work_key else ""

        if work_key:
            detailed = await self.get_book_details(work_key, niche)
            if detailed:
                return detailed

        # Fallback: create from search result metadata
        title = book.get("title", "")
        if not title:
            return None

        # Build content from available metadata
        authors = book.get("author_name", [])
        author_str = ", ".join(authors) if isinstance(authors, list) else str(authors)
        subjects = book.get("subject", [])[:10] if book.get("subject") else []
        year = book.get("first_publish_year", "")

        # Create a summary from metadata
        content_parts = [f"'{title}' is a book"]
        if author_str:
            content_parts.append(f"by {author_str}")
        if year:
            content_parts.append(f"first published in {year}")
        if subjects:
            content_parts.append(f". Topics covered include: {', '.join(subjects[:5])}")

        content = " ".join(content_parts) + "."

        # OpenLibrary books often lack detailed descriptions in search results
        # Return None if content is too short
        if len(content) < 50:
            return None

        return RawContent(
            title=title,
            content=content,
            source_type=ContentSourceType.OPEN_LIBRARY,
            source_url=f"{self.BASE_URL}{work_key}" if work_key else "",
            source_id=work_key or book.get("key", ""),
            author=author_str if author_str else None,
            published_at=(
                datetime(int(year), 1, 1) if year and str(year).isdigit() else None
            ),
            score=60.0,  # Lower score for metadata-only results
            metadata={
                "niche": niche.value,
                "subjects": subjects[:5],
                "first_publish_year": year,
                "cover_id": book.get("cover_i"),
            },
        )

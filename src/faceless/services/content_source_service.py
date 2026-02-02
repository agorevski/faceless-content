"""
Content Source Service - Main orchestrator for multi-source content fetching.

This service coordinates fetching content from multiple sources (Reddit,
Wikipedia, YouTube, News, HackerNews, OpenLibrary) with intelligent
source selection based on niche, deduplication, and ranking.
"""

import asyncio
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from faceless.config import get_settings
from faceless.core.enums import ContentSourceType, Niche
from faceless.core.exceptions import ContentFetchError
from faceless.services.sources import (
    ContentSource,
    HackerNewsSource,
    NewsSource,
    OpenLibrarySource,
    RawContent,
    RedditSource,
    WikipediaSource,
    YouTubeSource,
)
from faceless.utils.logging import LoggerMixin

# Priority order of sources for each niche
# Higher priority sources are tried first
NICHE_SOURCE_PRIORITY: dict[Niche, list[ContentSourceType]] = {
    # Story-based niches - Reddit primary
    Niche.SCARY_STORIES: [ContentSourceType.REDDIT],
    Niche.TRUE_CRIME: [
        ContentSourceType.REDDIT,
        ContentSourceType.NEWS,
        ContentSourceType.WIKIPEDIA,
    ],
    Niche.CONSPIRACY_MYSTERIES: [
        ContentSourceType.REDDIT,
        ContentSourceType.WIKIPEDIA,
    ],
    Niche.UNSOLVED_MYSTERIES: [
        ContentSourceType.REDDIT,
        ContentSourceType.WIKIPEDIA,
    ],
    Niche.RELATIONSHIP_ADVICE: [ContentSourceType.REDDIT],
    # Educational niches - Wikipedia primary
    Niche.HISTORY: [
        ContentSourceType.WIKIPEDIA,
        ContentSourceType.REDDIT,
    ],
    Niche.PSYCHOLOGY_FACTS: [
        ContentSourceType.WIKIPEDIA,
        ContentSourceType.REDDIT,
    ],
    Niche.MYTHOLOGY_FOLKLORE: [
        ContentSourceType.WIKIPEDIA,
        ContentSourceType.REDDIT,
    ],
    Niche.GEOGRAPHY_FACTS: [
        ContentSourceType.WIKIPEDIA,
        ContentSourceType.REDDIT,
    ],
    Niche.ANIMAL_FACTS: [
        ContentSourceType.WIKIPEDIA,
        ContentSourceType.REDDIT,
    ],
    Niche.SPACE_ASTRONOMY: [
        ContentSourceType.WIKIPEDIA,
        ContentSourceType.REDDIT,
        ContentSourceType.NEWS,
    ],
    Niche.PHILOSOPHY: [
        ContentSourceType.WIKIPEDIA,
        ContentSourceType.REDDIT,
        ContentSourceType.OPEN_LIBRARY,
    ],
    # Tech niches - HackerNews + News primary
    Niche.TECH_GADGETS: [
        ContentSourceType.HACKER_NEWS,
        ContentSourceType.REDDIT,
        ContentSourceType.YOUTUBE,
        ContentSourceType.NEWS,
    ],
    Niche.AI_FUTURE_TECH: [
        ContentSourceType.HACKER_NEWS,
        ContentSourceType.NEWS,
        ContentSourceType.REDDIT,
        ContentSourceType.YOUTUBE,
    ],
    # Finance/Business - News + Reddit
    Niche.FINANCE: [
        ContentSourceType.REDDIT,
        ContentSourceType.NEWS,
        ContentSourceType.YOUTUBE,
    ],
    Niche.LUXURY: [
        ContentSourceType.REDDIT,
        ContentSourceType.YOUTUBE,
        ContentSourceType.NEWS,
    ],
    Niche.CELEBRITY_NET_WORTH: [
        ContentSourceType.NEWS,
        ContentSourceType.REDDIT,
        ContentSourceType.YOUTUBE,
    ],
    # Book-related - OpenLibrary primary
    Niche.BOOK_SUMMARIES: [
        ContentSourceType.OPEN_LIBRARY,
        ContentSourceType.REDDIT,
    ],
    # Lifestyle niches - Reddit + YouTube
    Niche.MOTIVATION: [
        ContentSourceType.REDDIT,
        ContentSourceType.YOUTUBE,
    ],
    Niche.HEALTH_WELLNESS: [
        ContentSourceType.REDDIT,
        ContentSourceType.NEWS,
    ],
    Niche.LIFE_HACKS: [
        ContentSourceType.REDDIT,
        ContentSourceType.YOUTUBE,
    ],
    Niche.SURVIVAL_TIPS: [
        ContentSourceType.REDDIT,
        ContentSourceType.YOUTUBE,
    ],
    Niche.SLEEP_RELAXATION: [
        ContentSourceType.REDDIT,
        ContentSourceType.YOUTUBE,
    ],
    Niche.NETFLIX_RECOMMENDATIONS: [
        ContentSourceType.REDDIT,
        ContentSourceType.YOUTUBE,
    ],
    Niche.MOCKUMENTARY_HOWMADE: [
        ContentSourceType.REDDIT,
        ContentSourceType.YOUTUBE,
    ],
}


class ContentSourceService(LoggerMixin):
    """
    Orchestrates content fetching from multiple sources.

    This service manages all content sources, handles intelligent
    source selection based on niche, and provides unified content
    fetching with deduplication and ranking.

    Features:
    - Multi-source content fetching
    - Niche-based source prioritization
    - Parallel fetching from multiple sources
    - Content deduplication
    - Score-based ranking
    - Fallback to alternative sources

    Example:
        >>> service = ContentSourceService()
        >>> content = await service.fetch_content(Niche.SCARY_STORIES, limit=10)
        >>> for item in content:
        ...     print(f"{item.source_type.value}: {item.title}")
    """

    def __init__(self) -> None:
        """Initialize content source service with all available sources."""
        self._settings = get_settings()

        # Initialize all sources
        self._sources: dict[ContentSourceType, ContentSource] = {
            ContentSourceType.REDDIT: RedditSource(),
            ContentSourceType.WIKIPEDIA: WikipediaSource(),
            ContentSourceType.HACKER_NEWS: HackerNewsSource(),
            ContentSourceType.OPEN_LIBRARY: OpenLibrarySource(),
            ContentSourceType.NEWS: NewsSource(),
            ContentSourceType.YOUTUBE: YouTubeSource(),
        }

    def get_available_sources(self) -> list[ContentSourceType]:
        """Get list of available (configured) content sources."""
        return [
            source_type
            for source_type, source in self._sources.items()
            if source.is_available()
        ]

    def get_sources_for_niche(self, niche: Niche) -> list[ContentSourceType]:
        """Get prioritized list of sources that support a niche."""
        priority = NICHE_SOURCE_PRIORITY.get(niche, [ContentSourceType.REDDIT])

        available = []
        for source_type in priority:
            source = self._sources.get(source_type)
            if source and source.is_available() and source.supports_niche(niche):
                available.append(source_type)

        # Fallback to Reddit if nothing else available
        if not available and self._sources[ContentSourceType.REDDIT].is_available():
            available = [ContentSourceType.REDDIT]

        return available

    async def fetch_content(
        self,
        niche: Niche,
        query: str | None = None,
        limit: int = 10,
        sources: list[ContentSourceType] | None = None,
        parallel: bool = True,
    ) -> list[RawContent]:
        """
        Fetch content from sources for a niche.

        Args:
            niche: Content niche to fetch
            query: Optional search query to filter content
            limit: Maximum total items to return
            sources: Specific sources to use (defaults to niche priority)
            parallel: Whether to fetch from sources in parallel

        Returns:
            List of RawContent items, deduplicated and ranked

        Raises:
            ContentFetchError: If all sources fail
        """
        # Determine which sources to use
        if sources is None:
            sources = self.get_sources_for_niche(niche)

        if not sources:
            raise ContentFetchError(
                f"No available sources for niche: {niche.value}",
                niche=niche.value,
            )

        self.logger.info(
            "Fetching content",
            niche=niche.value,
            sources=[s.value for s in sources],
            limit=limit,
        )

        # Calculate items per source
        items_per_source = max(1, limit // len(sources) + 2)

        # Fetch from sources
        if parallel and len(sources) > 1:
            all_content = await self._fetch_parallel(
                niche, query, sources, items_per_source
            )
        else:
            all_content = await self._fetch_sequential(
                niche, query, sources, items_per_source
            )

        if not all_content:
            self.logger.warning("No content fetched", niche=niche.value)
            return []

        # Deduplicate and rank
        unique_content = self._deduplicate(all_content)
        ranked_content = self._rank_content(unique_content)

        self.logger.info(
            "Content fetch complete",
            niche=niche.value,
            total=len(all_content),
            unique=len(unique_content),
            returned=min(len(ranked_content), limit),
        )

        return ranked_content[:limit]

    async def fetch_trending(
        self,
        niche: Niche,
        limit: int = 10,
        sources: list[ContentSourceType] | None = None,
    ) -> list[RawContent]:
        """
        Fetch trending content from sources for a niche.

        Args:
            niche: Content niche
            limit: Maximum items to return
            sources: Specific sources to use

        Returns:
            List of trending RawContent items
        """
        if sources is None:
            sources = self.get_sources_for_niche(niche)

        all_content: list[RawContent] = []
        items_per_source = max(1, limit // len(sources) + 2)

        for source_type in sources:
            source = self._sources.get(source_type)
            if not source:
                continue

            try:
                content = await source.fetch_trending(niche, items_per_source)
                all_content.extend(content)
            except Exception as e:
                self.logger.warning(
                    "Trending fetch failed",
                    source=source_type.value,
                    error=str(e),
                )

        unique_content = self._deduplicate(all_content)
        ranked_content = self._rank_content(unique_content)

        return ranked_content[:limit]

    async def search(
        self,
        query: str,
        niche: Niche | None = None,
        limit: int = 10,
        sources: list[ContentSourceType] | None = None,
    ) -> list[RawContent]:
        """
        Search for content across sources.

        Args:
            query: Search query
            niche: Optional niche filter
            limit: Maximum items to return
            sources: Specific sources to use

        Returns:
            List of matching RawContent items
        """
        if sources is None:
            if niche:
                sources = self.get_sources_for_niche(niche)
            else:
                # Use all available sources for non-niche search
                sources = self.get_available_sources()

        all_content: list[RawContent] = []
        items_per_source = max(1, limit // len(sources) + 2)

        for source_type in sources:
            source = self._sources.get(source_type)
            if not source or not source.capabilities.supports_search:
                continue

            try:
                if niche:
                    content = await source.fetch_content(
                        niche, query=query, limit=items_per_source
                    )
                else:
                    content = await source.search(query, limit=items_per_source)
                all_content.extend(content)
            except Exception as e:
                self.logger.warning(
                    "Search failed",
                    source=source_type.value,
                    query=query,
                    error=str(e),
                )

        unique_content = self._deduplicate(all_content)
        ranked_content = self._rank_content(unique_content)

        return ranked_content[:limit]

    def content_to_script_dict(
        self,
        content: RawContent,
        niche: Niche,
        max_scenes: int = 10,
        words_per_scene: int = 150,
    ) -> dict[str, Any]:
        """
        Convert RawContent to a script dictionary compatible with the pipeline.

        This is a simplified version - for better results, use the EnhancerService.

        Args:
            content: The raw content to convert
            niche: Target niche
            max_scenes: Maximum number of scenes
            words_per_scene: Target words per scene

        Returns:
            Script dictionary ready for pipeline
        """
        text = content.content
        title = content.title

        # Split into paragraphs
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        # Merge/split to target scene length
        scenes: list[str] = []
        current_text = ""

        for para in paragraphs:
            current_text += " " + para if current_text else para
            word_count = len(current_text.split())

            if word_count >= words_per_scene:
                scenes.append(current_text.strip())
                current_text = ""

                if len(scenes) >= max_scenes:
                    break

        if current_text and len(scenes) < max_scenes:
            scenes.append(current_text.strip())

        # Generate basic image prompts
        script_scenes = []
        for i, narration in enumerate(scenes, 1):
            image_prompt = self._generate_basic_image_prompt(
                narration, niche, i, len(scenes)
            )
            script_scenes.append(
                {
                    "scene_number": i,
                    "narration": narration,
                    "image_prompt": image_prompt,
                    "duration_estimate": len(narration.split()) / 2.5,
                }
            )

        return {
            "title": title,
            "source": content.source_type.value,
            "author": content.author or "",
            "url": content.source_url,
            "niche": niche.value,
            "created_at": datetime.now().isoformat(),
            "scenes": script_scenes,
        }

    async def save_content_as_script(
        self,
        content: RawContent,
        niche: Niche,
        output_dir: Path | None = None,
    ) -> Path:
        """
        Save RawContent as a script JSON file.

        Args:
            content: The content to save
            niche: Target niche
            output_dir: Output directory (defaults to niche scripts dir)

        Returns:
            Path to saved script file
        """
        import json

        if output_dir is None:
            output_dir = self._settings.get_scripts_dir(niche)

        output_dir.mkdir(parents=True, exist_ok=True)

        script = self.content_to_script_dict(content, niche)

        # Generate filename
        safe_title = re.sub(r"[^\w\s-]", "", content.title[:50])
        safe_title = re.sub(r"[-\s]+", "-", safe_title).strip("-")
        filename = f"{safe_title.lower()}_script.json"

        output_path = output_dir / filename

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(script, f, indent=2, ensure_ascii=False)

        self.logger.info(
            "Script saved", path=str(output_path), title=content.title[:50]
        )

        return output_path

    async def _fetch_parallel(
        self,
        niche: Niche,
        query: str | None,
        sources: list[ContentSourceType],
        limit_per_source: int,
    ) -> list[RawContent]:
        """Fetch from multiple sources in parallel."""

        async def fetch_from_source(source_type: ContentSourceType) -> list[RawContent]:
            source = self._sources.get(source_type)
            if not source:
                return []
            try:
                return await source.fetch_content(niche, query, limit_per_source)
            except Exception as e:
                self.logger.warning(
                    "Source fetch failed",
                    source=source_type.value,
                    error=str(e),
                )
                return []

        tasks = [fetch_from_source(s) for s in sources]
        results = await asyncio.gather(*tasks)

        all_content: list[RawContent] = []
        for content_list in results:
            all_content.extend(content_list)

        return all_content

    async def _fetch_sequential(
        self,
        niche: Niche,
        query: str | None,
        sources: list[ContentSourceType],
        limit_per_source: int,
    ) -> list[RawContent]:
        """Fetch from sources sequentially."""
        all_content: list[RawContent] = []

        for source_type in sources:
            source = self._sources.get(source_type)
            if not source:
                continue

            try:
                content = await source.fetch_content(niche, query, limit_per_source)
                all_content.extend(content)
            except Exception as e:
                self.logger.warning(
                    "Source fetch failed",
                    source=source_type.value,
                    error=str(e),
                )

        return all_content

    def _deduplicate(self, content: list[RawContent]) -> list[RawContent]:
        """Remove duplicate content based on title similarity."""
        seen_titles: set[str] = set()
        unique: list[RawContent] = []

        for item in content:
            # Normalize title for comparison
            normalized = item.title.lower().strip()
            normalized = re.sub(r"[^\w\s]", "", normalized)

            if normalized not in seen_titles:
                seen_titles.add(normalized)
                unique.append(item)

        return unique

    def _rank_content(self, content: list[RawContent]) -> list[RawContent]:
        """Rank content by score and other factors."""
        # Sort by score (descending), then by content length
        return sorted(
            content,
            key=lambda x: (x.score, x.word_count),
            reverse=True,
        )

    def _generate_basic_image_prompt(
        self,
        narration: str,
        niche: Niche,
        scene_num: int,
        total_scenes: int,
    ) -> str:
        """Generate a basic image prompt from narration."""
        words = narration.lower().split()

        # Niche-specific base prompts
        niche_bases = {
            Niche.SCARY_STORIES: "Dark atmospheric scene, horror movie cinematography",
            Niche.FINANCE: "Professional business visualization, modern minimalist",
            Niche.LUXURY: "Elegant luxury aesthetic, cinematic lighting",
            Niche.TRUE_CRIME: "Documentary style, dramatic noir lighting",
            Niche.HISTORY: "Historical scene, period-accurate, epic",
            Niche.SPACE_ASTRONOMY: "Space visualization, cosmic, awe-inspiring",
            Niche.TECH_GADGETS: "Modern technology, sleek design, professional",
            Niche.AI_FUTURE_TECH: "Futuristic, sci-fi aesthetic, advanced technology",
        }

        base = niche_bases.get(niche, "Professional visualization")

        # Add scene position context
        if scene_num == 1:
            base = f"Opening shot, {base}"
        elif scene_num == total_scenes:
            base = f"Climactic scene, {base}"

        # Extract key nouns (simple approach)
        keywords = [w for w in words[:30] if len(w) > 4][:5]
        keyword_str = ", ".join(keywords) if keywords else ""

        return f"{base}, {keyword_str}, cinematic composition, dramatic lighting"

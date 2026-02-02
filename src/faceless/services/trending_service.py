"""
Trending topic discovery service for the Faceless Content Pipeline.

This service discovers trending topics from Reddit, Google Trends,
and other sources to help create timely, relevant content.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from faceless.clients.azure_openai import AzureOpenAIClient
from faceless.config import get_settings
from faceless.core.enums import Niche
from faceless.utils.logging import LoggerMixin


class TrendSource(str, Enum):
    """Sources for trending topic discovery."""

    REDDIT = "reddit"
    GOOGLE_TRENDS = "google_trends"
    AI_SUGGESTED = "ai_suggested"
    NEWS = "news"


class TrendLifecycle(str, Enum):
    """Lifecycle stage of a trend."""

    EMERGING = "emerging"  # Just starting to grow
    RISING = "rising"  # Growing rapidly
    PEAK = "peak"  # At maximum interest
    DECLINING = "declining"  # Interest dropping
    EVERGREEN = "evergreen"  # Consistent interest over time


@dataclass
class TrendingTopic:
    """A single trending topic."""

    title: str
    niche: Niche
    source: TrendSource
    discovered_at: datetime = field(default_factory=datetime.now)

    # Trend metrics
    score: float = 0.0  # Overall trend score (0-100)
    search_volume: int = 0  # Relative search volume
    growth_rate: float = 0.0  # % growth in last period
    lifecycle: TrendLifecycle = TrendLifecycle.EMERGING

    # Content potential
    video_potential: float = 0.0  # 0-1, how suitable for video
    competition_level: str = "medium"  # low, medium, high
    evergreen_potential: float = 0.0  # 0-1, lasting value

    # Metadata
    related_topics: list[str] = field(default_factory=list)
    suggested_angles: list[str] = field(default_factory=list)
    source_url: str = ""
    subreddit: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "title": self.title,
            "niche": self.niche.value,
            "source": self.source.value,
            "discovered_at": self.discovered_at.isoformat(),
            "score": self.score,
            "search_volume": self.search_volume,
            "growth_rate": self.growth_rate,
            "lifecycle": self.lifecycle.value,
            "video_potential": self.video_potential,
            "competition_level": self.competition_level,
            "evergreen_potential": self.evergreen_potential,
            "related_topics": self.related_topics,
            "suggested_angles": self.suggested_angles,
            "source_url": self.source_url,
            "subreddit": self.subreddit,
        }


@dataclass
class TrendReport:
    """A complete trend report for a niche."""

    niche: Niche
    generated_at: datetime = field(default_factory=datetime.now)

    # Categorized topics
    hot_topics: list[TrendingTopic] = field(
        default_factory=list
    )  # Immediate opportunities
    rising_topics: list[TrendingTopic] = field(default_factory=list)  # Growing trends
    evergreen_topics: list[TrendingTopic] = field(
        default_factory=list
    )  # Always relevant
    viral_potential: list[TrendingTopic] = field(
        default_factory=list
    )  # High viral chance

    # Recommendations
    top_recommendation: TrendingTopic | None = None
    content_calendar_suggestions: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "niche": self.niche.value,
            "generated_at": self.generated_at.isoformat(),
            "hot_topics": [t.to_dict() for t in self.hot_topics],
            "rising_topics": [t.to_dict() for t in self.rising_topics],
            "evergreen_topics": [t.to_dict() for t in self.evergreen_topics],
            "viral_potential": [t.to_dict() for t in self.viral_potential],
            "top_recommendation": (
                self.top_recommendation.to_dict() if self.top_recommendation else None
            ),
            "content_calendar": self.content_calendar_suggestions,
        }


# Subreddit configurations by niche
NICHE_SUBREDDITS: dict[Niche, list[str]] = {
    Niche.SCARY_STORIES: [
        "nosleep",
        "creepypasta",
        "LetsNotMeet",
        "Glitch_in_the_Matrix",
        "TrueScaryStories",
    ],
    Niche.FINANCE: [
        "personalfinance",
        "investing",
        "stocks",
        "financialindependence",
        "povertyfinance",
    ],
    Niche.LUXURY: ["luxury", "watches", "cars", "realestate", "Superstonk"],
    Niche.TRUE_CRIME: [
        "TrueCrime",
        "UnresolvedMysteries",
        "serialkillers",
        "TrueCrimeDiscussion",
    ],
    Niche.PSYCHOLOGY_FACTS: [
        "psychology",
        "neuroscience",
        "AskSocialScience",
        "cogsci",
    ],
    Niche.HISTORY: ["history", "HistoryPorn", "AskHistorians", "todayilearned"],
    Niche.MOTIVATION: [
        "GetMotivated",
        "DecidingToBeBetter",
        "selfimprovement",
        "productivity",
    ],
    Niche.SPACE_ASTRONOMY: ["space", "Astronomy", "astrophysics", "nasa"],
    Niche.CONSPIRACY_MYSTERIES: [
        "conspiracy",
        "HighStrangeness",
        "UnsolvedMysteries",
        "aliens",
    ],
    Niche.ANIMAL_FACTS: [
        "Awwducational",
        "NatureIsFuckingLit",
        "animals",
        "interestingasfuck",
    ],
    Niche.HEALTH_WELLNESS: ["Health", "nutrition", "Fitness", "longevity"],
    Niche.RELATIONSHIP_ADVICE: [
        "relationship_advice",
        "dating_advice",
        "Marriage",
        "BreakUps",
    ],
    Niche.TECH_GADGETS: ["gadgets", "technology", "Android", "apple"],
    Niche.LIFE_HACKS: ["lifehacks", "LifeProTips", "productivity", "howto"],
    Niche.MYTHOLOGY_FOLKLORE: ["mythology", "folklore", "Paranormal", "occult"],
    Niche.UNSOLVED_MYSTERIES: [
        "UnsolvedMysteries",
        "UnresolvedMysteries",
        "RBI",
        "Thetruthishere",
    ],
    Niche.GEOGRAPHY_FACTS: ["geography", "MapPorn", "travel", "earthporn"],
    Niche.AI_FUTURE_TECH: [
        "Futurology",
        "artificial",
        "MachineLearning",
        "singularity",
    ],
    Niche.PHILOSOPHY: ["philosophy", "Stoicism", "Existentialism", "askphilosophy"],
    Niche.BOOK_SUMMARIES: ["books", "booksuggestions", "52book", "nonfictionbooks"],
    Niche.CELEBRITY_NET_WORTH: [
        "Celebs",
        "entertainment",
        "popculturechat",
        "celebrity",
    ],
    Niche.SURVIVAL_TIPS: ["Survival", "preppers", "Bushcraft", "CampingandHiking"],
    Niche.SLEEP_RELAXATION: ["sleep", "Meditation", "asmr", "relaxation"],
}


class TrendingService(LoggerMixin):
    """
    Service for discovering trending topics.

    Finds trending content opportunities from multiple sources
    to help create timely, relevant content.

    Features:
    - Reddit hot post analysis
    - AI-powered trend suggestions
    - Topic scoring and ranking
    - Content calendar recommendations
    - Evergreen topic identification

    Example:
        >>> service = TrendingService()
        >>> report = service.get_trend_report(Niche.SCARY_STORIES)
        >>> top_topic = report.top_recommendation
    """

    def __init__(
        self,
        client: AzureOpenAIClient | None = None,
    ) -> None:
        """
        Initialize trending service.

        Args:
            client: Optional Azure OpenAI client
        """
        self._client = client or AzureOpenAIClient()
        self._settings = get_settings()

    def get_trend_report(
        self,
        niche: Niche,
        include_reddit: bool = True,
        include_ai_suggestions: bool = True,
        max_topics_per_source: int = 10,
    ) -> TrendReport:
        """
        Generate a comprehensive trend report for a niche.

        Args:
            niche: Content niche to analyze
            include_reddit: Include Reddit-based trends
            include_ai_suggestions: Include AI-suggested topics
            max_topics_per_source: Maximum topics per source

        Returns:
            TrendReport with categorized trending topics
        """
        self.logger.info("Generating trend report", niche=niche.value)

        report = TrendReport(niche=niche)
        all_topics: list[TrendingTopic] = []

        # Get Reddit trends (using AI to simulate for now)
        if include_reddit:
            reddit_topics = self._get_reddit_trends(niche, max_topics_per_source)
            all_topics.extend(reddit_topics)

        # Get AI-suggested trends
        if include_ai_suggestions:
            ai_topics = self._get_ai_trends(niche, max_topics_per_source)
            all_topics.extend(ai_topics)

        # Categorize and rank topics
        self._categorize_topics(report, all_topics)

        # Generate content calendar suggestions
        report.content_calendar_suggestions = self._generate_calendar(report)

        # Set top recommendation
        if report.hot_topics:
            report.top_recommendation = report.hot_topics[0]
        elif report.rising_topics:
            report.top_recommendation = report.rising_topics[0]
        elif report.viral_potential:
            report.top_recommendation = report.viral_potential[0]

        self.logger.info(
            "Trend report generated",
            niche=niche.value,
            hot_count=len(report.hot_topics),
            rising_count=len(report.rising_topics),
        )

        return report

    def get_hot_topics(
        self,
        niche: Niche,
        count: int = 10,
    ) -> list[TrendingTopic]:
        """
        Get currently hot topics for a niche.

        Args:
            niche: Content niche
            count: Number of topics to return

        Returns:
            List of hot trending topics
        """
        report = self.get_trend_report(niche, max_topics_per_source=count)
        return report.hot_topics[:count]

    def analyze_topic_potential(
        self,
        topic: str,
        niche: Niche,
    ) -> TrendingTopic:
        """
        Analyze a specific topic's viral/content potential.

        Args:
            topic: Topic to analyze
            niche: Content niche context

        Returns:
            TrendingTopic with detailed analysis
        """
        prompt = f"""Analyze this topic's potential for a {niche.display_name} YouTube/TikTok video:

Topic: "{topic}"

Evaluate:
1. Current search interest (is it trending?)
2. Video content potential
3. Competition level
4. Evergreen vs timely value
5. Viral potential
6. Best angles to cover

Return JSON:
{{
    "score": 75,
    "search_volume_estimate": "high|medium|low",
    "growth_rate": 15.5,
    "lifecycle": "emerging|rising|peak|declining|evergreen",
    "video_potential": 0.85,
    "competition_level": "low|medium|high",
    "evergreen_potential": 0.3,
    "related_topics": ["topic 1", "topic 2"],
    "suggested_angles": ["angle 1", "angle 2", "angle 3"],
    "best_format": "explainer|story|list|comparison|tutorial",
    "timing_recommendation": "post now|wait for peak|evergreen - anytime"
}}"""

        try:
            result = self._client.chat_json(
                system_prompt="You are a trend analyst specializing in YouTube and TikTok content.",
                user_prompt=prompt,
                temperature=0.6,
            )

            volume_map = {"high": 80000, "medium": 30000, "low": 10000}
            volume_str = result.get("search_volume_estimate", "medium")
            if isinstance(volume_str, str):
                volume = volume_map.get(volume_str.lower(), 30000)
            else:
                volume = int(volume_str)

            lifecycle_str = result.get("lifecycle", "emerging")
            try:
                lifecycle = TrendLifecycle(lifecycle_str.lower())
            except ValueError:
                lifecycle = TrendLifecycle.EMERGING

            return TrendingTopic(
                title=topic,
                niche=niche,
                source=TrendSource.AI_SUGGESTED,
                score=float(result.get("score", 50)),
                search_volume=volume,
                growth_rate=float(result.get("growth_rate", 0)),
                lifecycle=lifecycle,
                video_potential=float(result.get("video_potential", 0.5)),
                competition_level=result.get("competition_level", "medium"),
                evergreen_potential=float(result.get("evergreen_potential", 0.3)),
                related_topics=result.get("related_topics", []),
                suggested_angles=result.get("suggested_angles", []),
            )

        except Exception as e:
            self.logger.warning("Topic analysis failed", topic=topic, error=str(e))
            return TrendingTopic(
                title=topic,
                niche=niche,
                source=TrendSource.AI_SUGGESTED,
                score=50,
            )

    def get_subreddit_hot_posts(
        self,
        subreddit: str,
        count: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Get hot posts from a subreddit (simulated via AI for now).

        Note: For production, integrate with Reddit API (PRAW).

        Args:
            subreddit: Subreddit name (without r/)
            count: Number of posts to return

        Returns:
            List of post data dictionaries
        """
        prompt = f"""Simulate the current top {count} hot posts from r/{subreddit}.

For each post, provide realistic:
- Title (actual style used in that subreddit)
- Upvotes (realistic range for that sub)
- Comment count
- Posted time (hours ago)
- Potential content angle

Return JSON array:
[
    {{
        "title": "Post title here",
        "upvotes": 5432,
        "comments": 234,
        "hours_ago": 4,
        "content_angle": "How this could be turned into video content"
    }}
]"""

        try:
            result = self._client.chat_json(
                system_prompt="You are a Reddit trend analyst. Simulate realistic trending content.",
                user_prompt=prompt,
                temperature=0.8,
            )

            if isinstance(result, list):
                return list(result[:count])
            if "posts" in result:
                return list(result["posts"][:count])
            return []

        except Exception as e:
            self.logger.warning(
                "Subreddit fetch failed", subreddit=subreddit, error=str(e)
            )
            return []

    def suggest_content_timing(
        self,
        topic: TrendingTopic,
    ) -> dict[str, Any]:
        """
        Suggest optimal timing for content about a topic.

        Args:
            topic: The trending topic

        Returns:
            Timing recommendations
        """
        lifecycle_timing = {
            TrendLifecycle.EMERGING: {
                "urgency": "medium",
                "recommendation": "Prepare content now, publish as trend grows",
                "window": "1-2 weeks",
            },
            TrendLifecycle.RISING: {
                "urgency": "high",
                "recommendation": "Publish as soon as possible to catch the wave",
                "window": "3-7 days",
            },
            TrendLifecycle.PEAK: {
                "urgency": "very_high",
                "recommendation": "Publish immediately or wait for next cycle",
                "window": "1-3 days",
            },
            TrendLifecycle.DECLINING: {
                "urgency": "low",
                "recommendation": "Wait for topic to become nostalgic or add new angle",
                "window": "Consider for future series",
            },
            TrendLifecycle.EVERGREEN: {
                "urgency": "none",
                "recommendation": "Publish anytime, focus on quality over speed",
                "window": "Indefinite",
            },
        }

        return {
            "topic": topic.title,
            "lifecycle": topic.lifecycle.value,
            **lifecycle_timing.get(
                topic.lifecycle, lifecycle_timing[TrendLifecycle.EVERGREEN]
            ),
        }

    def _get_reddit_trends(
        self,
        niche: Niche,
        max_topics: int,
    ) -> list[TrendingTopic]:
        """Get trending topics from Reddit (AI-simulated)."""
        subreddits = NICHE_SUBREDDITS.get(niche, [])[:3]  # Top 3 subreddits

        prompt = f"""Identify the top {max_topics} trending topics from these {niche.display_name} subreddits: {', '.join(subreddits)}

Consider:
- What's currently getting high engagement
- Emerging discussions
- Viral potential stories/topics
- Topics suitable for video content

Return JSON array:
[
    {{
        "title": "Topic/story title",
        "subreddit": "subreddit_name",
        "score": 85,
        "growth_rate": 25.0,
        "lifecycle": "rising",
        "video_potential": 0.9,
        "suggested_angles": ["angle 1", "angle 2"]
    }}
]"""

        try:
            result = self._client.chat_json(
                system_prompt="You are a Reddit trend analyst for content creators.",
                user_prompt=prompt,
                temperature=0.7,
            )

            topics = []
            items = result if isinstance(result, list) else result.get("topics", [])

            for item in items[:max_topics]:
                if not isinstance(item, dict):
                    continue

                lifecycle_str = item.get("lifecycle", "emerging")
                try:
                    lifecycle = TrendLifecycle(lifecycle_str.lower())
                except ValueError:
                    lifecycle = TrendLifecycle.EMERGING

                topics.append(
                    TrendingTopic(
                        title=item.get("title", "Unknown"),
                        niche=niche,
                        source=TrendSource.REDDIT,
                        score=float(item.get("score", 50)),
                        growth_rate=float(item.get("growth_rate", 0)),
                        lifecycle=lifecycle,
                        video_potential=float(item.get("video_potential", 0.5)),
                        suggested_angles=item.get("suggested_angles", []),
                        subreddit=item.get("subreddit", ""),
                    )
                )

            return topics

        except Exception as e:
            self.logger.warning("Reddit trends failed", error=str(e))
            return []

    def _get_ai_trends(
        self,
        niche: Niche,
        max_topics: int,
    ) -> list[TrendingTopic]:
        """Get AI-suggested trending topics."""
        prompt = f"""Suggest {max_topics} trending or high-potential topics for {niche.display_name} video content.

Include a mix of:
- Currently trending topics (news, viral discussions)
- Rising topics (growing interest)
- Evergreen topics with proven engagement
- Underserved topics with high potential

Return JSON array:
[
    {{
        "title": "Topic title",
        "score": 80,
        "lifecycle": "rising|emerging|peak|evergreen",
        "video_potential": 0.85,
        "competition_level": "low|medium|high",
        "evergreen_potential": 0.6,
        "suggested_angles": ["angle 1", "angle 2"],
        "why_trending": "Brief explanation"
    }}
]"""

        try:
            result = self._client.chat_json(
                system_prompt="You are a content strategist for YouTube and TikTok creators.",
                user_prompt=prompt,
                temperature=0.8,
            )

            topics = []
            items = result if isinstance(result, list) else result.get("topics", [])

            for item in items[:max_topics]:
                if not isinstance(item, dict):
                    continue

                lifecycle_str = item.get("lifecycle", "emerging")
                try:
                    lifecycle = TrendLifecycle(lifecycle_str.lower())
                except ValueError:
                    lifecycle = TrendLifecycle.EMERGING

                topics.append(
                    TrendingTopic(
                        title=item.get("title", "Unknown"),
                        niche=niche,
                        source=TrendSource.AI_SUGGESTED,
                        score=float(item.get("score", 50)),
                        lifecycle=lifecycle,
                        video_potential=float(item.get("video_potential", 0.5)),
                        competition_level=item.get("competition_level", "medium"),
                        evergreen_potential=float(item.get("evergreen_potential", 0.3)),
                        suggested_angles=item.get("suggested_angles", []),
                    )
                )

            return topics

        except Exception as e:
            self.logger.warning("AI trends failed", error=str(e))
            return []

    def _categorize_topics(
        self,
        report: TrendReport,
        topics: list[TrendingTopic],
    ) -> None:
        """Categorize topics into report sections."""
        for topic in topics:
            # Hot topics: high score + rising/peak lifecycle
            if topic.score >= 75 and topic.lifecycle in (
                TrendLifecycle.RISING,
                TrendLifecycle.PEAK,
            ):
                report.hot_topics.append(topic)

            # Rising topics: emerging with good growth
            elif topic.lifecycle == TrendLifecycle.EMERGING and topic.growth_rate > 10:
                report.rising_topics.append(topic)

            # Evergreen topics
            elif (
                topic.lifecycle == TrendLifecycle.EVERGREEN
                or topic.evergreen_potential >= 0.7
            ):
                report.evergreen_topics.append(topic)

            # Viral potential: high video potential + low competition
            if topic.video_potential >= 0.8 and topic.competition_level == "low":
                report.viral_potential.append(topic)

        # Sort each category by score
        report.hot_topics.sort(key=lambda x: x.score, reverse=True)
        report.rising_topics.sort(key=lambda x: x.growth_rate, reverse=True)
        report.evergreen_topics.sort(key=lambda x: x.evergreen_potential, reverse=True)
        report.viral_potential.sort(key=lambda x: x.video_potential, reverse=True)

    def _generate_calendar(
        self,
        report: TrendReport,
    ) -> list[dict[str, str]]:
        """Generate content calendar suggestions."""
        calendar = []

        # Immediate (1-3 days): Hot topics
        for topic in report.hot_topics[:2]:
            calendar.append(
                {
                    "timing": "This week",
                    "topic": topic.title,
                    "reason": "Currently trending - high urgency",
                    "format": "Quick video to catch the wave",
                }
            )

        # Short-term (1-2 weeks): Rising topics
        for topic in report.rising_topics[:2]:
            calendar.append(
                {
                    "timing": "Next 1-2 weeks",
                    "topic": topic.title,
                    "reason": "Growing trend - optimal timing",
                    "format": "Well-researched comprehensive video",
                }
            )

        # Ongoing: Evergreen topics
        for topic in report.evergreen_topics[:2]:
            calendar.append(
                {
                    "timing": "Anytime (fill gaps)",
                    "topic": topic.title,
                    "reason": "Consistent interest - reliable performance",
                    "format": "High-quality evergreen content",
                }
            )

        return calendar

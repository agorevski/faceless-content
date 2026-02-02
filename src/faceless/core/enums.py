"""
Enumeration types for the Faceless Content Pipeline.

This module defines all the enum types used throughout the application,
providing type-safe constants for niches, platforms, and job statuses.
"""

from enum import Enum


class Niche(str, Enum):
    """
    Content niche categories supported by the pipeline.

    Each niche has specific voice settings, image styles, and content sources
    configured in the settings module.
    """

    # Original niches
    SCARY_STORIES = "scary-stories"
    FINANCE = "finance"
    LUXURY = "luxury"

    # New evergreen niches
    TRUE_CRIME = "true-crime"
    PSYCHOLOGY_FACTS = "psychology-facts"
    HISTORY = "history"
    MOTIVATION = "motivation"
    SPACE_ASTRONOMY = "space-astronomy"
    CONSPIRACY_MYSTERIES = "conspiracy-mysteries"
    ANIMAL_FACTS = "animal-facts"
    HEALTH_WELLNESS = "health-wellness"
    RELATIONSHIP_ADVICE = "relationship-advice"
    TECH_GADGETS = "tech-gadgets"
    LIFE_HACKS = "life-hacks"
    MYTHOLOGY_FOLKLORE = "mythology-folklore"
    UNSOLVED_MYSTERIES = "unsolved-mysteries"
    GEOGRAPHY_FACTS = "geography-facts"
    AI_FUTURE_TECH = "ai-future-tech"
    PHILOSOPHY = "philosophy"
    BOOK_SUMMARIES = "book-summaries"
    CELEBRITY_NET_WORTH = "celebrity-net-worth"
    SURVIVAL_TIPS = "survival-tips"
    SLEEP_RELAXATION = "sleep-relaxation"
    NETFLIX_RECOMMENDATIONS = "netflix-recommendations"
    MOCKUMENTARY_HOWMADE = "mockumentary-howmade"

    @property
    def display_name(self) -> str:
        """Human-readable name for the niche."""
        return {
            Niche.SCARY_STORIES: "Scary Stories",
            Niche.FINANCE: "Finance",
            Niche.LUXURY: "Luxury",
            Niche.TRUE_CRIME: "True Crime",
            Niche.PSYCHOLOGY_FACTS: "Psychology Facts",
            Niche.HISTORY: "History",
            Niche.MOTIVATION: "Motivation",
            Niche.SPACE_ASTRONOMY: "Space & Astronomy",
            Niche.CONSPIRACY_MYSTERIES: "Conspiracy & Mysteries",
            Niche.ANIMAL_FACTS: "Animal Facts",
            Niche.HEALTH_WELLNESS: "Health & Wellness",
            Niche.RELATIONSHIP_ADVICE: "Relationship Advice",
            Niche.TECH_GADGETS: "Tech & Gadgets",
            Niche.LIFE_HACKS: "Life Hacks",
            Niche.MYTHOLOGY_FOLKLORE: "Mythology & Folklore",
            Niche.UNSOLVED_MYSTERIES: "Unsolved Mysteries",
            Niche.GEOGRAPHY_FACTS: "Geography Facts",
            Niche.AI_FUTURE_TECH: "AI & Future Tech",
            Niche.PHILOSOPHY: "Philosophy",
            Niche.BOOK_SUMMARIES: "Book Summaries",
            Niche.CELEBRITY_NET_WORTH: "Celebrity Net Worth",
            Niche.SURVIVAL_TIPS: "Survival Tips",
            Niche.SLEEP_RELAXATION: "Sleep & Relaxation",
            Niche.NETFLIX_RECOMMENDATIONS: "Netflix Recommendations",
            Niche.MOCKUMENTARY_HOWMADE: "Mockumentary How It's Made",
        }[self]

    @property
    def subreddits(self) -> list[str]:
        """Default subreddits for content scraping."""
        return {
            Niche.SCARY_STORIES: ["nosleep", "LetsNotMeet", "creepypasta"],
            Niche.FINANCE: ["personalfinance", "financialindependence", "investing"],
            Niche.LUXURY: ["luxury", "watches", "cars"],
            Niche.TRUE_CRIME: ["TrueCrime", "UnresolvedMysteries", "serialkillers"],
            Niche.PSYCHOLOGY_FACTS: ["psychology", "AskScience", "todayilearned"],
            Niche.HISTORY: ["history", "HistoryPorn", "AskHistorians"],
            Niche.MOTIVATION: ["GetMotivated", "DecidingToBeBetter", "selfimprovement"],
            Niche.SPACE_ASTRONOMY: ["space", "Astronomy", "astrophotography"],
            Niche.CONSPIRACY_MYSTERIES: [
                "conspiracy",
                "HighStrangeness",
                "Glitch_in_the_Matrix",
            ],
            Niche.ANIMAL_FACTS: [
                "Awwducational",
                "NatureIsFuckingLit",
                "interestingasfuck",
            ],
            Niche.HEALTH_WELLNESS: ["HealthyFood", "Fitness", "nutrition"],
            Niche.RELATIONSHIP_ADVICE: [
                "relationship_advice",
                "dating_advice",
                "AskMen",
            ],
            Niche.TECH_GADGETS: ["gadgets", "technology", "Android"],
            Niche.LIFE_HACKS: ["lifehacks", "LifeProTips", "productivity"],
            Niche.MYTHOLOGY_FOLKLORE: ["mythology", "folklore", "Lovecraft"],
            Niche.UNSOLVED_MYSTERIES: ["UnsolvedMysteries", "RBI", "Disappearances"],
            Niche.GEOGRAPHY_FACTS: ["geography", "MapPorn", "todayilearned"],
            Niche.AI_FUTURE_TECH: ["Futurology", "artificial", "singularity"],
            Niche.PHILOSOPHY: ["philosophy", "Stoicism", "Existentialism"],
            Niche.BOOK_SUMMARIES: ["books", "booksuggestions", "52book"],
            Niche.CELEBRITY_NET_WORTH: ["Celebs", "entertainment", "popculturechat"],
            Niche.SURVIVAL_TIPS: ["Survival", "preppers", "Bushcraft"],
            Niche.SLEEP_RELAXATION: ["sleep", "Meditation", "asmr"],
            Niche.NETFLIX_RECOMMENDATIONS: [
                "NetflixBestOf",
                "television",
                "MovieSuggestions",
            ],
            Niche.MOCKUMENTARY_HOWMADE: [
                "InterdimensionalCable",
                "funny",
                "AbsurdHumor",
            ],
        }[self]


class Platform(str, Enum):
    """
    Target platforms for video output.

    Each platform has specific resolution, aspect ratio, and duration requirements.
    """

    YOUTUBE = "youtube"
    TIKTOK = "tiktok"

    @property
    def display_name(self) -> str:
        """Human-readable name for the platform."""
        return {
            Platform.YOUTUBE: "YouTube",
            Platform.TIKTOK: "TikTok",
        }[self]

    @property
    def resolution(self) -> tuple[int, int]:
        """Video resolution (width, height) for the platform."""
        return {
            Platform.YOUTUBE: (1920, 1080),  # 16:9
            Platform.TIKTOK: (1080, 1920),  # 9:16
        }[self]

    @property
    def aspect_ratio(self) -> str:
        """Aspect ratio string for the platform."""
        return {
            Platform.YOUTUBE: "16:9",
            Platform.TIKTOK: "9:16",
        }[self]

    @property
    def image_size(self) -> str:
        """Image generation size for the platform."""
        return {
            Platform.YOUTUBE: "1536x1024",  # Landscape
            Platform.TIKTOK: "1024x1536",  # Portrait
        }[self]

    @property
    def max_duration(self) -> int:
        """Maximum recommended duration in seconds."""
        return {
            Platform.YOUTUBE: 600,  # 10 minutes
            Platform.TIKTOK: 180,  # 3 minutes (though 60s is optimal)
        }[self]


class JobStatus(str, Enum):
    """
    Status of a content generation job.

    Jobs progress through these states during pipeline execution.
    """

    PENDING = "pending"
    SCRAPING = "scraping"
    ENHANCING = "enhancing"
    GENERATING_IMAGES = "generating_images"
    GENERATING_AUDIO = "generating_audio"
    ASSEMBLING_VIDEO = "assembling_video"
    GENERATING_THUMBNAILS = "generating_thumbnails"
    GENERATING_SUBTITLES = "generating_subtitles"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        """Whether this status represents a final state."""
        return self in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED)

    @property
    def is_active(self) -> bool:
        """Whether this status represents an active processing state."""
        return self not in (
            JobStatus.PENDING,
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
        )


class Voice(str, Enum):
    """
    Available Azure OpenAI TTS voices.

    These voices are available for the gpt-4o-mini-tts model.
    """

    ALLOY = "alloy"
    ECHO = "echo"
    FABLE = "fable"
    ONYX = "onyx"
    NOVA = "nova"
    SHIMMER = "shimmer"

    @property
    def description(self) -> str:
        """Description of the voice characteristics."""
        return {
            Voice.ALLOY: "Neutral, balanced voice",
            Voice.ECHO: "Warm, conversational voice",
            Voice.FABLE: "Expressive, dramatic voice",
            Voice.ONYX: "Deep, authoritative male voice",
            Voice.NOVA: "Warm, friendly female voice",
            Voice.SHIMMER: "Clear, professional female voice",
        }[self]


class ImageQuality(str, Enum):
    """Image generation quality settings."""

    STANDARD = "standard"
    HIGH = "high"
    HD = "hd"


class ContentSourceType(str, Enum):
    """
    Types of content sources for fetching raw content.

    Each source type represents a different platform or API
    that can provide content for video scripts.
    """

    REDDIT = "reddit"
    WIKIPEDIA = "wikipedia"
    YOUTUBE = "youtube"
    NEWS = "news"
    HACKER_NEWS = "hacker_news"
    OPEN_LIBRARY = "open_library"
    AI_GENERATED = "ai_generated"

    @property
    def display_name(self) -> str:
        """Human-readable name for the source type."""
        return {
            ContentSourceType.REDDIT: "Reddit",
            ContentSourceType.WIKIPEDIA: "Wikipedia",
            ContentSourceType.YOUTUBE: "YouTube",
            ContentSourceType.NEWS: "News APIs",
            ContentSourceType.HACKER_NEWS: "Hacker News",
            ContentSourceType.OPEN_LIBRARY: "OpenLibrary",
            ContentSourceType.AI_GENERATED: "AI Generated",
        }[self]

    @property
    def requires_api_key(self) -> bool:
        """Whether this source requires an API key."""
        return self in (
            ContentSourceType.YOUTUBE,
            ContentSourceType.NEWS,
        )


class ThumbnailConcept(str, Enum):
    """
    Thumbnail design concepts for A/B testing.

    Each concept represents a different visual approach to maximize CTR.
    """

    REACTION = "reaction"
    REVEAL = "reveal"
    VERSUS = "versus"
    BEFORE_AFTER = "before_after"
    COUNTDOWN = "countdown"
    MYSTERY = "mystery"
    WARNING = "warning"
    SECRET = "secret"

    @property
    def description(self) -> str:
        """Description of the thumbnail concept."""
        return {
            ThumbnailConcept.REACTION: "Person with shocked/amazed expression",
            ThumbnailConcept.REVEAL: "Subject being unveiled or discovered",
            ThumbnailConcept.VERSUS: "Two items/concepts side by side",
            ThumbnailConcept.BEFORE_AFTER: "Dramatic transformation visualization",
            ThumbnailConcept.COUNTDOWN: "Number with dramatic emphasis",
            ThumbnailConcept.MYSTERY: "Obscured subject with intrigue",
            ThumbnailConcept.WARNING: "Alert/danger symbolism",
            ThumbnailConcept.SECRET: "Hidden information being revealed",
        }[self]

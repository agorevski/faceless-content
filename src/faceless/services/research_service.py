"""
Deep research service for the Faceless Content Pipeline.

This service performs comprehensive research on topics using AI models,
web search integration, and multi-source fact verification to create
high-quality, authoritative content.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from faceless.clients.azure_openai import AzureOpenAIClient
from faceless.config import get_settings
from faceless.core.enums import Niche
from faceless.core.exceptions import ClientError
from faceless.utils.logging import LoggerMixin


class ResearchDepth(str, Enum):
    """Research depth levels for topic investigation."""

    QUICK = "quick"  # 2-5 min equivalent, basic facts
    STANDARD = "standard"  # 10-15 min, comprehensive
    DEEP = "deep"  # 30-60 min, expert-level
    INVESTIGATIVE = "investigative"  # 2-4 hours, primary sources


@dataclass
class ResearchSource:
    """A source used in research."""

    title: str
    url: str | None = None
    source_type: str = "ai_generated"  # ai_generated, web, academic, primary
    credibility_score: float = 0.7
    excerpt: str = ""


@dataclass
class ResearchFinding:
    """A single research finding or fact."""

    content: str
    category: str  # fact, statistic, quote, insight, counterargument
    importance: float = 0.5  # 0-1 scale
    sources: list[ResearchSource] = field(default_factory=list)
    verified: bool = False


@dataclass
class ResearchOutput:
    """Complete research output for a topic."""

    topic: str
    niche: Niche
    depth: ResearchDepth
    researched_at: datetime = field(default_factory=datetime.now)

    # Core findings
    key_findings: list[ResearchFinding] = field(default_factory=list)
    statistics: list[ResearchFinding] = field(default_factory=list)
    expert_quotes: list[ResearchFinding] = field(default_factory=list)
    counterarguments: list[ResearchFinding] = field(default_factory=list)

    # Contextual information
    historical_context: str = ""
    recent_developments: str = ""
    why_it_matters: str = ""

    # Content suggestions
    suggested_hook: str = ""
    suggested_structure: list[str] = field(default_factory=list)
    visual_opportunities: list[str] = field(default_factory=list)

    # Metadata
    sources: list[ResearchSource] = field(default_factory=list)
    confidence_score: float = 0.0
    follow_up_topics: list[str] = field(default_factory=list)
    multi_video_potential: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "topic": self.topic,
            "niche": self.niche.value,
            "depth": self.depth.value,
            "researched_at": self.researched_at.isoformat(),
            "key_findings": [
                {
                    "content": f.content,
                    "category": f.category,
                    "importance": f.importance,
                }
                for f in self.key_findings
            ],
            "statistics": [
                {"content": f.content, "importance": f.importance}
                for f in self.statistics
            ],
            "expert_quotes": [{"content": f.content} for f in self.expert_quotes],
            "counterarguments": [{"content": f.content} for f in self.counterarguments],
            "historical_context": self.historical_context,
            "recent_developments": self.recent_developments,
            "why_it_matters": self.why_it_matters,
            "suggested_hook": self.suggested_hook,
            "suggested_structure": self.suggested_structure,
            "visual_opportunities": self.visual_opportunities,
            "sources": [
                {"title": s.title, "url": s.url, "type": s.source_type}
                for s in self.sources
            ],
            "confidence_score": self.confidence_score,
            "follow_up_topics": self.follow_up_topics,
            "multi_video_potential": self.multi_video_potential,
        }


# Research prompts by depth level
RESEARCH_PROMPTS = {
    ResearchDepth.QUICK: """You are a research assistant. Provide quick, factual research on the topic.

Focus on:
- 3-5 key facts
- 1-2 surprising statistics
- Basic context

Keep it concise and accurate.""",
    ResearchDepth.STANDARD: """You are an expert research assistant. Provide comprehensive research on the topic.

Focus on:
- 5-10 key findings with importance ranking
- 3-5 statistics with sources
- Historical context
- Recent developments (last 1-2 years)
- 2-3 counterarguments or alternative perspectives
- Expert quotes or perspectives

Be thorough but organized.""",
    ResearchDepth.DEEP: """You are a senior research analyst. Provide expert-level research on the topic.

Focus on:
- 10-15 key findings with detailed analysis
- 5-10 statistics with source citations
- Complete historical timeline
- Recent developments with analysis
- All major counterarguments and rebuttals
- Multiple expert perspectives
- Original insights and connections
- Content structure recommendations
- Visual storytelling opportunities

Be comprehensive and analytical. Cite sources where possible.""",
    ResearchDepth.INVESTIGATIVE: """You are an investigative researcher. Provide exhaustive research on the topic.

Focus on:
- All relevant facts and findings
- Complete statistical analysis
- Full historical context and timeline
- Every perspective and counterargument
- Primary source references
- Expert analysis and quotes
- Hidden connections and insights
- Multi-video content potential
- Series structure recommendations

Leave no stone unturned. This research should support documentary-level content.""",
}


class DeepResearchService(LoggerMixin):
    """
    Service for conducting deep research on topics.

    Performs comprehensive research using AI models to generate
    authoritative, well-researched content foundations.

    Features:
    - Configurable research depth levels
    - Multi-perspective analysis
    - Fact synthesis and verification
    - Content structure recommendations
    - Visual opportunity identification

    Example:
        >>> service = DeepResearchService()
        >>> research = service.research_topic(
        ...     topic="Why diamonds are artificially expensive",
        ...     niche=Niche.FINANCE,
        ...     depth=ResearchDepth.STANDARD,
        ... )
    """

    def __init__(self, client: AzureOpenAIClient | None = None) -> None:
        """
        Initialize research service.

        Args:
            client: Optional Azure OpenAI client
        """
        self._client = client or AzureOpenAIClient()
        self._settings = get_settings()

    def research_topic(
        self,
        topic: str,
        niche: Niche,
        depth: ResearchDepth = ResearchDepth.STANDARD,
        additional_context: str = "",
    ) -> ResearchOutput:
        """
        Conduct research on a topic.

        Args:
            topic: The topic to research
            niche: Content niche for context
            depth: Research depth level
            additional_context: Optional additional context or focus areas

        Returns:
            ResearchOutput with comprehensive findings
        """
        self.logger.info(
            "Starting research",
            topic=topic,
            niche=niche.value,
            depth=depth.value,
        )

        # Build research prompt
        user_prompt = self._build_research_prompt(
            topic, niche, depth, additional_context
        )
        system_prompt = RESEARCH_PROMPTS[depth]

        # Get max tokens based on depth
        max_tokens = {
            ResearchDepth.QUICK: 1500,
            ResearchDepth.STANDARD: 3000,
            ResearchDepth.DEEP: 5000,
            ResearchDepth.INVESTIGATIVE: 8000,
        }[depth]

        try:
            result = self._client.chat_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=max_tokens,
            )

            research_output = self._parse_research_result(result, topic, niche, depth)

            self.logger.info(
                "Research completed",
                topic=topic,
                findings_count=len(research_output.key_findings),
                confidence=research_output.confidence_score,
            )

            return research_output

        except Exception as e:
            self.logger.error("Research failed", topic=topic, error=str(e))
            raise ClientError(f"Research failed for topic '{topic}': {e}") from e

    def expand_topic_questions(
        self,
        topic: str,
        niche: Niche,
        count: int = 20,
    ) -> list[str]:
        """
        Generate comprehensive questions that research should answer.

        Args:
            topic: The main topic
            niche: Content niche
            count: Number of questions to generate

        Returns:
            List of research questions
        """
        prompt = f"""For a {niche.display_name} video about "{topic}", generate {count} questions
that comprehensive coverage would need to answer.

Include:
- Basic "what is" questions
- "Why" and "how" questions
- Historical questions
- Current state questions
- Controversial or debatable aspects
- Lesser-known facts
- Expert perspectives to explore
- Common misconceptions to address

Return as a JSON array of strings."""

        try:
            result = self._client.chat_json(
                system_prompt="You are a research planner. Generate comprehensive research questions.",
                user_prompt=prompt,
                temperature=0.8,
            )

            if isinstance(result, list):
                return list(result[:count])
            if "questions" in result:
                return list(result["questions"][:count])
            return []

        except Exception as e:
            self.logger.warning("Question expansion failed", error=str(e))
            return []

    def verify_facts(
        self,
        facts: list[str],
        topic: str,
    ) -> list[dict[str, Any]]:
        """
        Verify a list of facts for accuracy.

        Args:
            facts: List of factual claims to verify
            topic: Topic context

        Returns:
            List of verification results
        """
        prompt = f"""Verify these facts about "{topic}":

{chr(10).join(f'{i+1}. {fact}' for i, fact in enumerate(facts))}

For each fact, provide:
- verified: true/false/uncertain
- confidence: 0-1 score
- correction: corrected version if needed
- notes: any caveats or context

Return as JSON array."""

        try:
            result = self._client.chat_json(
                system_prompt="You are a fact-checker. Verify claims with high accuracy.",
                user_prompt=prompt,
                temperature=0.3,  # Lower temperature for accuracy
            )

            if isinstance(result, list):
                return list(result)
            if "facts" in result:
                return list(result["facts"])
            return []

        except Exception as e:
            self.logger.warning("Fact verification failed", error=str(e))
            return []

    def generate_content_structure(
        self,
        research: ResearchOutput,
        target_duration: int = 600,  # 10 minutes
    ) -> dict[str, Any]:
        """
        Generate optimal content structure from research.

        Args:
            research: Completed research output
            target_duration: Target video duration in seconds

        Returns:
            Recommended content structure
        """
        prompt = f"""Based on this research about "{research.topic}", create an optimal video structure.

Key findings: {[f.content for f in research.key_findings[:5]]}
Statistics: {[f.content for f in research.statistics[:3]]}
Hook suggestion: {research.suggested_hook}

Target duration: {target_duration} seconds ({target_duration // 60} minutes)

Return JSON with:
{{
    "hook": "Opening hook (first 10-15 seconds)",
    "promise": "What viewers will learn",
    "sections": [
        {{
            "title": "Section name",
            "duration_seconds": 60,
            "key_points": ["point 1", "point 2"],
            "visual_suggestion": "What to show"
        }}
    ],
    "conclusion": "Ending summary",
    "cta": "Call to action"
}}"""

        try:
            result = self._client.chat_json(
                system_prompt="You are a video content strategist. Create engaging video structures.",
                user_prompt=prompt,
                temperature=0.7,
            )
            return result

        except Exception as e:
            self.logger.warning("Structure generation failed", error=str(e))
            return {}

    def _build_research_prompt(
        self,
        topic: str,
        niche: Niche,
        depth: ResearchDepth,
        additional_context: str,
    ) -> str:
        """Build the research request prompt."""
        niche_context = {
            Niche.SCARY_STORIES: "Focus on atmospheric details, psychological elements, and building dread.",
            Niche.FINANCE: "Include specific numbers, percentages, and actionable insights.",
            Niche.LUXURY: "Emphasize exclusivity, craftsmanship, and aspirational elements.",
            Niche.TRUE_CRIME: "Focus on factual accuracy, timeline, and investigative details.",
            Niche.PSYCHOLOGY_FACTS: "Include scientific studies and practical applications.",
            Niche.HISTORY: "Emphasize chronology, cause-effect, and lesser-known details.",
            Niche.MOTIVATION: "Focus on actionable strategies and success stories.",
            Niche.SPACE_ASTRONOMY: "Include scale comparisons and mind-blowing facts.",
            Niche.CONSPIRACY_MYSTERIES: "Present multiple perspectives and evidence objectively.",
            Niche.ANIMAL_FACTS: "Include surprising behaviors and evolutionary context.",
            Niche.HEALTH_WELLNESS: "Cite scientific sources and include practical tips.",
            Niche.RELATIONSHIP_ADVICE: "Focus on psychology-backed advice and real scenarios.",
            Niche.TECH_GADGETS: "Include specs, comparisons, and future implications.",
            Niche.LIFE_HACKS: "Focus on practical, immediately actionable tips.",
            Niche.MYTHOLOGY_FOLKLORE: "Include cultural context and storytelling elements.",
            Niche.UNSOLVED_MYSTERIES: "Present all theories objectively with evidence.",
            Niche.GEOGRAPHY_FACTS: "Include comparative data and visual opportunities.",
            Niche.AI_FUTURE_TECH: "Balance hype with realistic timeline expectations.",
            Niche.PHILOSOPHY: "Make complex ideas accessible with examples.",
            Niche.BOOK_SUMMARIES: "Capture key insights and actionable takeaways.",
            Niche.CELEBRITY_NET_WORTH: "Include income sources and financial decisions.",
            Niche.SURVIVAL_TIPS: "Focus on practical, life-saving information.",
            Niche.SLEEP_RELAXATION: "Include science-backed techniques and calming elements.",
        }

        context = niche_context.get(niche, "")

        return f"""Research Topic: {topic}
Niche: {niche.display_name}
Research Depth: {depth.value}

Niche-Specific Focus: {context}

{f'Additional Context: {additional_context}' if additional_context else ''}

Provide your research as JSON with this structure:
{{
    "key_findings": [
        {{"content": "finding text", "category": "fact|statistic|insight", "importance": 0.9}}
    ],
    "statistics": [
        {{"content": "statistic with number", "source": "source name", "importance": 0.8}}
    ],
    "expert_quotes": [
        {{"content": "quote or paraphrase", "source": "expert/organization name"}}
    ],
    "counterarguments": [
        {{"content": "opposing view or nuance", "response": "how to address it"}}
    ],
    "historical_context": "Background and timeline",
    "recent_developments": "What's new in the last 1-2 years",
    "why_it_matters": "Why audience should care",
    "suggested_hook": "Attention-grabbing opening line",
    "suggested_structure": ["Section 1", "Section 2", "Section 3"],
    "visual_opportunities": ["Visual idea 1", "Visual idea 2"],
    "follow_up_topics": ["Related topic 1", "Related topic 2"],
    "multi_video_potential": true/false,
    "confidence_score": 0.85
}}"""

    def _parse_research_result(
        self,
        result: dict[str, Any],
        topic: str,
        niche: Niche,
        depth: ResearchDepth,
    ) -> ResearchOutput:
        """Parse AI response into ResearchOutput."""
        output = ResearchOutput(
            topic=topic,
            niche=niche,
            depth=depth,
        )

        # Parse key findings
        for finding in result.get("key_findings", []):
            if isinstance(finding, dict):
                output.key_findings.append(
                    ResearchFinding(
                        content=finding.get("content", ""),
                        category=finding.get("category", "fact"),
                        importance=float(finding.get("importance", 0.5)),
                    )
                )

        # Parse statistics
        for stat in result.get("statistics", []):
            if isinstance(stat, dict):
                source = ResearchSource(
                    title=stat.get("source", "Research"),
                    source_type="ai_generated",
                )
                output.statistics.append(
                    ResearchFinding(
                        content=stat.get("content", ""),
                        category="statistic",
                        importance=float(stat.get("importance", 0.7)),
                        sources=[source],
                    )
                )

        # Parse expert quotes
        for quote in result.get("expert_quotes", []):
            if isinstance(quote, dict):
                source = ResearchSource(
                    title=quote.get("source", "Expert"),
                    source_type="ai_generated",
                )
                output.expert_quotes.append(
                    ResearchFinding(
                        content=quote.get("content", ""),
                        category="quote",
                        sources=[source],
                    )
                )

        # Parse counterarguments
        for counter in result.get("counterarguments", []):
            if isinstance(counter, dict):
                output.counterarguments.append(
                    ResearchFinding(
                        content=counter.get("content", ""),
                        category="counterargument",
                    )
                )

        # Parse text fields
        output.historical_context = result.get("historical_context", "")
        output.recent_developments = result.get("recent_developments", "")
        output.why_it_matters = result.get("why_it_matters", "")
        output.suggested_hook = result.get("suggested_hook", "")

        # Parse lists
        output.suggested_structure = result.get("suggested_structure", [])
        output.visual_opportunities = result.get("visual_opportunities", [])
        output.follow_up_topics = result.get("follow_up_topics", [])

        # Parse metadata
        output.multi_video_potential = result.get("multi_video_potential", False)
        output.confidence_score = float(result.get("confidence_score", 0.7))

        return output

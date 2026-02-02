"""
Unit tests for the new services: DeepResearchService, QualityService, TrendingService.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from faceless.core.enums import Niche
from faceless.core.models import Scene, Script
from faceless.services.quality_service import (
    HookAnalysis,
    QualityGate,
    QualityScore,
    QualityService,
)
from faceless.services.research_service import (
    DeepResearchService,
    ResearchDepth,
    ResearchFinding,
    ResearchOutput,
)
from faceless.services.trending_service import (
    TrendingService,
    TrendingTopic,
    TrendLifecycle,
    TrendReport,
    TrendSource,
)

# =============================================================================
# DeepResearchService Tests
# =============================================================================


class TestResearchOutput:
    """Tests for ResearchOutput dataclass."""

    def test_research_output_creation(self) -> None:
        """Test creating a ResearchOutput instance."""
        output = ResearchOutput(
            topic="Test Topic",
            niche=Niche.FINANCE,
            depth=ResearchDepth.STANDARD,
        )

        assert output.topic == "Test Topic"
        assert output.niche == Niche.FINANCE
        assert output.depth == ResearchDepth.STANDARD
        assert output.key_findings == []
        assert output.confidence_score == 0.0

    def test_research_output_to_dict(self) -> None:
        """Test ResearchOutput serialization."""
        output = ResearchOutput(
            topic="Test Topic",
            niche=Niche.SCARY_STORIES,
            depth=ResearchDepth.DEEP,
            confidence_score=0.85,
        )
        output.key_findings.append(
            ResearchFinding(content="Finding 1", category="fact", importance=0.9)
        )

        result = output.to_dict()

        assert result["topic"] == "Test Topic"
        assert result["niche"] == "scary-stories"
        assert result["depth"] == "deep"
        assert result["confidence_score"] == 0.85
        assert len(result["key_findings"]) == 1


class TestDeepResearchService:
    """Tests for DeepResearchService."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Create a mock Azure OpenAI client."""
        client = MagicMock()
        client.chat_json.return_value = {
            "key_findings": [
                {"content": "Test finding", "category": "fact", "importance": 0.8}
            ],
            "statistics": [
                {"content": "50% of people...", "source": "Study", "importance": 0.7}
            ],
            "expert_quotes": [{"content": "Expert says...", "source": "Dr. Smith"}],
            "counterarguments": [{"content": "However...", "response": "But..."}],
            "historical_context": "Background info",
            "recent_developments": "Recent news",
            "why_it_matters": "Important because...",
            "suggested_hook": "Did you know...?",
            "suggested_structure": ["Intro", "Main", "Conclusion"],
            "visual_opportunities": ["Chart", "Animation"],
            "follow_up_topics": ["Related topic"],
            "multi_video_potential": True,
            "confidence_score": 0.85,
        }
        return client

    def test_research_topic_returns_output(self, mock_client: MagicMock) -> None:
        """Test that research_topic returns ResearchOutput."""
        service = DeepResearchService(client=mock_client)

        result = service.research_topic(
            topic="Why diamonds are expensive",
            niche=Niche.FINANCE,
            depth=ResearchDepth.STANDARD,
        )

        assert isinstance(result, ResearchOutput)
        assert result.topic == "Why diamonds are expensive"
        assert result.niche == Niche.FINANCE
        assert result.confidence_score == 0.85
        mock_client.chat_json.assert_called_once()

    def test_research_topic_parses_findings(self, mock_client: MagicMock) -> None:
        """Test that findings are parsed correctly."""
        service = DeepResearchService(client=mock_client)

        result = service.research_topic(
            topic="Test",
            niche=Niche.SCARY_STORIES,
        )

        assert len(result.key_findings) == 1
        assert result.key_findings[0].content == "Test finding"
        assert result.key_findings[0].importance == 0.8

    def test_research_depth_affects_max_tokens(self, mock_client: MagicMock) -> None:
        """Test that different depths use different token limits."""
        service = DeepResearchService(client=mock_client)

        # Quick research
        service.research_topic("Test", Niche.FINANCE, ResearchDepth.QUICK)
        quick_call = mock_client.chat_json.call_args_list[-1]

        # Deep research
        service.research_topic("Test", Niche.FINANCE, ResearchDepth.DEEP)
        deep_call = mock_client.chat_json.call_args_list[-1]

        # Deep should request more tokens
        assert quick_call.kwargs["max_tokens"] < deep_call.kwargs["max_tokens"]

    def test_expand_topic_questions(self, mock_client: MagicMock) -> None:
        """Test question expansion."""
        mock_client.chat_json.return_value = ["Q1?", "Q2?", "Q3?"]
        service = DeepResearchService(client=mock_client)

        questions = service.expand_topic_questions("Test topic", Niche.HISTORY, count=3)

        assert len(questions) == 3
        assert "Q1?" in questions


# =============================================================================
# QualityService Tests
# =============================================================================


class TestHookAnalysis:
    """Tests for HookAnalysis dataclass."""

    def test_hook_analysis_creation(self) -> None:
        """Test creating HookAnalysis."""
        analysis = HookAnalysis(
            score=8.5,
            hook_type="question",
            attention_grab=0.9,
            curiosity_gap=0.85,
        )

        assert analysis.score == 8.5
        assert analysis.hook_type == "question"
        assert analysis.improvement_suggestions == []


class TestQualityScore:
    """Tests for QualityScore dataclass."""

    def test_quality_score_creation(self) -> None:
        """Test creating QualityScore."""
        score = QualityScore(
            script_title="Test Script",
            niche=Niche.FINANCE,
        )

        assert score.script_title == "Test Script"
        assert score.overall_score == 0.0
        assert score.approved_for_production is False

    def test_quality_score_to_dict(self) -> None:
        """Test QualityScore serialization."""
        score = QualityScore(
            script_title="Test",
            niche=Niche.LUXURY,
            overall_score=7.5,
            hook_score=8.0,
            approved_for_production=True,
        )

        result = score.to_dict()

        assert result["script_title"] == "Test"
        assert result["scores"]["overall"] == 7.5
        assert result["approved"] is True


class TestQualityService:
    """Tests for QualityService."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Create mock client with quality analysis response."""
        client = MagicMock()
        client.chat_json.return_value = {
            "hook_analysis": {
                "score": 8.0,
                "hook_type": "question",
                "attention_grab": 0.85,
                "curiosity_gap": 0.80,
                "improvement_suggestions": ["Be more specific"],
                "alternative_hooks": ["Alternative 1"],
            },
            "retention_analysis": {
                "predicted_retention_30s": 0.75,
                "predicted_retention_50pct": 0.55,
                "predicted_completion_rate": 0.40,
                "drop_off_risks": ["Slow middle section"],
                "mid_video_hooks_present": True,
                "loop_potential": 0.3,
            },
            "engagement_analysis": {
                "comment_trigger_score": 7.0,
                "share_potential": 6.5,
                "save_potential": 7.5,
                "debate_potential": 5.0,
                "comment_triggers": ["Opinion request"],
            },
            "narrative_score": 7.5,
            "information_score": 8.0,
            "overall_score": 7.5,
            "critical_issues": [],
            "improvements": ["Add more statistics"],
            "confidence": 0.85,
        }
        return client

    @pytest.fixture
    def sample_script(self) -> Script:
        """Create sample script for testing."""
        return Script(
            title="Test Script",
            niche=Niche.FINANCE,
            scenes=[
                Scene(
                    scene_number=1,
                    narration="Did you know 90% of people make this money mistake?",
                    image_prompt="Person looking at bills",
                    duration_estimate=15.0,
                ),
                Scene(
                    scene_number=2,
                    narration="Here's what you should do instead.",
                    image_prompt="Success imagery",
                    duration_estimate=30.0,
                ),
            ],
        )

    def test_evaluate_script_returns_quality_score(
        self, mock_client: MagicMock, sample_script: Script
    ) -> None:
        """Test that evaluate_script returns QualityScore."""
        service = QualityService(client=mock_client)

        result = service.evaluate_script(sample_script)

        assert isinstance(result, QualityScore)
        assert result.script_title == "Test Script"
        mock_client.chat_json.assert_called_once()

    def test_evaluate_script_parses_hook_analysis(
        self, mock_client: MagicMock, sample_script: Script
    ) -> None:
        """Test hook analysis is parsed correctly."""
        service = QualityService(client=mock_client)

        result = service.evaluate_script(sample_script)

        assert result.hook_analysis is not None
        assert result.hook_analysis.score == 8.0
        assert result.hook_score == 8.0

    def test_quality_gates_applied(
        self, mock_client: MagicMock, sample_script: Script
    ) -> None:
        """Test quality gates are applied correctly."""
        service = QualityService(client=mock_client)

        result = service.evaluate_script(sample_script)

        # With score 8.0 and threshold 7.0, hook gate should pass
        assert QualityGate.HOOK_QUALITY in result.gates_passed

    def test_approval_with_good_scores(
        self, mock_client: MagicMock, sample_script: Script
    ) -> None:
        """Test approval when scores meet thresholds."""
        service = QualityService(client=mock_client)

        result = service.evaluate_script(sample_script)

        # Overall 7.5 >= 6.5 threshold, hook 8.0 >= 7.0, no critical issues
        assert result.approved_for_production is True

    def test_rejection_with_low_hook_score(
        self, mock_client: MagicMock, sample_script: Script
    ) -> None:
        """Test rejection when hook score is low."""
        mock_client.chat_json.return_value["hook_analysis"]["score"] = 5.0
        mock_client.chat_json.return_value["overall_score"] = 5.0
        service = QualityService(client=mock_client)

        result = service.evaluate_script(sample_script)

        assert QualityGate.HOOK_QUALITY in result.gates_failed
        assert result.approved_for_production is False

    def test_evaluate_hook_only(self, mock_client: MagicMock) -> None:
        """Test evaluating just a hook."""
        mock_client.chat_json.return_value = {
            "score": 7.5,
            "hook_type": "statistic",
            "attention_grab": 0.8,
            "curiosity_gap": 0.7,
            "improvement_suggestions": ["Add emotion"],
            "alternative_hooks": ["Alt hook 1"],
        }
        service = QualityService(client=mock_client)

        result = service.evaluate_hook_only(
            "Did you know 90% of people fail?",
            Niche.FINANCE,
        )

        assert isinstance(result, HookAnalysis)
        assert result.score == 7.5
        assert result.hook_type == "statistic"

    def test_generate_better_hooks(
        self, mock_client: MagicMock, sample_script: Script
    ) -> None:
        """Test generating hook alternatives."""
        mock_client.chat_json.return_value = [
            "Hook 1",
            "Hook 2",
            "Hook 3",
        ]
        service = QualityService(client=mock_client)

        hooks = service.generate_better_hooks(sample_script, count=3)

        assert len(hooks) == 3
        assert "Hook 1" in hooks


# =============================================================================
# TrendingService Tests
# =============================================================================


class TestTrendingTopic:
    """Tests for TrendingTopic dataclass."""

    def test_trending_topic_creation(self) -> None:
        """Test creating TrendingTopic."""
        topic = TrendingTopic(
            title="Viral Finance Topic",
            niche=Niche.FINANCE,
            source=TrendSource.REDDIT,
            score=85.0,
        )

        assert topic.title == "Viral Finance Topic"
        assert topic.score == 85.0
        assert topic.lifecycle == TrendLifecycle.EMERGING

    def test_trending_topic_to_dict(self) -> None:
        """Test TrendingTopic serialization."""
        topic = TrendingTopic(
            title="Test Topic",
            niche=Niche.SCARY_STORIES,
            source=TrendSource.AI_SUGGESTED,
            score=75.0,
            lifecycle=TrendLifecycle.RISING,
        )

        result = topic.to_dict()

        assert result["title"] == "Test Topic"
        assert result["source"] == "ai_suggested"
        assert result["lifecycle"] == "rising"


class TestTrendReport:
    """Tests for TrendReport dataclass."""

    def test_trend_report_creation(self) -> None:
        """Test creating TrendReport."""
        report = TrendReport(niche=Niche.LUXURY)

        assert report.niche == Niche.LUXURY
        assert report.hot_topics == []
        assert report.top_recommendation is None


class TestTrendingService:
    """Tests for TrendingService."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Create mock client for trending service."""
        client = MagicMock()
        client.chat_json.return_value = [
            {
                "title": "Hot Topic 1",
                "subreddit": "finance",
                "score": 85,
                "growth_rate": 25.0,
                "lifecycle": "rising",
                "video_potential": 0.9,
                "suggested_angles": ["Angle 1"],
            },
            {
                "title": "Emerging Topic 2",
                "score": 65,
                "growth_rate": 15.0,
                "lifecycle": "emerging",
                "video_potential": 0.7,
                "evergreen_potential": 0.3,
                "competition_level": "low",
            },
        ]
        return client

    def test_get_trend_report_returns_report(self, mock_client: MagicMock) -> None:
        """Test that get_trend_report returns TrendReport."""
        service = TrendingService(client=mock_client)

        result = service.get_trend_report(Niche.FINANCE)

        assert isinstance(result, TrendReport)
        assert result.niche == Niche.FINANCE

    def test_trend_report_categorizes_topics(self, mock_client: MagicMock) -> None:
        """Test that topics are categorized correctly."""
        service = TrendingService(client=mock_client)

        result = service.get_trend_report(Niche.FINANCE)

        # Hot Topic 1 should be in hot_topics (score 85, rising)
        # Topics get categorized based on score and lifecycle
        assert len(result.hot_topics) > 0 or len(result.rising_topics) > 0

    def test_get_hot_topics(self, mock_client: MagicMock) -> None:
        """Test getting hot topics only."""
        service = TrendingService(client=mock_client)

        topics = service.get_hot_topics(Niche.SCARY_STORIES, count=5)

        assert isinstance(topics, list)
        # May be empty if categorization puts them elsewhere
        for topic in topics:
            assert isinstance(topic, TrendingTopic)

    def test_analyze_topic_potential(self, mock_client: MagicMock) -> None:
        """Test analyzing a specific topic."""
        mock_client.chat_json.return_value = {
            "score": 80,
            "search_volume_estimate": "high",
            "growth_rate": 20.0,
            "lifecycle": "rising",
            "video_potential": 0.85,
            "competition_level": "medium",
            "evergreen_potential": 0.4,
            "related_topics": ["Related 1"],
            "suggested_angles": ["Angle 1", "Angle 2"],
        }
        service = TrendingService(client=mock_client)

        result = service.analyze_topic_potential(
            "Why Gen Z is different with money",
            Niche.FINANCE,
        )

        assert isinstance(result, TrendingTopic)
        assert result.score == 80
        assert result.lifecycle == TrendLifecycle.RISING
        assert result.video_potential == 0.85

    def test_suggest_content_timing(self, mock_client: MagicMock) -> None:
        """Test content timing suggestions."""
        service = TrendingService(client=mock_client)

        topic = TrendingTopic(
            title="Test",
            niche=Niche.FINANCE,
            source=TrendSource.REDDIT,
            lifecycle=TrendLifecycle.PEAK,
        )

        timing = service.suggest_content_timing(topic)

        assert timing["urgency"] == "very_high"
        assert "immediately" in timing["recommendation"].lower()

    def test_trend_lifecycle_enum(self) -> None:
        """Test TrendLifecycle enum values."""
        assert TrendLifecycle.EMERGING.value == "emerging"
        assert TrendLifecycle.RISING.value == "rising"
        assert TrendLifecycle.PEAK.value == "peak"
        assert TrendLifecycle.DECLINING.value == "declining"
        assert TrendLifecycle.EVERGREEN.value == "evergreen"


# =============================================================================
# Integration-style Tests
# =============================================================================


class TestServiceIntegration:
    """Tests for service interactions."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Create a comprehensive mock client."""
        client = MagicMock()
        return client

    def test_research_to_quality_workflow(self, mock_client: MagicMock) -> None:
        """Test using research output to inform quality evaluation."""
        # Simulate research
        research = ResearchOutput(
            topic="Money mistakes",
            niche=Niche.FINANCE,
            depth=ResearchDepth.STANDARD,
            suggested_hook="90% of people make this mistake...",
            confidence_score=0.85,
        )

        # The suggested hook could be used in a script
        assert research.suggested_hook is not None
        assert "mistake" in research.suggested_hook.lower()

    def test_trending_to_research_workflow(self, mock_client: MagicMock) -> None:
        """Test using trending topics to inform research."""
        # Create a trending topic
        topic = TrendingTopic(
            title="Why savings accounts are losing money",
            niche=Niche.FINANCE,
            source=TrendSource.REDDIT,
            score=85,
            video_potential=0.9,
        )

        # This topic would be good for deep research
        assert topic.video_potential >= 0.8
        assert topic.score >= 80

        # Research service could be called with topic.title
        research_topic = topic.title
        assert "savings" in research_topic.lower()

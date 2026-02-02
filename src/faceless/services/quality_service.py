"""
Quality scoring service for the Faceless Content Pipeline.

This service evaluates script quality, focusing on hooks, retention potential,
and engagement factors to ensure only high-quality content proceeds to
expensive generation stages.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from faceless.clients.azure_openai import AzureOpenAIClient
from faceless.config import get_settings
from faceless.core.enums import Niche
from faceless.core.models import Script
from faceless.utils.logging import LoggerMixin


class QualityGate(str, Enum):
    """Quality gates that scripts must pass."""

    HOOK_QUALITY = "hook_quality"
    NARRATIVE_FLOW = "narrative_flow"
    INFORMATION_DENSITY = "information_density"
    ENGAGEMENT_POTENTIAL = "engagement_potential"
    FACTUAL_FOUNDATION = "factual_foundation"


@dataclass
class HookAnalysis:
    """Analysis of a script's opening hook."""

    score: float  # 0-10
    hook_type: str  # question, statistic, story, shocking, mystery
    attention_grab: float  # 0-1, how well it grabs attention
    curiosity_gap: float  # 0-1, how much it creates curiosity
    improvement_suggestions: list[str] = field(default_factory=list)
    alternative_hooks: list[str] = field(default_factory=list)


@dataclass
class RetentionAnalysis:
    """Analysis of content retention potential."""

    predicted_retention_30s: float  # % retained at 30 seconds
    predicted_retention_50pct: float  # % retained at midpoint
    predicted_completion_rate: float  # % who watch to end
    drop_off_risks: list[str] = field(default_factory=list)
    mid_video_hooks_present: bool = False
    loop_potential: float = 0.0  # 0-1, potential for rewatches


@dataclass
class EngagementAnalysis:
    """Analysis of engagement potential."""

    comment_trigger_score: float  # 0-10
    share_potential: float  # 0-10
    save_potential: float  # 0-10
    debate_potential: float  # 0-10
    comment_triggers: list[str] = field(default_factory=list)


@dataclass
class QualityScore:
    """Complete quality assessment for a script."""

    script_title: str
    niche: Niche
    evaluated_at: datetime = field(default_factory=datetime.now)

    # Core scores (0-10 scale)
    overall_score: float = 0.0
    hook_score: float = 0.0
    narrative_score: float = 0.0
    engagement_score: float = 0.0
    information_score: float = 0.0

    # Detailed analysis
    hook_analysis: HookAnalysis | None = None
    retention_analysis: RetentionAnalysis | None = None
    engagement_analysis: EngagementAnalysis | None = None

    # Gate results
    gates_passed: list[QualityGate] = field(default_factory=list)
    gates_failed: list[QualityGate] = field(default_factory=list)

    # Recommendations
    critical_issues: list[str] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)

    # Verdict
    approved_for_production: bool = False
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "script_title": self.script_title,
            "niche": self.niche.value,
            "evaluated_at": self.evaluated_at.isoformat(),
            "scores": {
                "overall": self.overall_score,
                "hook": self.hook_score,
                "narrative": self.narrative_score,
                "engagement": self.engagement_score,
                "information": self.information_score,
            },
            "hook_analysis": (
                {
                    "score": self.hook_analysis.score,
                    "type": self.hook_analysis.hook_type,
                    "attention_grab": self.hook_analysis.attention_grab,
                    "curiosity_gap": self.hook_analysis.curiosity_gap,
                    "improvements": self.hook_analysis.improvement_suggestions,
                    "alternatives": self.hook_analysis.alternative_hooks,
                }
                if self.hook_analysis
                else None
            ),
            "retention_analysis": (
                {
                    "retention_30s": self.retention_analysis.predicted_retention_30s,
                    "retention_50pct": self.retention_analysis.predicted_retention_50pct,
                    "completion_rate": self.retention_analysis.predicted_completion_rate,
                    "drop_off_risks": self.retention_analysis.drop_off_risks,
                    "mid_hooks_present": self.retention_analysis.mid_video_hooks_present,
                    "loop_potential": self.retention_analysis.loop_potential,
                }
                if self.retention_analysis
                else None
            ),
            "engagement_analysis": (
                {
                    "comment_score": self.engagement_analysis.comment_trigger_score,
                    "share_potential": self.engagement_analysis.share_potential,
                    "save_potential": self.engagement_analysis.save_potential,
                    "debate_potential": self.engagement_analysis.debate_potential,
                    "comment_triggers": self.engagement_analysis.comment_triggers,
                }
                if self.engagement_analysis
                else None
            ),
            "gates": {
                "passed": [g.value for g in self.gates_passed],
                "failed": [g.value for g in self.gates_failed],
            },
            "critical_issues": self.critical_issues,
            "improvements": self.improvements,
            "approved": self.approved_for_production,
            "confidence": self.confidence,
        }


# Quality thresholds
DEFAULT_THRESHOLDS = {
    "min_hook_score": 7.0,
    "min_overall_score": 6.5,
    "min_retention_30s": 0.70,
    "min_engagement_score": 5.0,
    "max_critical_issues": 0,
}


QUALITY_SYSTEM_PROMPT = """You are an expert content quality analyst specializing in short-form video content.
You evaluate scripts for YouTube and TikTok faceless channels.

Your role is to:
1. Analyze hook quality and attention-grabbing potential
2. Predict retention curves and identify drop-off risks
3. Evaluate engagement triggers (comments, shares, saves)
4. Assess narrative flow and pacing
5. Identify areas for improvement

Be critical but constructive. High-quality content is essential for success."""


class QualityService(LoggerMixin):
    """
    Service for evaluating script quality.

    Analyzes scripts for hook strength, retention potential,
    engagement factors, and overall quality to ensure only
    high-quality content proceeds to production.

    Features:
    - Hook quality scoring (0-10)
    - Retention curve prediction
    - Engagement potential analysis
    - Quality gate enforcement
    - Improvement recommendations

    Example:
        >>> service = QualityService()
        >>> score = service.evaluate_script(script)
        >>> if score.approved_for_production:
        ...     proceed_to_generation(script)
    """

    def __init__(
        self,
        client: AzureOpenAIClient | None = None,
        thresholds: dict[str, float] | None = None,
    ) -> None:
        """
        Initialize quality service.

        Args:
            client: Optional Azure OpenAI client
            thresholds: Custom quality thresholds (uses defaults if not provided)
        """
        self._client = client or AzureOpenAIClient()
        self._settings = get_settings()
        self._thresholds = thresholds or DEFAULT_THRESHOLDS

    def evaluate_script(
        self,
        script: Script,
        strict_mode: bool = False,
    ) -> QualityScore:
        """
        Evaluate a script's quality.

        Args:
            script: Script to evaluate
            strict_mode: If True, requires all gates to pass

        Returns:
            QualityScore with detailed analysis
        """
        self.logger.info(
            "Evaluating script quality",
            title=script.title,
            scenes=len(script.scenes),
        )

        # Prepare script content for analysis
        script_content = self._prepare_script_content(script)

        # Get comprehensive quality analysis
        analysis = self._analyze_quality(script_content, script.niche)

        # Build quality score from analysis
        quality_score = self._build_quality_score(analysis, script)

        # Apply quality gates
        self._apply_quality_gates(quality_score, strict_mode)

        self.logger.info(
            "Quality evaluation complete",
            title=script.title,
            overall_score=quality_score.overall_score,
            hook_score=quality_score.hook_score,
            approved=quality_score.approved_for_production,
        )

        return quality_score

    def evaluate_hook_only(
        self,
        hook_text: str,
        niche: Niche,
    ) -> HookAnalysis:
        """
        Quickly evaluate just a hook's quality.

        Args:
            hook_text: The opening hook text
            niche: Content niche

        Returns:
            HookAnalysis with score and suggestions
        """
        prompt = f"""Evaluate this {niche.display_name} video hook:

"{hook_text}"

Return JSON with:
{{
    "score": 8.5,
    "hook_type": "question|statistic|story|shocking|mystery",
    "attention_grab": 0.85,
    "curiosity_gap": 0.80,
    "strengths": ["strength 1", "strength 2"],
    "weaknesses": ["weakness 1"],
    "improvement_suggestions": ["suggestion 1", "suggestion 2"],
    "alternative_hooks": ["better hook 1", "better hook 2", "better hook 3"]
}}"""

        try:
            result = self._client.chat_json(
                system_prompt=QUALITY_SYSTEM_PROMPT,
                user_prompt=prompt,
                temperature=0.5,
            )

            return HookAnalysis(
                score=float(result.get("score", 5.0)),
                hook_type=result.get("hook_type", "unknown"),
                attention_grab=float(result.get("attention_grab", 0.5)),
                curiosity_gap=float(result.get("curiosity_gap", 0.5)),
                improvement_suggestions=result.get("improvement_suggestions", []),
                alternative_hooks=result.get("alternative_hooks", []),
            )

        except Exception as e:
            self.logger.warning("Hook evaluation failed", error=str(e))
            return HookAnalysis(
                score=5.0,
                hook_type="unknown",
                attention_grab=0.5,
                curiosity_gap=0.5,
            )

    def generate_better_hooks(
        self,
        script: Script,
        count: int = 5,
    ) -> list[str]:
        """
        Generate improved hook alternatives for a script.

        Args:
            script: Script to improve hooks for
            count: Number of alternatives to generate

        Returns:
            List of improved hook options
        """
        current_hook = script.scenes[0].narration[:200] if script.scenes else ""

        prompt = f"""Generate {count} powerful hook alternatives for this {script.niche.display_name} video.

Title: {script.title}
Current opening: "{current_hook}"

Requirements:
- Must grab attention in first 0.5 seconds
- Create a strong curiosity gap
- Match the {script.niche.display_name} niche tone
- Be varied in style (question, statistic, story, shocking, mystery)

Return JSON array of {count} hook strings."""

        try:
            result = self._client.chat_json(
                system_prompt=QUALITY_SYSTEM_PROMPT,
                user_prompt=prompt,
                temperature=0.9,  # Higher creativity
            )

            if isinstance(result, list):
                return list(result[:count])
            if "hooks" in result:
                return list(result["hooks"][:count])
            return []

        except Exception as e:
            self.logger.warning("Hook generation failed", error=str(e))
            return []

    def check_mid_video_retention(
        self,
        script: Script,
    ) -> dict[str, Any]:
        """
        Check for mid-video retention hooks.

        Args:
            script: Script to analyze

        Returns:
            Analysis of mid-video retention elements
        """
        if len(script.scenes) < 3:
            return {
                "has_mid_hooks": False,
                "suggestion": "Script too short for mid-video hooks",
            }

        # Get middle section of script
        mid_start = len(script.scenes) // 3
        mid_end = (len(script.scenes) * 2) // 3
        mid_content = " ".join(s.narration for s in script.scenes[mid_start:mid_end])

        prompt = f"""Analyze the middle section of this {script.niche.display_name} script for retention hooks.

Middle content:
"{mid_content[:1000]}"

Check for:
- "But here's where it gets worse..." type hooks
- Pattern interrupts
- Promise of upcoming reveal
- Building tension
- Questions to the viewer

Return JSON with:
{{
    "has_mid_hooks": true/false,
    "hooks_found": ["description of hook 1"],
    "retention_score": 7.5,
    "suggestions": ["add hook suggestion 1"]
}}"""

        try:
            return self._client.chat_json(
                system_prompt=QUALITY_SYSTEM_PROMPT,
                user_prompt=prompt,
                temperature=0.5,
            )

        except Exception as e:
            self.logger.warning("Mid-video analysis failed", error=str(e))
            return {"has_mid_hooks": False, "error": str(e)}

    def _prepare_script_content(self, script: Script) -> str:
        """Prepare script content for analysis."""
        scenes_text = []
        for scene in script.scenes:
            scenes_text.append(f"Scene {scene.scene_number}: {scene.narration}")

        return f"""Title: {script.title}
Niche: {script.niche.display_name}
Total Scenes: {len(script.scenes)}

FULL SCRIPT:
{chr(10).join(scenes_text)}"""

    def _analyze_quality(
        self,
        script_content: str,
        niche: Niche,
    ) -> dict[str, Any]:
        """Get comprehensive quality analysis from AI."""
        prompt = f"""{script_content}

Analyze this {niche.display_name} script comprehensively.

Return JSON with:
{{
    "hook_analysis": {{
        "score": 8.0,
        "hook_type": "question|statistic|story|shocking|mystery",
        "attention_grab": 0.85,
        "curiosity_gap": 0.75,
        "improvement_suggestions": ["suggestion 1"],
        "alternative_hooks": ["alt 1", "alt 2"]
    }},
    "retention_analysis": {{
        "predicted_retention_30s": 0.75,
        "predicted_retention_50pct": 0.55,
        "predicted_completion_rate": 0.40,
        "drop_off_risks": ["risk 1", "risk 2"],
        "mid_video_hooks_present": true,
        "loop_potential": 0.3
    }},
    "engagement_analysis": {{
        "comment_trigger_score": 7.5,
        "share_potential": 6.0,
        "save_potential": 7.0,
        "debate_potential": 5.5,
        "comment_triggers": ["trigger 1", "trigger 2"]
    }},
    "narrative_score": 7.5,
    "information_score": 8.0,
    "critical_issues": ["issue 1"],
    "improvements": ["improvement 1", "improvement 2"],
    "overall_score": 7.5,
    "confidence": 0.85
}}"""

        try:
            return self._client.chat_json(
                system_prompt=QUALITY_SYSTEM_PROMPT,
                user_prompt=prompt,
                temperature=0.5,
                max_tokens=2000,
            )

        except Exception as e:
            self.logger.error("Quality analysis failed", error=str(e))
            return {}

    def _build_quality_score(
        self,
        analysis: dict[str, Any],
        script: Script,
    ) -> QualityScore:
        """Build QualityScore from analysis results."""
        score = QualityScore(
            script_title=script.title,
            niche=script.niche,
        )

        # Parse hook analysis
        if "hook_analysis" in analysis:
            ha = analysis["hook_analysis"]
            score.hook_analysis = HookAnalysis(
                score=float(ha.get("score", 5.0)),
                hook_type=ha.get("hook_type", "unknown"),
                attention_grab=float(ha.get("attention_grab", 0.5)),
                curiosity_gap=float(ha.get("curiosity_gap", 0.5)),
                improvement_suggestions=ha.get("improvement_suggestions", []),
                alternative_hooks=ha.get("alternative_hooks", []),
            )
            score.hook_score = score.hook_analysis.score

        # Parse retention analysis
        if "retention_analysis" in analysis:
            ra = analysis["retention_analysis"]
            score.retention_analysis = RetentionAnalysis(
                predicted_retention_30s=float(ra.get("predicted_retention_30s", 0.5)),
                predicted_retention_50pct=float(
                    ra.get("predicted_retention_50pct", 0.4)
                ),
                predicted_completion_rate=float(
                    ra.get("predicted_completion_rate", 0.3)
                ),
                drop_off_risks=ra.get("drop_off_risks", []),
                mid_video_hooks_present=ra.get("mid_video_hooks_present", False),
                loop_potential=float(ra.get("loop_potential", 0.0)),
            )

        # Parse engagement analysis
        if "engagement_analysis" in analysis:
            ea = analysis["engagement_analysis"]
            score.engagement_analysis = EngagementAnalysis(
                comment_trigger_score=float(ea.get("comment_trigger_score", 5.0)),
                share_potential=float(ea.get("share_potential", 5.0)),
                save_potential=float(ea.get("save_potential", 5.0)),
                debate_potential=float(ea.get("debate_potential", 5.0)),
                comment_triggers=ea.get("comment_triggers", []),
            )
            score.engagement_score = score.engagement_analysis.comment_trigger_score

        # Parse other scores
        score.narrative_score = float(analysis.get("narrative_score", 5.0))
        score.information_score = float(analysis.get("information_score", 5.0))
        score.overall_score = float(analysis.get("overall_score", 5.0))
        score.confidence = float(analysis.get("confidence", 0.7))

        # Parse issues and improvements
        score.critical_issues = analysis.get("critical_issues", [])
        score.improvements = analysis.get("improvements", [])

        return score

    def _apply_quality_gates(
        self,
        score: QualityScore,
        strict_mode: bool,
    ) -> None:
        """Apply quality gates and determine approval."""
        # Check hook quality gate
        if score.hook_score >= self._thresholds["min_hook_score"]:
            score.gates_passed.append(QualityGate.HOOK_QUALITY)
        else:
            score.gates_failed.append(QualityGate.HOOK_QUALITY)

        # Check narrative flow gate
        if score.narrative_score >= 6.0:
            score.gates_passed.append(QualityGate.NARRATIVE_FLOW)
        else:
            score.gates_failed.append(QualityGate.NARRATIVE_FLOW)

        # Check information density gate
        if score.information_score >= 5.0:
            score.gates_passed.append(QualityGate.INFORMATION_DENSITY)
        else:
            score.gates_failed.append(QualityGate.INFORMATION_DENSITY)

        # Check engagement potential gate
        if score.engagement_score >= self._thresholds["min_engagement_score"]:
            score.gates_passed.append(QualityGate.ENGAGEMENT_POTENTIAL)
        else:
            score.gates_failed.append(QualityGate.ENGAGEMENT_POTENTIAL)

        # Check factual foundation (based on information score)
        if score.information_score >= 6.0:
            score.gates_passed.append(QualityGate.FACTUAL_FOUNDATION)
        else:
            score.gates_failed.append(QualityGate.FACTUAL_FOUNDATION)

        # Determine approval
        critical_issue_count = len(score.critical_issues)
        has_critical_issues = (
            critical_issue_count > self._thresholds["max_critical_issues"]
        )

        if strict_mode:
            # All gates must pass
            score.approved_for_production = (
                len(score.gates_failed) == 0
                and not has_critical_issues
                and score.overall_score >= self._thresholds["min_overall_score"]
            )
        else:
            # Hook must pass, overall score must meet threshold
            hook_passed = QualityGate.HOOK_QUALITY in score.gates_passed
            score.approved_for_production = (
                hook_passed
                and not has_critical_issues
                and score.overall_score >= self._thresholds["min_overall_score"]
            )

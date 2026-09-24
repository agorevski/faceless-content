"""Tests that production quality gates fail closed on invalid AI assessments."""

from unittest.mock import MagicMock

import pytest

from faceless.core.enums import Niche
from faceless.core.exceptions import AzureOpenAIError, PipelineError
from faceless.core.models import Scene, Script
from faceless.services.quality_service import QualityService


@pytest.fixture
def script() -> Script:
    return Script(
        title="A true story",
        niche=Niche.SCARY_STORIES,
        scenes=[Scene(scene_number=1, narration="A door opened.", image_prompt="Door")],
    )


@pytest.fixture
def analysis() -> dict[str, object]:
    return {
        "hook_analysis": {"score": 8.0},
        "engagement_analysis": {"comment_trigger_score": 7.0},
        "narrative_score": 7.0,
        "information_score": 7.0,
        "overall_score": 8.0,
        "critical_issues": [],
    }


def test_valid_quality_analysis_is_approved(
    script: Script, analysis: dict[str, object]
) -> None:
    client = MagicMock()
    client.chat_json.return_value = analysis

    score = QualityService(client=client).evaluate_script(script)

    assert score.approved_for_production
    assert score.hook_score == 8.0


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("hook_analysis", None),
        ("hook_analysis", {"score": 11}),
        ("hook_analysis", {"score": True}),
        ("overall_score", float("nan")),
        ("overall_score", -1),
        ("critical_issues", None),
        ("critical_issues", [1]),
        ("engagement_analysis", {}),
    ],
)
def test_incomplete_or_invalid_analysis_rejected(
    script: Script,
    analysis: dict[str, object],
    key: str,
    value: object,
) -> None:
    analysis[key] = value
    client = MagicMock()
    client.chat_json.return_value = analysis

    with pytest.raises(PipelineError, match="Quality analysis"):
        QualityService(client=client).evaluate_script(script)


def test_api_error_does_not_turn_into_a_default_score(script: Script) -> None:
    client = MagicMock()
    client.chat_json.side_effect = AzureOpenAIError("Service unavailable")

    with pytest.raises(PipelineError, match="cannot proceed"):
        QualityService(client=client).evaluate_script(script)

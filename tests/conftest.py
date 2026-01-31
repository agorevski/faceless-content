"""
Pytest configuration and fixtures for the Faceless Content Pipeline.

This module provides common fixtures used across all tests.
"""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from faceless.core.enums import Niche, Platform
from faceless.core.models import Scene, Script, VisualStyle

# =============================================================================
# Path Fixtures
# =============================================================================


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


@pytest.fixture
def temp_scripts_dir(temp_output_dir: Path) -> Path:
    """Create a temporary scripts directory."""
    scripts_dir = temp_output_dir / "scary-stories" / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    return scripts_dir


# =============================================================================
# Model Fixtures
# =============================================================================


@pytest.fixture
def sample_scene() -> Scene:
    """Create a sample scene for testing."""
    return Scene(
        scene_number=1,
        narration="The old house stood silent at the end of the street.",
        image_prompt="A dark Victorian house at night with fog",
        duration_estimate=15.0,
    )


@pytest.fixture
def sample_scenes() -> list[Scene]:
    """Create multiple sample scenes for testing."""
    return [
        Scene(
            scene_number=1,
            narration="The old house stood silent at the end of the street.",
            image_prompt="A dark Victorian house at night with fog",
            duration_estimate=15.0,
        ),
        Scene(
            scene_number=2,
            narration="I approached the door, my heart pounding.",
            image_prompt="A close-up of a weathered wooden door with brass handle",
            duration_estimate=12.0,
        ),
        Scene(
            scene_number=3,
            narration="The door creaked open, revealing only darkness.",
            image_prompt="An open doorway leading into complete darkness",
            duration_estimate=10.0,
        ),
    ]


@pytest.fixture
def sample_visual_style() -> VisualStyle:
    """Create a sample visual style for testing."""
    return VisualStyle(
        environment="Dark foggy suburban neighborhood at twilight",
        color_mood="Deep blues, grays, with occasional amber highlights",
        texture="Weathered wood, wet asphalt, overgrown vegetation",
        recurring_elements={
            "the_house": "A Victorian mansion with dark windows",
            "fog": "Thick ground-level fog",
        },
    )


@pytest.fixture
def sample_script(
    sample_scenes: list[Scene], sample_visual_style: VisualStyle
) -> Script:
    """Create a sample script for testing."""
    return Script(
        title="The House at the End of the Street",
        niche=Niche.SCARY_STORIES,
        scenes=sample_scenes,
        source="r/nosleep",
        author="test_author",
        visual_style=sample_visual_style,
    )


@pytest.fixture
def sample_script_json(sample_script: Script, temp_scripts_dir: Path) -> Path:
    """Save sample script to JSON and return path."""
    script_path = temp_scripts_dir / "test-script_script.json"
    sample_script.to_json_file(script_path)
    return script_path


# =============================================================================
# Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_settings() -> Generator[MagicMock, None, None]:
    """Mock the settings singleton."""
    with patch("faceless.config.get_settings") as mock:
        settings = MagicMock()
        settings.azure_openai.is_configured = True
        settings.azure_openai.endpoint = "https://test.openai.azure.com/"
        settings.azure_openai.api_key = "test-api-key"
        settings.azure_openai.image_deployment = "gpt-image-1"
        settings.azure_openai.chat_deployment = "gpt-4o"
        settings.azure_openai.tts_deployment = "gpt-4o-mini-tts"
        settings.output_base_dir = Path("output")
        settings.max_concurrent_requests = 5
        settings.request_timeout = 120
        settings.enable_retry = True
        settings.max_retries = 3
        mock.return_value = settings
        yield settings


@pytest.fixture
def mock_httpx_client() -> Generator[MagicMock, None, None]:
    """Mock httpx.Client for HTTP tests."""
    with patch("httpx.Client") as mock:
        yield mock


# =============================================================================
# Platform/Niche Fixtures
# =============================================================================


@pytest.fixture(params=list(Niche))
def all_niches(request: pytest.FixtureRequest) -> Niche:
    """Parametrized fixture for all niches."""
    return request.param


@pytest.fixture(params=list(Platform))
def all_platforms(request: pytest.FixtureRequest) -> Platform:
    """Parametrized fixture for all platforms."""
    return request.param


# =============================================================================
# Test Markers
# =============================================================================


def pytest_configure(config: pytest.Config) -> None:
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")

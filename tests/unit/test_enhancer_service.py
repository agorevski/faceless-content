"""
Unit tests for EnhancerService.

Tests cover:
- Script enhancement
- Visual style generation
- Enhancement prompt building
- Error handling
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from faceless.core.enums import Niche
from faceless.core.models import Scene, Script, VisualStyle


class TestEnhancerService:
    """Tests for EnhancerService."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings."""
        with patch("faceless.services.enhancer_service.get_settings") as mock:
            settings = MagicMock()
            mock.return_value = settings
            yield settings

    @pytest.fixture
    def mock_client(self):
        """Mock Azure OpenAI client."""
        client = MagicMock()
        return client

    @pytest.fixture
    def enhancer_service(self, mock_settings, mock_client):
        """Create enhancer service with mocked client."""
        with patch("faceless.services.enhancer_service.AzureOpenAIClient"):
            from faceless.services.enhancer_service import EnhancerService

            service = EnhancerService(client=mock_client)
            return service

    @pytest.fixture
    def sample_script(self) -> Script:
        """Create sample script for testing."""
        scenes = [
            Scene(
                scene_number=1,
                narration="The door opened slowly.",
                image_prompt="An old wooden door opening",
                duration_estimate=10.0,
            ),
            Scene(
                scene_number=2,
                narration="Inside was darkness.",
                image_prompt="Complete darkness with shadows",
                duration_estimate=8.0,
            ),
        ]
        return Script(
            title="The Dark Room",
            niche=Niche.SCARY_STORIES,
            scenes=scenes,
            source="test",
            author="test_author",
        )

    def test_init_with_client(self, mock_settings, mock_client) -> None:
        """Test service initialization with provided client."""
        from faceless.services.enhancer_service import EnhancerService

        service = EnhancerService(client=mock_client)
        assert service._client == mock_client

    def test_init_without_client(self, mock_settings) -> None:
        """Test service initialization creates client."""
        with patch(
            "faceless.services.enhancer_service.AzureOpenAIClient"
        ) as mock_client_class:
            from faceless.services.enhancer_service import EnhancerService

            EnhancerService()
            mock_client_class.assert_called_once()

    def test_enhance_script_success(
        self, enhancer_service, mock_client, sample_script
    ) -> None:
        """Test successful script enhancement."""
        mock_client.chat_json.return_value = {
            "title": "The Dark Room - Enhanced",
            "visual_style": {
                "environment": "Dark Victorian mansion",
                "color_mood": "Deep blues and grays",
                "texture": "Weathered wood and dust",
                "recurring_elements": {"door": "Ornate wooden door"},
            },
            "scenes": [
                {
                    "scene_number": 1,
                    "narration": "The ancient door creaked open slowly.",
                    "image_prompt": "An ornate Victorian door opening with dust particles",
                },
                {
                    "scene_number": 2,
                    "narration": "Inside lay only darkness and silence.",
                    "image_prompt": "Impenetrable darkness with subtle shadows",
                },
            ],
        }

        result = enhancer_service.enhance_script(sample_script)

        assert result.title == "The Dark Room - Enhanced"
        assert result.scenes[0].narration == "The ancient door creaked open slowly."
        assert result.visual_style is not None
        assert result.visual_style.environment == "Dark Victorian mansion"

    def test_enhance_script_preserves_original_on_error(
        self, enhancer_service, mock_client, sample_script
    ) -> None:
        """Test that original script is returned on error."""
        mock_client.chat_json.side_effect = Exception("API Error")

        result = enhancer_service.enhance_script(sample_script)

        # Should return original script
        assert result.title == sample_script.title
        assert result.scenes[0].narration == sample_script.scenes[0].narration

    def test_enhance_script_partial_enhancement(
        self, enhancer_service, mock_client, sample_script
    ) -> None:
        """Test enhancement with partial response."""
        mock_client.chat_json.return_value = {
            "title": "Enhanced Title",
            "scenes": [
                {
                    "scene_number": 1,
                    "narration": "Enhanced narration",
                    "image_prompt": "Enhanced prompt",
                },
                # Scene 2 missing - should use original
            ],
        }

        result = enhancer_service.enhance_script(sample_script)

        assert result.title == "Enhanced Title"
        assert result.scenes[0].narration == "Enhanced narration"
        # Scene 2 should use original values
        assert result.scenes[1].narration == sample_script.scenes[1].narration

    def test_enhance_script_with_options(
        self, enhancer_service, mock_client, sample_script
    ) -> None:
        """Test enhancement with specific options."""
        mock_client.chat_json.return_value = {
            "title": sample_script.title,
            "scenes": [
                {
                    "scene_number": i + 1,
                    "narration": s.narration,
                    "image_prompt": s.image_prompt,
                }
                for i, s in enumerate(sample_script.scenes)
            ],
        }

        result = enhancer_service.enhance_script(
            sample_script,
            enhance_narration=False,
            enhance_prompts=True,
            add_visual_style=False,
        )

        assert result is not None
        mock_client.chat_json.assert_called_once()

    def test_enhance_script_sets_enhanced_at(
        self, enhancer_service, mock_client, sample_script
    ) -> None:
        """Test that enhanced_at is set."""
        mock_client.chat_json.return_value = {
            "title": sample_script.title,
            "scenes": [],
        }

        result = enhancer_service.enhance_script(sample_script)

        assert result.enhanced_at is not None
        assert isinstance(result.enhanced_at, datetime)

    def test_build_enhancement_prompt(self, enhancer_service, sample_script) -> None:
        """Test enhancement prompt building."""
        prompt = enhancer_service._build_enhancement_prompt(
            script=sample_script,
            enhance_narration=True,
            enhance_prompts=True,
            add_visual_style=True,
        )

        assert "scary-stories" in prompt.lower()
        assert sample_script.title in prompt
        assert "narration" in prompt.lower()
        assert "visual_style" in prompt.lower()

    def test_build_enhancement_prompt_selective(
        self, enhancer_service, sample_script
    ) -> None:
        """Test enhancement prompt with selective options."""
        prompt = enhancer_service._build_enhancement_prompt(
            script=sample_script,
            enhance_narration=True,
            enhance_prompts=False,
            add_visual_style=False,
        )

        assert "narration" in prompt.lower()

    def test_apply_enhancements(self, enhancer_service, sample_script) -> None:
        """Test applying enhancements to script."""
        enhancements = {
            "title": "New Title",
            "visual_style": {
                "environment": "Foggy forest",
                "color_mood": "Dark greens",
                "texture": "Moss and bark",
                "recurring_elements": {"tree": "Ancient oak"},
            },
            "scenes": [
                {
                    "scene_number": 1,
                    "narration": "New narration 1",
                    "image_prompt": "New prompt 1",
                },
            ],
        }

        result = enhancer_service._apply_enhancements(sample_script, enhancements)

        assert result.title == "New Title"
        assert result.scenes[0].narration == "New narration 1"
        assert result.visual_style.environment == "Foggy forest"
        # Scene 2 should keep original
        assert result.scenes[1].narration == sample_script.scenes[1].narration

    def test_apply_enhancements_preserves_metadata(
        self, enhancer_service, sample_script
    ) -> None:
        """Test that apply_enhancements preserves original metadata."""
        enhancements = {"title": "New Title", "scenes": []}

        result = enhancer_service._apply_enhancements(sample_script, enhancements)

        assert result.niche == sample_script.niche
        assert result.source == sample_script.source
        assert result.author == sample_script.author
        assert result.created_at == sample_script.created_at

    def test_generate_visual_style_success(
        self, enhancer_service, mock_client, sample_script
    ) -> None:
        """Test successful visual style generation."""
        mock_client.chat_json.return_value = {
            "environment": "Haunted Victorian mansion",
            "color_mood": "Deep purples and blacks",
            "texture": "Cracked paint and cobwebs",
            "recurring_elements": {"ghost": "Translucent figure"},
        }

        result = enhancer_service.generate_visual_style(sample_script)

        assert isinstance(result, VisualStyle)
        assert result.environment == "Haunted Victorian mansion"
        assert result.color_mood == "Deep purples and blacks"
        assert "ghost" in result.recurring_elements

    def test_generate_visual_style_error_returns_empty(
        self, enhancer_service, mock_client, sample_script
    ) -> None:
        """Test visual style generation returns empty on error."""
        mock_client.chat_json.side_effect = Exception("API Error")

        result = enhancer_service.generate_visual_style(sample_script)

        assert isinstance(result, VisualStyle)
        assert result.environment == ""
        assert result.color_mood == ""

    def test_generate_visual_style_partial_response(
        self, enhancer_service, mock_client, sample_script
    ) -> None:
        """Test visual style with partial response."""
        mock_client.chat_json.return_value = {
            "environment": "Dark forest",
            # Missing other fields
        }

        result = enhancer_service.generate_visual_style(sample_script)

        assert result.environment == "Dark forest"
        assert result.color_mood == ""
        assert result.texture == ""

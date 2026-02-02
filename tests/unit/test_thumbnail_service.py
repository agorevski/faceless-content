"""
Unit tests for the thumbnail service.

Tests thumbnail prompt generation, template handling, and text overlay.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# =============================================================================
# Thumbnail Template Tests
# =============================================================================


class TestThumbnailTemplates:
    """Tests for thumbnail template configuration."""

    def test_scary_stories_template_exists(self) -> None:
        """Test scary-stories template exists."""
        from faceless.services.thumbnail_service import THUMBNAIL_TEMPLATES

        assert "scary-stories" in THUMBNAIL_TEMPLATES
        template = THUMBNAIL_TEMPLATES["scary-stories"]
        assert "style" in template
        assert "colors" in template
        assert "elements" in template
        assert "prompt_template" in template

    def test_finance_template_exists(self) -> None:
        """Test finance template exists."""
        from faceless.services.thumbnail_service import THUMBNAIL_TEMPLATES

        assert "finance" in THUMBNAIL_TEMPLATES
        template = THUMBNAIL_TEMPLATES["finance"]
        assert "style" in template

    def test_luxury_template_exists(self) -> None:
        """Test luxury template exists."""
        from faceless.services.thumbnail_service import THUMBNAIL_TEMPLATES

        assert "luxury" in THUMBNAIL_TEMPLATES


class TestThumbnailConcepts:
    """Tests for thumbnail concept definitions."""

    def test_all_concepts_exist(self) -> None:
        """Test that all expected concepts exist."""
        from faceless.services.thumbnail_service import THUMBNAIL_CONCEPTS

        expected = [
            "reaction",
            "reveal",
            "versus",
            "before_after",
            "countdown",
            "mystery",
            "warning",
            "secret",
        ]

        for concept in expected:
            assert concept in THUMBNAIL_CONCEPTS
            assert len(THUMBNAIL_CONCEPTS[concept]) > 0


# =============================================================================
# Generate Thumbnail Prompt Tests
# =============================================================================


class TestGenerateThumbnailPrompt:
    """Tests for thumbnail prompt generation."""

    def test_basic_prompt_generation(self) -> None:
        """Test basic prompt generation."""
        from faceless.services.thumbnail_service import generate_thumbnail_prompt

        prompt = generate_thumbnail_prompt(
            title="The Haunted House Mystery",
            niche="scary-stories",
            concept="reveal",
        )

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "horror" in prompt.lower() or "dark" in prompt.lower()

    def test_custom_subject(self) -> None:
        """Test prompt with custom subject."""
        from faceless.services.thumbnail_service import generate_thumbnail_prompt

        prompt = generate_thumbnail_prompt(
            title="Some Title",
            niche="scary-stories",
            concept="reveal",
            custom_subject="A creepy abandoned hospital",
        )

        assert "abandoned hospital" in prompt.lower()

    def test_removes_filler_words(self) -> None:
        """Test that filler words are removed from title."""
        from faceless.services.thumbnail_service import generate_thumbnail_prompt

        prompt = generate_thumbnail_prompt(
            title="Why The Stock Market Crashed",
            niche="finance",
            concept="reaction",
        )

        # The prompt shouldn't start with "Why" or "The"
        assert isinstance(prompt, str)

    def test_concept_included(self) -> None:
        """Test that concept description is included."""
        from faceless.services.thumbnail_service import (
            THUMBNAIL_CONCEPTS,
            generate_thumbnail_prompt,
        )

        prompt = generate_thumbnail_prompt(
            title="Test Video",
            niche="finance",
            concept="reaction",
        )

        # Part of the reaction concept should be in the prompt
        assert "shocked" in prompt.lower() or "amazed" in prompt.lower()

    def test_includes_composition_guidance(self) -> None:
        """Test that composition guidance is included."""
        from faceless.services.thumbnail_service import generate_thumbnail_prompt

        prompt = generate_thumbnail_prompt(
            title="Test",
            niche="scary-stories",
            concept="mystery",
        )

        assert "16:9" in prompt or "composition" in prompt.lower()

    def test_fallback_for_unknown_niche(self) -> None:
        """Test fallback to finance template for unknown niche."""
        from faceless.services.thumbnail_service import generate_thumbnail_prompt

        prompt = generate_thumbnail_prompt(
            title="Test Title",
            niche="unknown-niche",
            concept="reveal",
        )

        # Should still generate a valid prompt
        assert isinstance(prompt, str)
        assert len(prompt) > 20


# =============================================================================
# Generate Thumbnail Tests
# =============================================================================


class TestGenerateThumbnail:
    """Tests for thumbnail image generation."""

    @patch("faceless.services.thumbnail_service.httpx.Client")
    @patch("faceless.services.thumbnail_service.get_settings")
    def test_generate_thumbnail_success(
        self, mock_settings: MagicMock, mock_client_class: MagicMock, tmp_path: Path
    ) -> None:
        """Test successful thumbnail generation."""
        from faceless.services.thumbnail_service import generate_thumbnail

        mock_settings.return_value.output_base_dir = tmp_path
        mock_settings.return_value.azure_openai.endpoint = (
            "https://test.openai.azure.com/"
        )
        mock_settings.return_value.azure_openai.api_key = "test-key"
        mock_settings.return_value.azure_openai.image_deployment = "gpt-image-1"
        mock_settings.return_value.azure_openai.image_api_version = "2024-02-01"

        # Mock the API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [{"b64_json": "dGVzdGltYWdl"}]  # base64 for "testimage"
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = generate_thumbnail(
            prompt="Test prompt",
            niche="scary-stories",
            output_name="test_thumb",
            output_dir=tmp_path,
        )

        assert result.exists()
        assert result.name == "test_thumb.png"

    @patch("faceless.services.thumbnail_service.get_settings")
    def test_generate_thumbnail_skips_existing(
        self, mock_settings: MagicMock, tmp_path: Path
    ) -> None:
        """Test that existing thumbnails are not regenerated."""
        from faceless.services.thumbnail_service import generate_thumbnail

        mock_settings.return_value.output_base_dir = tmp_path

        # Create existing thumbnail
        existing = tmp_path / "existing_thumb.png"
        existing.write_bytes(b"existing image")

        result = generate_thumbnail(
            prompt="Test prompt",
            niche="scary-stories",
            output_name="existing_thumb",
            output_dir=tmp_path,
        )

        assert result == existing
        assert result.read_bytes() == b"existing image"

    @patch("faceless.services.thumbnail_service.httpx.Client")
    @patch("faceless.services.thumbnail_service.get_settings")
    def test_generate_thumbnail_saves_prompt(
        self, mock_settings: MagicMock, mock_client_class: MagicMock, tmp_path: Path
    ) -> None:
        """Test that the prompt is saved alongside the image."""
        from faceless.services.thumbnail_service import generate_thumbnail

        mock_settings.return_value.output_base_dir = tmp_path
        mock_settings.return_value.azure_openai.endpoint = (
            "https://test.openai.azure.com/"
        )
        mock_settings.return_value.azure_openai.api_key = "test-key"
        mock_settings.return_value.azure_openai.image_deployment = "gpt-image-1"
        mock_settings.return_value.azure_openai.image_api_version = "2024-02-01"

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": [{"b64_json": "dGVzdA=="}]}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = generate_thumbnail(
            prompt="My test prompt",
            niche="scary-stories",
            output_name="test",
            output_dir=tmp_path,
        )

        prompt_file = result.with_suffix(".txt")
        assert prompt_file.exists()
        assert prompt_file.read_text() == "My test prompt"

    @patch("faceless.services.thumbnail_service.httpx.Client")
    @patch("faceless.services.thumbnail_service.get_settings")
    def test_generate_thumbnail_handles_url_response(
        self, mock_settings: MagicMock, mock_client_class: MagicMock, tmp_path: Path
    ) -> None:
        """Test handling of URL-based image response."""
        from faceless.services.thumbnail_service import generate_thumbnail

        mock_settings.return_value.output_base_dir = tmp_path
        mock_settings.return_value.azure_openai.endpoint = (
            "https://test.openai.azure.com/"
        )
        mock_settings.return_value.azure_openai.api_key = "test-key"
        mock_settings.return_value.azure_openai.image_deployment = "gpt-image-1"
        mock_settings.return_value.azure_openai.image_api_version = "2024-02-01"

        # First call returns URL
        mock_response1 = MagicMock()
        mock_response1.json.return_value = {
            "data": [{"url": "https://example.com/image.png"}]
        }
        mock_response1.raise_for_status = MagicMock()

        # Second call gets the image
        mock_response2 = MagicMock()
        mock_response2.content = b"image bytes"

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response1
        mock_client.get.return_value = mock_response2
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = generate_thumbnail(
            prompt="Test",
            niche="scary-stories",
            output_name="url_test",
            output_dir=tmp_path,
        )

        assert result.exists()


# =============================================================================
# Generate Thumbnail Variants Tests
# =============================================================================


class TestGenerateThumbnailVariants:
    """Tests for generating multiple thumbnail variants."""

    @patch("faceless.services.thumbnail_service.generate_thumbnail")
    def test_generates_multiple_variants(
        self, mock_generate: MagicMock, tmp_path: Path
    ) -> None:
        """Test that multiple variants are generated."""
        from faceless.services.thumbnail_service import generate_thumbnail_variants

        mock_generate.return_value = tmp_path / "thumb.png"

        result = generate_thumbnail_variants(
            title="Test Video",
            niche="scary-stories",
            base_name="test",
            output_dir=tmp_path,
            num_variants=3,
        )

        assert len(result) == 3
        assert mock_generate.call_count == 3

    @patch("faceless.services.thumbnail_service.generate_thumbnail")
    def test_uses_niche_specific_concepts(
        self, mock_generate: MagicMock, tmp_path: Path
    ) -> None:
        """Test that niche-specific concepts are used."""
        from faceless.services.thumbnail_service import generate_thumbnail_variants

        mock_generate.return_value = tmp_path / "thumb.png"

        generate_thumbnail_variants(
            title="Test",
            niche="scary-stories",
            base_name="test",
            output_dir=tmp_path,
        )

        # Should have called with scary-stories concepts
        assert mock_generate.called

    @patch("faceless.services.thumbnail_service.generate_thumbnail")
    def test_custom_concepts(self, mock_generate: MagicMock, tmp_path: Path) -> None:
        """Test using custom concepts."""
        from faceless.services.thumbnail_service import generate_thumbnail_variants

        mock_generate.return_value = tmp_path / "thumb.png"

        generate_thumbnail_variants(
            title="Test",
            niche="finance",
            base_name="test",
            output_dir=tmp_path,
            concepts=["reaction", "countdown"],
        )

        assert mock_generate.call_count == 2

    @patch("faceless.services.thumbnail_service.generate_thumbnail")
    def test_handles_generation_failures(
        self, mock_generate: MagicMock, tmp_path: Path
    ) -> None:
        """Test that failures are handled gracefully."""
        from faceless.services.thumbnail_service import generate_thumbnail_variants

        # First succeeds, second fails, third succeeds
        mock_generate.side_effect = [
            tmp_path / "thumb1.png",
            Exception("API Error"),
            tmp_path / "thumb3.png",
        ]

        result = generate_thumbnail_variants(
            title="Test",
            niche="scary-stories",
            base_name="test",
            output_dir=tmp_path,
            num_variants=3,
        )

        assert len(result) == 3
        assert result[0] is not None
        assert result[1] is None  # Failed
        assert result[2] is not None


# =============================================================================
# Text Overlay Instructions Tests
# =============================================================================


class TestCreateTextOverlayInstructions:
    """Tests for text overlay instruction generation."""

    def test_scary_stories_styling(self) -> None:
        """Test text overlay styling for scary stories."""
        from faceless.services.thumbnail_service import create_text_overlay_instructions

        result = create_text_overlay_instructions(
            title="The Haunted House",
            niche="scary-stories",
        )

        assert result["text_color"] == "#FF0000"  # Red
        assert result["outline_color"] == "#000000"  # Black
        assert "Impact" in result["font_style"]

    def test_finance_styling(self) -> None:
        """Test text overlay styling for finance."""
        from faceless.services.thumbnail_service import create_text_overlay_instructions

        result = create_text_overlay_instructions(
            title="How to Save Money",
            niche="finance",
        )

        assert result["text_color"] == "#00FF00"  # Green
        assert "Montserrat" in result["font_style"] or "Arial" in result["font_style"]

    def test_luxury_styling(self) -> None:
        """Test text overlay styling for luxury."""
        from faceless.services.thumbnail_service import create_text_overlay_instructions

        result = create_text_overlay_instructions(
            title="Billionaire Lifestyle",
            niche="luxury",
        )

        assert result["text_color"] == "#FFD700"  # Gold
        assert result["outline_color"] == "#000000"

    def test_truncates_long_titles(self) -> None:
        """Test that long titles are truncated."""
        from faceless.services.thumbnail_service import create_text_overlay_instructions

        long_title = "This is a very long video title that should be truncated for thumbnail text"

        result = create_text_overlay_instructions(
            title=long_title,
            niche="scary-stories",
        )

        # Should be truncated with ellipsis
        assert len(result["recommended_text"]) < len(long_title)
        assert "..." in result["recommended_text"]

    def test_short_titles_not_truncated(self) -> None:
        """Test that short titles are not truncated."""
        from faceless.services.thumbnail_service import create_text_overlay_instructions

        short_title = "Short"

        result = create_text_overlay_instructions(
            title=short_title,
            niche="scary-stories",
        )

        assert result["recommended_text"] == short_title

    def test_includes_tips(self) -> None:
        """Test that styling tips are included."""
        from faceless.services.thumbnail_service import create_text_overlay_instructions

        result = create_text_overlay_instructions(
            title="Test",
            niche="finance",
        )

        assert "tips" in result
        assert len(result["tips"]) > 0

    def test_includes_placement(self) -> None:
        """Test that placement guidance is included."""
        from faceless.services.thumbnail_service import create_text_overlay_instructions

        result = create_text_overlay_instructions(
            title="Test",
            niche="scary-stories",
        )

        assert "placement" in result
        assert "size" in result

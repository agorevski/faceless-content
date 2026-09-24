"""
Unit tests for the thumbnail service.

Tests thumbnail prompt generation, composition, and optional overlay guidance.
"""

import json
import shutil
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from faceless.clients.azure_openai import AzureOpenAIClient
from faceless.core.exceptions import (
    FFmpegError,
    ImageGenerationError,
    InputValidationError,
)

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
        from faceless.services.thumbnail_service import generate_thumbnail_prompt

        prompt = generate_thumbnail_prompt(
            title="Test Video",
            niche="finance",
            concept="reaction",
        )

        assert "no face needed" in prompt.lower()

    def test_includes_composition_guidance(self) -> None:
        """Test that composition guidance is included."""
        from faceless.services.thumbnail_service import generate_thumbnail_prompt

        prompt = generate_thumbnail_prompt(
            title="Test",
            niche="scary-stories",
            concept="mystery",
        )

        assert "16:9" in prompt or "composition" in prompt.lower()

    @pytest.mark.parametrize("niche", ["history", "true-crime", "unknown-niche"])
    def test_fallback_for_unconfigured_niche(self, niche: str) -> None:
        """Other niches use source-grounded visuals without finance cues."""
        from faceless.services.thumbnail_service import generate_thumbnail_prompt

        prompt = generate_thumbnail_prompt(
            title="The Ancient Library",
            niche=niche,
            concept="reveal",
        )

        assert "The Ancient Library" in prompt
        assert "supplied subject faithfully" in prompt
        assert "extra claims" in prompt
        assert "finance" not in prompt.lower()
        assert "money" not in prompt.lower()
        assert "green and gold" not in prompt.lower()


# =============================================================================
# Generate Thumbnail Tests
# =============================================================================


class TestGenerateThumbnail:
    """Tests for thumbnail image generation."""

    @patch("faceless.services.thumbnail_service.AzureOpenAIClient")
    @patch("faceless.services.thumbnail_service.get_settings")
    def test_generate_thumbnail_success(
        self, mock_settings: MagicMock, mock_client_class: MagicMock, tmp_path: Path
    ) -> None:
        """Test successful thumbnail generation."""
        from faceless.services.thumbnail_service import generate_thumbnail

        mock_settings.return_value.output_base_dir = tmp_path
        mock_client = MagicMock(spec=AzureOpenAIClient)
        mock_client.generate_image.return_value = b"testimage"
        mock_client_class.return_value = mock_client

        result = generate_thumbnail(
            prompt="Test prompt",
            niche="scary-stories",
            output_name="test_thumb",
            output_dir=tmp_path,
        )

        assert result.exists()
        assert result.name == "test_thumb.png"
        assert result.read_bytes() == b"testimage"
        mock_client.generate_image.assert_called_once_with(
            "Test prompt", size="1536x1024"
        )
        mock_client.__exit__.assert_called_once()

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

    @patch("faceless.services.thumbnail_service.AzureOpenAIClient")
    @patch("faceless.services.thumbnail_service.get_settings")
    def test_generate_thumbnail_saves_prompt(
        self, mock_settings: MagicMock, mock_client_class: MagicMock, tmp_path: Path
    ) -> None:
        """Test that the prompt is saved alongside the image."""
        from faceless.services.thumbnail_service import generate_thumbnail

        mock_settings.return_value.output_base_dir = tmp_path
        mock_client = MagicMock(spec=AzureOpenAIClient)
        mock_client.generate_image.return_value = b"test"
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

    def test_generate_thumbnail_reuses_shared_client(self, tmp_path: Path) -> None:
        """The shared client owns download/error handling and its own lifecycle."""
        from faceless.services.thumbnail_service import generate_thumbnail

        client = MagicMock(spec=AzureOpenAIClient)
        client.generate_image.return_value = b"image bytes"

        result = generate_thumbnail(
            prompt="Test",
            niche="scary-stories",
            output_name="shared",
            output_dir=tmp_path,
            size="1024x1024",
            client=client,
        )

        assert result.read_bytes() == b"image bytes"
        client.generate_image.assert_called_once_with("Test", size="1024x1024")
        client.close.assert_not_called()
        client.__exit__.assert_not_called()

    def test_generate_thumbnail_replaces_empty_cached_file(
        self, tmp_path: Path
    ) -> None:
        """An interrupted, empty image file must not suppress generation."""
        from faceless.services.thumbnail_service import generate_thumbnail

        existing = tmp_path / "empty.png"
        existing.touch()
        client = MagicMock(spec=AzureOpenAIClient)
        client.generate_image.return_value = b"image"

        result = generate_thumbnail(
            "Prompt", "finance", "empty", tmp_path, client=client
        )

        assert result.read_bytes() == b"image"
        client.generate_image.assert_called_once()

    @pytest.mark.parametrize("empty_response", [False, True])
    def test_generate_thumbnail_failure_does_not_save_image(
        self, tmp_path: Path, empty_response: bool
    ) -> None:
        """A failed or empty API response never becomes a cached PNG."""
        from faceless.services.thumbnail_service import generate_thumbnail

        with patch("faceless.services.thumbnail_service.AzureOpenAIClient") as factory:
            client = factory.return_value
            if empty_response:
                client.generate_image.return_value = b""
            else:
                client.generate_image.side_effect = ImageGenerationError("API failed")
            with pytest.raises(ImageGenerationError):
                generate_thumbnail("Prompt", "finance", "failed", tmp_path)

        assert not (tmp_path / "failed.png").exists()
        client.__exit__.assert_called_once()


# =============================================================================
# Generate Thumbnail Variants Tests
# =============================================================================


class TestGenerateThumbnailVariants:
    """Tests for generating multiple thumbnail variants."""

    @pytest.mark.parametrize("num_variants", [0, -1])
    @patch("faceless.services.thumbnail_service.generate_thumbnail")
    def test_rejects_nonpositive_variant_count(
        self, mock_generate: MagicMock, num_variants: int, tmp_path: Path
    ) -> None:
        """Zero or negative counts must fail before contacting the image API."""
        from faceless.services.thumbnail_service import generate_thumbnail_variants

        with pytest.raises(InputValidationError, match="num_variants"):
            generate_thumbnail_variants(
                "Test", "finance", "test", tmp_path, num_variants=num_variants
            )
        mock_generate.assert_not_called()

    @patch("faceless.services.thumbnail_service.generate_thumbnail")
    def test_rejects_empty_concepts(
        self, mock_generate: MagicMock, tmp_path: Path
    ) -> None:
        """An empty concept selection cannot silently produce no thumbnails."""
        from faceless.services.thumbnail_service import generate_thumbnail_variants

        with pytest.raises(InputValidationError, match="concept"):
            generate_thumbnail_variants(
                "Test", "finance", "test", tmp_path, concepts=[]
            )
        mock_generate.assert_not_called()

    @patch("faceless.services.thumbnail_service._compose_thumbnail")
    @patch("faceless.services.thumbnail_service.generate_thumbnail")
    def test_generates_multiple_variants(
        self, mock_generate: MagicMock, mock_compose: MagicMock, tmp_path: Path
    ) -> None:
        """Test that every generated image is composed into its final path."""
        from faceless.services.thumbnail_service import generate_thumbnail_variants

        mock_generate.return_value = tmp_path / "thumb.png"
        mock_compose.side_effect = lambda _source, output, _title, _niche: output

        result = generate_thumbnail_variants(
            title="Test Video",
            niche="scary-stories",
            base_name="test",
            output_dir=tmp_path,
            num_variants=3,
        )

        assert len(result) == 3
        assert mock_generate.call_count == 3
        assert mock_compose.call_count == 3
        assert len(set(result)) == 3
        assert all(path.suffix == ".png" for path in result)

    @patch("faceless.services.thumbnail_service._compose_thumbnail")
    @patch("faceless.services.thumbnail_service.generate_thumbnail")
    def test_uses_niche_specific_concepts(
        self, mock_generate: MagicMock, mock_compose: MagicMock, tmp_path: Path
    ) -> None:
        """Test that niche-specific concepts are used."""
        from faceless.services.thumbnail_service import generate_thumbnail_variants

        mock_generate.return_value = tmp_path / "thumb.png"
        mock_compose.side_effect = lambda _source, output, _title, _niche: output

        generate_thumbnail_variants(
            title="Test",
            niche="scary-stories",
            base_name="test",
            output_dir=tmp_path,
        )

        for i, concept in enumerate(["mystery", "reveal", "warning"], 1):
            assert (
                mock_generate.call_args_list[i - 1]
                .args[2]
                .startswith(f"test_thumb_v{i}_{concept}_source_")
            )

    @patch("faceless.services.thumbnail_service._compose_thumbnail")
    @patch("faceless.services.thumbnail_service.generate_thumbnail")
    def test_custom_concepts(
        self, mock_generate: MagicMock, mock_compose: MagicMock, tmp_path: Path
    ) -> None:
        """Test using custom concepts."""
        from faceless.services.thumbnail_service import generate_thumbnail_variants

        mock_generate.return_value = tmp_path / "thumb.png"
        mock_compose.side_effect = lambda _source, output, _title, _niche: output

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
        """Failed images remain retryable without hiding successful variants."""
        from faceless.services.thumbnail_service import generate_thumbnail_variants

        mock_generate.side_effect = [
            tmp_path / "thumb1.png",
            ImageGenerationError("API unavailable"),
            tmp_path / "thumb3.png",
        ]
        with patch("faceless.services.thumbnail_service._compose_thumbnail") as compose:
            compose.side_effect = lambda _source, output, _title, _niche: output

            result = generate_thumbnail_variants(
                title="Test",
                niche="scary-stories",
                base_name="test",
                output_dir=tmp_path,
                num_variants=3,
            )

        assert mock_generate.call_count == 3
        assert result[0] is not None
        assert result[1] is None
        assert result[2] is not None

    @patch("faceless.services.thumbnail_service.generate_thumbnail")
    def test_marks_missing_image_for_retry(
        self, mock_generate: MagicMock, tmp_path: Path
    ) -> None:
        """A missing generated source is not a successful variant."""
        from faceless.services.thumbnail_service import generate_thumbnail_variants

        mock_generate.return_value = None
        result = generate_thumbnail_variants(
            "Test", "finance", "test", tmp_path, concepts=["reveal"]
        )
        assert result == [None]

    @patch("faceless.services.thumbnail_service._compose_thumbnail")
    def test_retry_reuses_nonempty_sources_and_only_regenerates_missing(
        self, mock_compose: MagicMock, tmp_path: Path
    ) -> None:
        """Retrying three variants pays the image API only for the failed one."""
        from faceless.services.thumbnail_service import generate_thumbnail_variants

        mock_compose.side_effect = lambda _source, output, _title, _niche: output
        client = MagicMock(spec=AzureOpenAIClient)
        client.generate_image.side_effect = [
            b"first source",
            ImageGenerationError("temporary outage"),
            b"third source",
            b"recovered source",
        ]

        options = {
            "title": "Real video title",
            "niche": "finance",
            "base_name": "episode",
            "output_dir": tmp_path,
            "client": client,
        }
        first = generate_thumbnail_variants(**options)
        second = generate_thumbnail_variants(**options)

        assert first[0] == second[0]
        assert first[1] is None
        assert second[1] is not None
        assert first[2] == second[2]
        assert client.generate_image.call_count == 4
        assert all(
            call.kwargs["size"] == "1536x1024"
            for call in client.generate_image.call_args_list
        )
        client.close.assert_not_called()

    @patch("faceless.services.thumbnail_service.generate_thumbnail")
    def test_composition_error_is_reported_and_cleans_up(
        self, mock_generate: MagicMock, tmp_path: Path
    ) -> None:
        """Corrupt image input fails clearly and removes intermediate files."""
        from faceless.services.thumbnail_service import generate_thumbnail_variants

        if shutil.which("ffmpeg") is None:
            pytest.skip("FFmpeg is not installed")
        source = tmp_path / "broken.png"
        source.write_bytes(b"not an image")
        mock_generate.return_value = source
        with pytest.raises(FFmpegError, match="composition failed"):
            generate_thumbnail_variants(
                "Actual title", "finance", "test", tmp_path, concepts=["reveal"]
            )
        assert not (tmp_path / "test_thumb_v1_reveal.png").exists()
        assert not list(tmp_path.glob(".thumbnail-*"))

    def test_selects_only_real_title_words(self) -> None:
        """Thumbnail copy never introduces a claim or invented statistic."""
        from faceless.services.thumbnail_service import _thumbnail_copy

        title = "Why Stock Markets Fell This Week According to Research"
        lines = _thumbnail_copy(title)
        assert " ".join(lines) == "Why Stock Markets Fell This"
        assert len(lines) <= 5
        with pytest.raises(InputValidationError):
            _thumbnail_copy(" \n\t ")

    def test_long_word_is_shortened_for_readability(self) -> None:
        """Unusually long title words do not shrink the whole caption to tiny text."""
        from faceless.services.thumbnail_service import _text_width, _thumbnail_copy

        lines = _thumbnail_copy("Supercalifragilisticexpialidocious story revealed")
        assert lines[0].endswith("…")
        assert max(_text_width(line) for line in lines) <= 8.0

    @patch("faceless.services.thumbnail_service._compose_thumbnail")
    @patch("faceless.services.thumbnail_service.generate_thumbnail")
    def test_image_cache_key_changes_with_title(
        self, mock_generate: MagicMock, mock_compose: MagicMock, tmp_path: Path
    ) -> None:
        """Reusing a basename for another title cannot reuse its old raw imagery."""
        from faceless.services.thumbnail_service import generate_thumbnail_variants

        mock_generate.return_value = tmp_path / "source.png"
        mock_compose.side_effect = lambda _source, output, _title, _niche: output
        for title in ("How Trees Grow", "Why Trees Die"):
            generate_thumbnail_variants(
                title, "finance", "tree", tmp_path, concepts=["reveal"]
            )
        assert (
            mock_generate.call_args_list[0].args[2]
            != (mock_generate.call_args_list[1].args[2])
        )

    @patch("faceless.services.thumbnail_service.generate_thumbnail")
    def test_composes_real_png_with_escaped_unicode_copy(
        self, mock_generate: MagicMock, tmp_path: Path
    ) -> None:
        """The composed PNG has correct size, legible white copy and a visible image."""
        from faceless.services.thumbnail_service import generate_thumbnail_variants

        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            pytest.skip("FFmpeg and ffprobe are required for the smoke test")
        output_dir = tmp_path / "thumb's:東京"
        output_dir.mkdir()
        source = output_dir / "source.png"
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "color=c=0x334455:s=640x360",
                "-frames:v",
                "1",
                "-update",
                "1",
                str(source),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        mock_generate.return_value = source
        paths = generate_thumbnail_variants(
            title="Why O'Brien's Café: 100% %{metadata}",
            niche="scary-stories",
            base_name="../episode;$(whoami)",
            output_dir=output_dir,
            concepts=["reveal"],
        )
        assert len(paths) == 1
        result = paths[0]
        assert result.parent == output_dir
        assert result.is_file()
        probe = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=codec_name,width,height",
                "-of",
                "json",
                str(result),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        assert json.loads(probe.stdout)["streams"][0] == {
            "codec_name": "png",
            "width": 1280,
            "height": 720,
        }
        pixels = subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(result),
                "-frames:v",
                "1",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "rgb24",
                "pipe:1",
            ],
            check=True,
            capture_output=True,
        ).stdout
        assert len(pixels) == 1280 * 720 * 3

        def rgb(x: int, y: int) -> tuple[int, int, int]:
            offset = (y * 1280 + x) * 3
            return pixels[offset], pixels[offset + 1], pixels[offset + 2]

        assert rgb(68, 300)[0] > 175  # niche accent, inside safe margins
        assert rgb(900, 360)[2] > 55  # original image remains visible
        bright_text = sum(
            all(channel > 180 for channel in rgb(x, y))
            for y in range(185, 540, 4)
            for x in range(100, 625, 4)
        )
        assert bright_text > 50
        assert not list(output_dir.glob(".thumbnail-*"))


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

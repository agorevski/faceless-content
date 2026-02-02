"""
Unit tests for the deprecated scraper service.

Tests the legacy scraping functions that are kept for backwards compatibility.
"""

import json
import warnings
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# =============================================================================
# Text Cleaning Tests
# =============================================================================


class TestCleanText:
    """Tests for the clean_text function."""

    def test_clean_bold_markdown(self) -> None:
        """Test removing markdown bold formatting."""
        from faceless.services.scraper_service import clean_text

        text = "This is **bold** text"
        result = clean_text(text)
        assert result == "This is bold text"

    def test_clean_italic_markdown(self) -> None:
        """Test removing markdown italic formatting."""
        from faceless.services.scraper_service import clean_text

        text = "This is *italic* text"
        result = clean_text(text)
        assert result == "This is italic text"

    def test_clean_underline_markdown(self) -> None:
        """Test removing markdown underline formatting."""
        from faceless.services.scraper_service import clean_text

        text = "This is __underlined__ text"
        result = clean_text(text)
        assert result == "This is underlined text"

    def test_clean_strikethrough_markdown(self) -> None:
        """Test removing markdown strikethrough formatting."""
        from faceless.services.scraper_service import clean_text

        text = "This is ~~deleted~~ text"
        result = clean_text(text)
        assert result == "This is deleted text"

    def test_clean_markdown_links(self) -> None:
        """Test removing markdown links but keeping text."""
        from faceless.services.scraper_service import clean_text

        text = "Check out [this link](https://example.com) here"
        result = clean_text(text)
        assert result == "Check out this link here"

    def test_clean_multiple_newlines(self) -> None:
        """Test collapsing multiple newlines."""
        from faceless.services.scraper_service import clean_text

        text = "Line 1\n\n\n\nLine 2"
        result = clean_text(text)
        assert result == "Line 1\n\nLine 2"

    def test_clean_multiple_spaces(self) -> None:
        """Test collapsing multiple spaces."""
        from faceless.services.scraper_service import clean_text

        text = "Multiple    spaces   here"
        result = clean_text(text)
        assert result == "Multiple spaces here"

    def test_clean_superscript(self) -> None:
        """Test removing Reddit superscript."""
        from faceless.services.scraper_service import clean_text

        text = "Text ^superscript"
        result = clean_text(text)
        assert "superscript" in result

    def test_clean_html_entities(self) -> None:
        """Test converting HTML entities."""
        from faceless.services.scraper_service import clean_text

        text = "Tom &amp; Jerry &lt;3 &gt;"
        result = clean_text(text)
        assert "&" in result
        assert "<" in result
        assert ">" in result

    def test_clean_strips_whitespace(self) -> None:
        """Test that result is stripped."""
        from faceless.services.scraper_service import clean_text

        text = "   Some text with spaces   "
        result = clean_text(text)
        assert result == "Some text with spaces"


# =============================================================================
# Save Story Tests
# =============================================================================


class TestSaveStory:
    """Tests for the save_story function."""

    def test_save_story_with_custom_filename(self, tmp_path: Path) -> None:
        """Test saving a story with custom filename."""
        from faceless.services.scraper_service import save_story

        story = {
            "title": "Test Story Title",
            "content": "This is the story content.",
            "author": "test_author",
            "score": 100,
            "url": "https://example.com",
        }

        output_path = save_story(
            story, "scary-stories", output_dir=tmp_path, filename="custom.json"
        )

        assert output_path.exists()
        assert output_path.name == "custom.json"

        # Verify content
        with open(output_path) as f:
            saved = json.load(f)
        assert saved["title"] == "Test Story Title"

    def test_save_story_generates_filename_from_title(self, tmp_path: Path) -> None:
        """Test saving a story generates filename from title."""
        from faceless.services.scraper_service import save_story

        story = {
            "title": "My Amazing Story!",
            "content": "Story content here.",
        }

        output_path = save_story(story, "scary-stories", output_dir=tmp_path)

        assert output_path.exists()
        assert "my-amazing-story" in output_path.name.lower()

    def test_save_story_creates_output_directory(self, tmp_path: Path) -> None:
        """Test that save_story creates the output directory."""
        from faceless.services.scraper_service import save_story

        output_dir = tmp_path / "new" / "nested" / "dir"
        story = {"title": "Test", "content": "Content"}

        output_path = save_story(
            story, "scary-stories", output_dir=output_dir, filename="test.json"
        )

        assert output_dir.exists()
        assert output_path.exists()


# =============================================================================
# Generate Image Prompt Tests
# =============================================================================


class TestGenerateImagePrompt:
    """Tests for the generate_image_prompt function."""

    def test_scary_stories_first_scene(self) -> None:
        """Test image prompt for scary stories opening scene."""
        from faceless.services.scraper_service import generate_image_prompt

        prompt = generate_image_prompt(
            "The old house stood at the end of the dark street.",
            "scary-stories",
            scene_num=1,
            total_scenes=5,
        )

        assert "Establishing shot" in prompt
        assert "horror" in prompt.lower() or "cinematography" in prompt.lower()

    def test_scary_stories_last_scene(self) -> None:
        """Test image prompt for scary stories climactic scene."""
        from faceless.services.scraper_service import generate_image_prompt

        prompt = generate_image_prompt(
            "The creature emerged from the shadows.",
            "scary-stories",
            scene_num=5,
            total_scenes=5,
        )

        assert "Climactic" in prompt
        assert "horror" in prompt.lower() or "tension" in prompt.lower()

    def test_scary_stories_location_detection(self) -> None:
        """Test that scary stories prompt detects location keywords."""
        from faceless.services.scraper_service import generate_image_prompt

        prompt = generate_image_prompt(
            "I walked into the basement and saw something terrifying.",
            "scary-stories",
            scene_num=2,
            total_scenes=5,
        )

        assert "basement" in prompt.lower()

    def test_scary_stories_entity_detection(self) -> None:
        """Test that scary stories prompt detects entity keywords."""
        from faceless.services.scraper_service import generate_image_prompt

        prompt = generate_image_prompt(
            "A dark figure stood in the corner watching me.",
            "scary-stories",
            scene_num=3,
            total_scenes=5,
        )

        assert "figure" in prompt.lower()

    def test_finance_prompt(self) -> None:
        """Test image prompt for finance niche."""
        from faceless.services.scraper_service import generate_image_prompt

        prompt = generate_image_prompt(
            "Save money by investing in stocks early.",
            "finance",
            scene_num=1,
            total_scenes=3,
        )

        assert "Professional" in prompt or "business" in prompt.lower()
        assert "green" in prompt.lower() or "gold" in prompt.lower()

    def test_luxury_prompt(self) -> None:
        """Test image prompt for luxury niche."""
        from faceless.services.scraper_service import generate_image_prompt

        prompt = generate_image_prompt(
            "The yacht sailed across the crystal blue waters.",
            "luxury",
            scene_num=2,
            total_scenes=4,
        )

        assert "luxury" in prompt.lower() or "Elegant" in prompt

    def test_unknown_niche_prompt(self) -> None:
        """Test image prompt for unknown niche falls back to generic."""
        from faceless.services.scraper_service import generate_image_prompt

        prompt = generate_image_prompt(
            "Some content for an unknown niche.",
            "unknown-niche",
            scene_num=1,
            total_scenes=2,
        )

        assert "Scene 1" in prompt


# =============================================================================
# Story to Script Tests
# =============================================================================


class TestStoryToScript:
    """Tests for the story_to_script function."""

    def test_story_to_script_basic(self) -> None:
        """Test basic story to script conversion."""
        from faceless.services.scraper_service import story_to_script

        story = {
            "title": "Test Story",
            "content": "This is paragraph one with some content.\n\n"
            "This is paragraph two with more content.\n\n"
            "This is paragraph three with final content.",
            "source": "r/nosleep",
            "author": "test_author",
            "url": "https://reddit.com/test",
        }

        script = story_to_script(story, "scary-stories")

        assert script["title"] == "Test Story"
        assert script["source"] == "r/nosleep"
        assert script["author"] == "test_author"
        assert script["niche"] == "scary-stories"
        assert "scenes" in script
        assert len(script["scenes"]) > 0

    def test_story_to_script_scene_structure(self) -> None:
        """Test that scenes have correct structure."""
        from faceless.services.scraper_service import story_to_script

        long_content = " ".join(["word"] * 300)  # 300 words
        story = {
            "title": "Test",
            "content": long_content,
        }

        script = story_to_script(story, "scary-stories", words_per_scene=100)

        for scene in script["scenes"]:
            assert "scene_number" in scene
            assert "narration" in scene
            assert "image_prompt" in scene
            assert "duration_estimate" in scene
            assert scene["scene_number"] >= 1

    def test_story_to_script_max_scenes(self) -> None:
        """Test that max_scenes limit is respected."""
        from faceless.services.scraper_service import story_to_script

        # Create story with enough content for many scenes
        long_content = " ".join(["word"] * 1000)
        story = {"title": "Long Story", "content": long_content}

        script = story_to_script(
            story, "scary-stories", max_scenes=3, words_per_scene=50
        )

        assert len(script["scenes"]) <= 3

    def test_story_to_script_duration_estimate(self) -> None:
        """Test that duration is estimated based on word count."""
        from faceless.services.scraper_service import story_to_script

        # 50 words at ~150 words/min = ~20 seconds
        content = " ".join(["word"] * 50)
        story = {"title": "Test", "content": content}

        script = story_to_script(story, "scary-stories", words_per_scene=100)

        for scene in script["scenes"]:
            assert scene["duration_estimate"] > 0


# =============================================================================
# Fetch Reddit Stories Tests (Mocked)
# =============================================================================


class TestFetchRedditStories:
    """Tests for fetch_reddit_stories with mocked HTTP."""

    @patch("faceless.services.scraper_service.httpx.Client")
    def test_fetch_reddit_stories_success(self, mock_client_class: MagicMock) -> None:
        """Test successful Reddit story fetching."""
        from faceless.services.scraper_service import fetch_reddit_stories

        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "children": [
                    {
                        "data": {
                            "title": "Test Story",
                            "selftext": "This is a test story with content.",
                            "author": "test_user",
                            "score": 500,
                            "permalink": "/r/nosleep/test",
                        }
                    },
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        stories = fetch_reddit_stories("nosleep", limit=1, min_score=100)

        assert len(stories) == 1
        assert stories[0]["title"] == "Test Story"
        assert stories[0]["author"] == "test_user"

    @patch("faceless.services.scraper_service.httpx.Client")
    def test_fetch_reddit_stories_filters_low_score(
        self, mock_client_class: MagicMock
    ) -> None:
        """Test that low score posts are filtered out."""
        from faceless.services.scraper_service import fetch_reddit_stories

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "children": [
                    {
                        "data": {
                            "title": "Low Score Story",
                            "selftext": "Content here",
                            "author": "user",
                            "score": 50,  # Below min_score
                            "permalink": "/r/nosleep/low",
                        }
                    },
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        stories = fetch_reddit_stories("nosleep", limit=1, min_score=100)

        assert len(stories) == 0

    @patch("faceless.services.scraper_service.httpx.Client")
    def test_fetch_reddit_stories_filters_no_content(
        self, mock_client_class: MagicMock
    ) -> None:
        """Test that posts without content are filtered out."""
        from faceless.services.scraper_service import fetch_reddit_stories

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "children": [
                    {
                        "data": {
                            "title": "Link Post",
                            "selftext": "",  # No content
                            "author": "user",
                            "score": 500,
                            "permalink": "/r/nosleep/link",
                        }
                    },
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        stories = fetch_reddit_stories("nosleep", limit=1, min_score=100)

        assert len(stories) == 0


# =============================================================================
# Fetch Creepypasta Tests
# =============================================================================


class TestFetchCreepypasta:
    """Tests for fetch_creepypasta function."""

    @patch("faceless.services.scraper_service.fetch_reddit_stories")
    def test_fetch_creepypasta_calls_reddit(self, mock_fetch_reddit: MagicMock) -> None:
        """Test that fetch_creepypasta uses Reddit as fallback."""
        from faceless.services.scraper_service import fetch_creepypasta

        mock_fetch_reddit.return_value = [{"title": "Test"}]

        result = fetch_creepypasta(limit=5)

        mock_fetch_reddit.assert_called_once_with("creepypasta", limit=5)
        assert len(result) == 1


# =============================================================================
# Fetch and Process Stories Tests
# =============================================================================


class TestFetchAndProcessStories:
    """Tests for fetch_and_process_stories function."""

    @patch("faceless.services.scraper_service.fetch_reddit_stories")
    @patch("faceless.services.scraper_service.get_settings")
    def test_fetch_and_process_scary_stories(
        self, mock_settings: MagicMock, mock_fetch: MagicMock, tmp_path: Path
    ) -> None:
        """Test processing scary stories."""
        from faceless.services.scraper_service import fetch_and_process_stories

        mock_settings.return_value.output_base_dir = tmp_path

        mock_fetch.return_value = [
            {
                "title": "Scary Story",
                "content": "This is a scary story content paragraph.\n\n"
                "Another paragraph with more content.",
                "source": "r/nosleep",
                "author": "author1",
            }
        ]

        result = fetch_and_process_stories(
            "scary-stories", count=1, output_dir=tmp_path
        )

        assert len(result) == 1
        assert result[0].exists()

    @patch("faceless.services.scraper_service.fetch_reddit_stories")
    @patch("faceless.services.scraper_service.get_settings")
    def test_fetch_and_process_finance(
        self, mock_settings: MagicMock, mock_fetch: MagicMock, tmp_path: Path
    ) -> None:
        """Test processing finance content."""
        from faceless.services.scraper_service import fetch_and_process_stories

        mock_settings.return_value.output_base_dir = tmp_path

        mock_fetch.return_value = [
            {
                "title": "Finance Tips",
                "content": "Save money by investing early.\n\nMore tips here.",
                "source": "r/personalfinance",
                "author": "finance_guru",
            }
        ]

        result = fetch_and_process_stories("finance", count=1, output_dir=tmp_path)

        assert len(result) == 1

    @patch("faceless.services.scraper_service.fetch_reddit_stories")
    @patch("faceless.services.scraper_service.get_settings")
    def test_fetch_and_process_luxury(
        self, mock_settings: MagicMock, mock_fetch: MagicMock, tmp_path: Path
    ) -> None:
        """Test processing luxury content."""
        from faceless.services.scraper_service import fetch_and_process_stories

        mock_settings.return_value.output_base_dir = tmp_path

        mock_fetch.return_value = [
            {
                "title": "Luxury Lifestyle",
                "content": "Experience the finest things.\n\nMore luxury content.",
                "source": "r/luxury",
                "author": "luxury_fan",
            }
        ]

        result = fetch_and_process_stories("luxury", count=1, output_dir=tmp_path)

        assert len(result) == 1

    @patch("faceless.services.scraper_service.get_settings")
    def test_fetch_and_process_unknown_niche(
        self, mock_settings: MagicMock, tmp_path: Path
    ) -> None:
        """Test handling unknown niche."""
        from faceless.services.scraper_service import fetch_and_process_stories

        mock_settings.return_value.output_base_dir = tmp_path

        result = fetch_and_process_stories(
            "unknown-niche", count=1, output_dir=tmp_path
        )

        assert len(result) == 0

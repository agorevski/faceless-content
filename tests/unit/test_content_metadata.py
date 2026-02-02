"""
Tests for the content_metadata module.
Tests metadata generation for TikTok posting.
"""

from pathlib import Path

import pytest

from faceless.services.metadata_service import (
    format_metadata_for_display,
    generate_content_metadata,
    generate_series_metadata,
    load_metadata,
    save_metadata,
)

# =============================================================================
# GENERATE_CONTENT_METADATA TESTS
# =============================================================================


class TestGenerateContentMetadata:
    """Tests for generate_content_metadata function."""

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_returns_dict_for_all_niches(self, niche: str):
        """Test metadata generation for all niches."""
        metadata = generate_content_metadata(
            niche=niche,
            title="Test Video",
            video_duration=60.0,
        )

        assert isinstance(metadata, dict)
        assert metadata["niche"] == niche

    def test_contains_required_fields(self):
        """Test that metadata contains all required fields."""
        metadata = generate_content_metadata(
            niche="scary-stories",
            title="Test Video",
            video_duration=60.0,
        )

        # Core fields
        assert "generated_at" in metadata
        assert "niche" in metadata
        assert "title" in metadata
        assert "video_duration_seconds" in metadata

        # Caption and hashtags
        assert "caption" in metadata
        assert "hashtags" in metadata
        assert "hashtag_string" in metadata
        assert "full_post_text" in metadata

        # Engagement elements
        assert "first_frame_hook" in metadata
        assert "mid_video_hook" in metadata
        assert "comment_trigger" in metadata
        assert "pinned_comment_suggestion" in metadata
        assert "loop_structure" in metadata

        # Posting schedule
        assert "optimal_posting" in metadata
        assert "datetime" in metadata["optimal_posting"]
        assert "formatted" in metadata["optimal_posting"]

        # Target metrics
        assert "target_metrics" in metadata

    def test_title_preserved(self):
        """Test that title is preserved in metadata."""
        metadata = generate_content_metadata(
            niche="finance",
            title="5 Money Mistakes to Avoid",
            video_duration=45.0,
        )

        assert metadata["title"] == "5 Money Mistakes to Avoid"

    def test_duration_preserved(self):
        """Test that duration is preserved in metadata."""
        metadata = generate_content_metadata(
            niche="luxury",
            title="Luxury Watch Collection",
            video_duration=90.0,
        )

        assert metadata["video_duration_seconds"] == 90.0

    def test_hashtags_are_list(self):
        """Test that hashtags is a list of strings."""
        metadata = generate_content_metadata(
            niche="scary-stories",
            title="Haunted House Story",
            video_duration=60.0,
        )

        assert isinstance(metadata["hashtags"], list)
        assert len(metadata["hashtags"]) > 0
        assert all(isinstance(h, str) for h in metadata["hashtags"])
        assert all(h.startswith("#") for h in metadata["hashtags"])

    def test_with_series_name(self):
        """Test metadata generation with series name."""
        metadata = generate_content_metadata(
            niche="scary-stories",
            title="The Basement",
            video_duration=60.0,
            series_name="3AM Stories",
            part_number=5,
        )

        assert metadata["series"] is not None
        assert metadata["series"]["name"] == "3AM Stories"
        assert metadata["series"]["part_number"] == 5
        assert "#3AMStories" in metadata["series"]["series_hashtag"]

    def test_with_format_name(self):
        """Test metadata generation with format name."""
        metadata = generate_content_metadata(
            niche="scary-stories",
            title="Rules of the Abandoned School",
            video_duration=60.0,
            format_name="rules_of_location",
        )

        assert metadata["format"] is not None
        assert metadata["format"]["name"] == "rules_of_location"

    def test_custom_caption(self):
        """Test custom caption override."""
        custom = "My custom caption here"
        metadata = generate_content_metadata(
            niche="finance",
            title="Test",
            video_duration=60.0,
            custom_caption=custom,
        )

        assert metadata["caption"] == custom


class TestEngagementElements:
    """Tests for engagement elements in metadata."""

    def test_first_frame_hook_structure(self):
        """Test first_frame_hook structure."""
        metadata = generate_content_metadata(
            niche="scary-stories",
            title="Test",
            video_duration=60.0,
        )

        hook = metadata["first_frame_hook"]
        assert "text" in hook
        assert "type" in hook
        assert len(hook["text"]) > 0

    def test_mid_video_hook_structure(self):
        """Test mid_video_hook structure."""
        metadata = generate_content_metadata(
            niche="finance",
            title="Test",
            video_duration=60.0,
        )

        hook = metadata["mid_video_hook"]
        assert "content" in hook or "text" in hook

    def test_comment_trigger_structure(self):
        """Test comment_trigger structure."""
        metadata = generate_content_metadata(
            niche="luxury",
            title="Test",
            video_duration=60.0,
        )

        trigger = metadata["comment_trigger"]
        assert "content" in trigger or "text" in trigger

    def test_pinned_comment_is_string(self):
        """Test pinned_comment_suggestion is a string."""
        metadata = generate_content_metadata(
            niche="scary-stories",
            title="Test",
            video_duration=60.0,
        )

        assert isinstance(metadata["pinned_comment_suggestion"], str)
        assert len(metadata["pinned_comment_suggestion"]) > 0


class TestOptimalPosting:
    """Tests for optimal posting information."""

    def test_posting_info_structure(self):
        """Test optimal_posting structure."""
        metadata = generate_content_metadata(
            niche="scary-stories",
            title="Test",
            video_duration=60.0,
        )

        posting = metadata["optimal_posting"]
        assert "datetime" in posting
        assert "formatted" in posting
        assert "day_rating" in posting
        assert "window_priority" in posting

    def test_formatted_is_readable(self):
        """Test that formatted time is human-readable."""
        metadata = generate_content_metadata(
            niche="finance",
            title="Test",
            video_duration=60.0,
        )

        formatted = metadata["optimal_posting"]["formatted"]
        # Should contain day name and time
        assert any(
            day in formatted
            for day in [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
        )


# =============================================================================
# SAVE AND LOAD METADATA TESTS
# =============================================================================


class TestSaveLoadMetadata:
    """Tests for save_metadata and load_metadata functions."""

    def test_save_metadata(self, tmp_path):
        """Test saving metadata to file."""
        metadata = generate_content_metadata(
            niche="scary-stories",
            title="Test Video",
            video_duration=60.0,
        )

        output_path = str(tmp_path / "test_metadata.json")
        result_path = save_metadata(metadata, output_path)

        assert Path(result_path).exists()
        assert result_path == output_path

    def test_load_metadata(self, tmp_path):
        """Test loading metadata from file."""
        metadata = generate_content_metadata(
            niche="finance",
            title="Money Tips",
            video_duration=45.0,
        )

        output_path = str(tmp_path / "test_metadata.json")
        save_metadata(metadata, output_path)

        loaded = load_metadata(output_path)

        assert loaded["niche"] == "finance"
        assert loaded["title"] == "Money Tips"

    def test_roundtrip_preserves_data(self, tmp_path):
        """Test that save/load roundtrip preserves data."""
        metadata = generate_content_metadata(
            niche="luxury",
            title="Luxury Cars",
            video_duration=90.0,
            series_name="Mega Yacht Monday",
            part_number=3,
        )

        output_path = str(tmp_path / "roundtrip.json")
        save_metadata(metadata, output_path)
        loaded = load_metadata(output_path)

        assert loaded["title"] == metadata["title"]
        assert loaded["video_duration_seconds"] == metadata["video_duration_seconds"]
        assert loaded["series"]["name"] == metadata["series"]["name"]


# =============================================================================
# SERIES METADATA TESTS
# =============================================================================


class TestGenerateSeriesMetadata:
    """Tests for generate_series_metadata function."""

    def test_generates_correct_count(self):
        """Test that correct number of metadata entries are generated."""
        titles = ["Part 1", "Part 2", "Part 3"]
        metadata_list = generate_series_metadata(
            niche="scary-stories",
            series_name="The Investigation",
            titles=titles,
        )

        assert len(metadata_list) == 3

    def test_part_numbers_correct(self):
        """Test that part numbers are correct."""
        titles = ["Episode 1", "Episode 2"]
        metadata_list = generate_series_metadata(
            niche="finance",
            series_name="Money Mistakes",
            titles=titles,
        )

        assert metadata_list[0]["series"]["part_number"] == 1
        assert metadata_list[1]["series"]["part_number"] == 2

    def test_series_name_consistent(self):
        """Test that series name is consistent across all entries."""
        titles = ["A", "B", "C"]
        metadata_list = generate_series_metadata(
            niche="luxury",
            series_name="Billionaire Life",
            titles=titles,
        )

        for metadata in metadata_list:
            assert metadata["series"]["name"] == "Billionaire Life"

    def test_custom_durations(self):
        """Test with custom durations per video."""
        titles = ["Short", "Medium", "Long"]
        durations = [30.0, 60.0, 90.0]

        metadata_list = generate_series_metadata(
            niche="scary-stories",
            series_name="Test",
            titles=titles,
            video_durations=durations,
        )

        assert metadata_list[0]["video_duration_seconds"] == 30.0
        assert metadata_list[1]["video_duration_seconds"] == 60.0
        assert metadata_list[2]["video_duration_seconds"] == 90.0


# =============================================================================
# DISPLAY FORMATTING TESTS
# =============================================================================


class TestFormatMetadataForDisplay:
    """Tests for format_metadata_for_display function."""

    def test_returns_string(self):
        """Test that function returns a string."""
        metadata = generate_content_metadata(
            niche="scary-stories",
            title="Test",
            video_duration=60.0,
        )

        result = format_metadata_for_display(metadata)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_title(self):
        """Test that display contains title."""
        metadata = generate_content_metadata(
            niche="finance",
            title="My Finance Video",
            video_duration=60.0,
        )

        result = format_metadata_for_display(metadata)

        assert "My Finance Video" in result

    def test_contains_hashtags(self):
        """Test that display contains hashtags section."""
        metadata = generate_content_metadata(
            niche="luxury",
            title="Test",
            video_duration=60.0,
        )

        result = format_metadata_for_display(metadata)

        assert "HASHTAGS" in result

    def test_contains_posting_info(self):
        """Test that display contains posting info."""
        metadata = generate_content_metadata(
            niche="scary-stories",
            title="Test",
            video_duration=60.0,
        )

        result = format_metadata_for_display(metadata)

        assert "POSTING" in result or "posting" in result.lower()

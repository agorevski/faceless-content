"""
Tests for the hashtags module.
Tests hashtag ladder system and generation utilities.
"""

import os
import sys

import pytest

# Add pipeline directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "pipeline"))

from hashtags import (
    HASHTAG_LADDER,
    TRENDING_TOPICS,
    analyze_hashtag_coverage,
    generate_hashtag_set,
    generate_hashtag_string,
    get_all_hashtags,
    get_format_specific_hashtags,
    get_series_suggestions,
)

# =============================================================================
# HASHTAG LADDER STRUCTURE TESTS
# =============================================================================


class TestHashtagLadderStructure:
    """Tests for hashtag ladder data structure."""

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_niche_exists_in_ladder(self, niche: str):
        """Test that all niches exist in the ladder."""
        assert niche in HASHTAG_LADDER

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_ladder_has_all_levels(self, niche: str):
        """Test that each niche has all required levels."""
        ladder = HASHTAG_LADDER[niche]

        assert "mega" in ladder
        assert "niche_broad" in ladder
        assert "niche_specific" in ladder
        assert "series_suggestions" in ladder

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_ladder_levels_not_empty(self, niche: str):
        """Test that ladder levels have hashtags."""
        ladder = HASHTAG_LADDER[niche]

        assert len(ladder["mega"]) > 0
        assert len(ladder["niche_broad"]) > 0
        assert len(ladder["niche_specific"]) > 0
        assert len(ladder["series_suggestions"]) > 0

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_hashtags_start_with_hash(self, niche: str):
        """Test that all hashtags start with #."""
        ladder = HASHTAG_LADDER[niche]

        for level in ["mega", "niche_broad", "niche_specific", "series_suggestions"]:
            for tag in ladder[level]:
                assert tag.startswith("#"), f"Tag '{tag}' doesn't start with #"

    def test_mega_hashtags_are_universal(self):
        """Test that mega hashtags include common viral tags."""
        for niche in ["scary-stories", "finance", "luxury"]:
            mega = HASHTAG_LADDER[niche]["mega"]
            assert "#fyp" in mega or "#foryou" in mega


# =============================================================================
# TRENDING TOPICS TESTS
# =============================================================================


class TestTrendingTopics:
    """Tests for trending topics structure."""

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_trending_topics_exist(self, niche: str):
        """Test that trending topics exist for all niches."""
        assert niche in TRENDING_TOPICS
        assert len(TRENDING_TOPICS[niche]) > 0


# =============================================================================
# GENERATE_HASHTAG_SET TESTS
# =============================================================================


class TestGenerateHashtagSet:
    """Tests for generate_hashtag_set function."""

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_generate_hashtag_set_returns_list(self, niche: str):
        """Test that generate_hashtag_set returns a list."""
        hashtags = generate_hashtag_set(niche)

        assert isinstance(hashtags, list)
        assert len(hashtags) > 0

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_generate_hashtag_set_default_count(self, niche: str):
        """Test that default count is 7 hashtags."""
        hashtags = generate_hashtag_set(niche)

        assert len(hashtags) == 7

    def test_generate_hashtag_set_custom_count(self):
        """Test custom hashtag count."""
        hashtags = generate_hashtag_set("scary-stories", total_count=5)

        assert len(hashtags) == 5

    def test_generate_hashtag_set_all_start_with_hash(self):
        """Test that all generated hashtags start with #."""
        hashtags = generate_hashtag_set("finance")

        for tag in hashtags:
            assert tag.startswith("#"), f"Tag '{tag}' doesn't start with #"

    def test_generate_hashtag_set_no_duplicates(self):
        """Test that generated set has no duplicates."""
        hashtags = generate_hashtag_set("luxury")

        assert len(hashtags) == len(set(hashtags))

    def test_generate_hashtag_set_custom_series_tag(self):
        """Test custom series tag inclusion."""
        custom_tag = "#MyCustomSeries"
        hashtags = generate_hashtag_set("scary-stories", series_tag=custom_tag)

        assert custom_tag in hashtags

    def test_generate_hashtag_set_series_tag_without_hash(self):
        """Test that series tag without # gets it added."""
        custom_tag = "MyCustomSeries"
        hashtags = generate_hashtag_set("scary-stories", series_tag=custom_tag)

        assert "#MyCustomSeries" in hashtags

    def test_generate_hashtag_set_without_trending(self):
        """Test generation without trending topics."""
        hashtags = generate_hashtag_set("finance", include_trending=False)

        # Should still have other hashtags
        assert len(hashtags) > 0


# =============================================================================
# GENERATE_HASHTAG_STRING TESTS
# =============================================================================


class TestGenerateHashtagString:
    """Tests for generate_hashtag_string function."""

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_generate_hashtag_string_returns_string(self, niche: str):
        """Test that generate_hashtag_string returns a string."""
        result = generate_hashtag_string(niche)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_hashtag_string_space_separated(self):
        """Test that hashtags are space-separated."""
        result = generate_hashtag_string("scary-stories")

        # Should have spaces between hashtags
        assert " " in result

        # Each part should start with #
        parts = result.split()
        for part in parts:
            assert part.startswith("#")


# =============================================================================
# GET_SERIES_SUGGESTIONS TESTS
# =============================================================================


class TestGetSeriesSuggestions:
    """Tests for get_series_suggestions function."""

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_get_series_suggestions_returns_list(self, niche: str):
        """Test that get_series_suggestions returns a list."""
        suggestions = get_series_suggestions(niche)

        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

    def test_get_series_suggestions_unknown_niche(self):
        """Test that unknown niche returns empty list."""
        suggestions = get_series_suggestions("unknown-niche")

        assert suggestions == []


# =============================================================================
# GET_ALL_HASHTAGS TESTS
# =============================================================================


class TestGetAllHashtags:
    """Tests for get_all_hashtags function."""

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_get_all_hashtags_returns_dict(self, niche: str):
        """Test that get_all_hashtags returns a dict."""
        all_tags = get_all_hashtags(niche)

        assert isinstance(all_tags, dict)
        assert len(all_tags) > 0

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_get_all_hashtags_includes_trending(self, niche: str):
        """Test that result includes trending topics."""
        all_tags = get_all_hashtags(niche)

        assert "trending" in all_tags

    def test_get_all_hashtags_unknown_niche(self):
        """Test that unknown niche returns empty dict."""
        all_tags = get_all_hashtags("unknown-niche")

        assert all_tags == {}


# =============================================================================
# ANALYZE_HASHTAG_COVERAGE TESTS
# =============================================================================


class TestAnalyzeHashtagCoverage:
    """Tests for analyze_hashtag_coverage function."""

    def test_analyze_coverage_returns_dict(self):
        """Test that analyze_hashtag_coverage returns a dict."""
        hashtags = ["#fyp", "#scary", "#horror"]
        analysis = analyze_hashtag_coverage(hashtags, "scary-stories")

        assert isinstance(analysis, dict)

    def test_analyze_coverage_counts_correct(self):
        """Test that coverage analysis counts correctly."""
        hashtags = [
            "#fyp",
            "#foryou",
            "#scarystory",
            "#horror",
            "#nosleep",
            "#truescary",
        ]
        analysis = analyze_hashtag_coverage(hashtags, "scary-stories")

        assert analysis["total_count"] == 6
        assert analysis["mega_count"] >= 1  # #fyp or #foryou
        assert analysis["broad_count"] >= 1  # #scarystory or #horror
        assert analysis["specific_count"] >= 1  # #nosleep or #truescary

    def test_analyze_coverage_recommendations(self):
        """Test that analysis provides recommendations."""
        # Minimal hashtag set should get recommendations
        hashtags = ["#fyp"]
        analysis = analyze_hashtag_coverage(hashtags, "scary-stories")

        assert "recommendations" in analysis
        assert len(analysis["recommendations"]) > 0

    def test_analyze_coverage_good_set(self):
        """Test that well-balanced set has fewer recommendations."""
        # Generate a good set
        hashtags = generate_hashtag_set("scary-stories")
        analysis = analyze_hashtag_coverage(hashtags, "scary-stories")

        # Should have coverage in multiple areas
        assert analysis["total_count"] >= 5

    def test_analyze_coverage_unknown_niche(self):
        """Test that unknown niche returns error."""
        analysis = analyze_hashtag_coverage(["#test"], "unknown-niche")

        assert "error" in analysis


# =============================================================================
# GET_FORMAT_SPECIFIC_HASHTAGS TESTS
# =============================================================================


class TestGetFormatSpecificHashtags:
    """Tests for get_format_specific_hashtags function."""

    def test_get_format_specific_hashtags_returns_list(self):
        """Test that get_format_specific_hashtags returns a list."""
        hashtags = get_format_specific_hashtags("scary-stories", "pov_horror")

        assert isinstance(hashtags, list)

    def test_get_format_specific_hashtags_pov_horror(self):
        """Test that POV horror format has specific hashtags."""
        hashtags = get_format_specific_hashtags("scary-stories", "pov_horror")

        assert len(hashtags) > 0
        assert "#pov" in hashtags or "#povhorror" in hashtags

    def test_get_format_specific_hashtags_unknown_format(self):
        """Test that unknown format returns empty list."""
        hashtags = get_format_specific_hashtags("scary-stories", "unknown_format")

        assert hashtags == []

    def test_get_format_specific_hashtags_unknown_niche(self):
        """Test that unknown niche returns empty list."""
        hashtags = get_format_specific_hashtags("unknown-niche", "pov_horror")

        assert hashtags == []

    @pytest.mark.parametrize(
        "niche,format_name",
        [
            ("scary-stories", "pov_horror"),
            ("scary-stories", "rules_of_location"),
            ("finance", "financial_red_flags_dating"),
            ("finance", "i_did_the_math"),
            ("luxury", "guess_the_price"),
            ("luxury", "cheap_vs_expensive"),
        ],
    )
    def test_format_specific_hashtags_start_with_hash(
        self, niche: str, format_name: str
    ):
        """Test that all format-specific hashtags start with #."""
        hashtags = get_format_specific_hashtags(niche, format_name)

        for tag in hashtags:
            assert tag.startswith("#"), f"Tag '{tag}' doesn't start with #"

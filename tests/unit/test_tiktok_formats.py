"""
Tests for the tiktok_formats module.
Tests TikTok-native content format definitions and utilities.
"""

import os
import sys

import pytest

# Add pipeline directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "pipeline"))

from tiktok_formats import (
    ALL_FORMATS,
    FINANCE_FORMATS,
    LUXURY_FORMATS,
    SCARY_FORMATS,
    TikTokFormat,
    format_to_prompt_guidance,
    get_all_formats_for_niche,
    get_format,
    get_format_names,
    get_random_format,
)

# =============================================================================
# FORMAT STRUCTURE TESTS
# =============================================================================


class TestFormatStructure:
    """Tests for TikTokFormat dataclass structure."""

    def test_tiktok_format_has_required_fields(self):
        """Test that TikTokFormat has all required fields."""
        format_obj = TikTokFormat(
            name="Test Format",
            description="A test format",
            structure=[{"element": "test"}],
            duration_range=(30, 60),
            visual_requirements={"layout": "standard"},
            why_it_works="Testing purposes",
            niche="scary-stories",
        )

        assert format_obj.name == "Test Format"
        assert format_obj.description == "A test format"
        assert len(format_obj.structure) > 0
        assert format_obj.duration_range == (30, 60)
        assert "layout" in format_obj.visual_requirements
        assert format_obj.why_it_works == "Testing purposes"
        assert format_obj.niche == "scary-stories"


# =============================================================================
# SCARY FORMATS TESTS
# =============================================================================


class TestScaryFormats:
    """Tests for scary story format definitions."""

    def test_scary_formats_exist(self):
        """Test that scary story formats are defined."""
        assert len(SCARY_FORMATS) > 0

    @pytest.mark.parametrize(
        "format_name",
        [
            "pov_horror",
            "green_screen_storytime",
            "ranking_viewer_stories",
            "split_screen_reaction",
            "rules_of_location",
            "creepy_text_messages",
        ],
    )
    def test_expected_scary_formats_exist(self, format_name: str):
        """Test that expected scary formats are defined."""
        assert format_name in SCARY_FORMATS

    def test_scary_formats_have_valid_duration_ranges(self):
        """Test that all scary formats have valid duration ranges."""
        for name, format_obj in SCARY_FORMATS.items():
            min_dur, max_dur = format_obj.duration_range
            assert min_dur > 0, f"{name} has invalid min duration"
            assert max_dur > min_dur, f"{name} has invalid max duration"
            assert max_dur <= 180, f"{name} exceeds reasonable TikTok length"

    def test_scary_formats_have_structures(self):
        """Test that all scary formats have structure definitions."""
        for name, format_obj in SCARY_FORMATS.items():
            assert len(format_obj.structure) > 0, f"{name} has no structure"

            # Each structure element should have an 'element' key
            for element in format_obj.structure:
                assert "element" in element, f"{name} structure missing 'element' key"


# =============================================================================
# FINANCE FORMATS TESTS
# =============================================================================


class TestFinanceFormats:
    """Tests for finance format definitions."""

    def test_finance_formats_exist(self):
        """Test that finance formats are defined."""
        assert len(FINANCE_FORMATS) > 0

    @pytest.mark.parametrize(
        "format_name",
        [
            "financial_red_flags_dating",
            "things_that_scream_broke",
            "roast_my_spending",
            "money_hot_takes",
            "what_x_gets_you",
            "i_did_the_math",
        ],
    )
    def test_expected_finance_formats_exist(self, format_name: str):
        """Test that expected finance formats are defined."""
        assert format_name in FINANCE_FORMATS

    def test_finance_formats_have_valid_duration_ranges(self):
        """Test that all finance formats have valid duration ranges."""
        for name, format_obj in FINANCE_FORMATS.items():
            min_dur, max_dur = format_obj.duration_range
            assert min_dur > 0, f"{name} has invalid min duration"
            assert max_dur >= min_dur, f"{name} has invalid max duration"


# =============================================================================
# LUXURY FORMATS TESTS
# =============================================================================


class TestLuxuryFormats:
    """Tests for luxury format definitions."""

    def test_luxury_formats_exist(self):
        """Test that luxury formats are defined."""
        assert len(LUXURY_FORMATS) > 0

    @pytest.mark.parametrize(
        "format_name",
        [
            "guess_the_price",
            "rich_people_secrets",
            "pov_afford_anything",
            "luxury_asmr",
            "cheap_vs_expensive",
            "billionaire_day_in_life",
        ],
    )
    def test_expected_luxury_formats_exist(self, format_name: str):
        """Test that expected luxury formats are defined."""
        assert format_name in LUXURY_FORMATS

    def test_luxury_formats_have_visual_requirements(self):
        """Test that all luxury formats have visual requirements."""
        for name, format_obj in LUXURY_FORMATS.items():
            assert (
                len(format_obj.visual_requirements) > 0
            ), f"{name} missing visual requirements"


# =============================================================================
# ALL_FORMATS REGISTRY TESTS
# =============================================================================


class TestAllFormatsRegistry:
    """Tests for the ALL_FORMATS registry."""

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_all_niches_in_registry(self, niche: str):
        """Test that all niches are in the registry."""
        assert niche in ALL_FORMATS

    def test_registry_has_correct_references(self):
        """Test that registry points to correct format dicts."""
        assert ALL_FORMATS["scary-stories"] is SCARY_FORMATS
        assert ALL_FORMATS["finance"] is FINANCE_FORMATS
        assert ALL_FORMATS["luxury"] is LUXURY_FORMATS


# =============================================================================
# GET_FORMAT TESTS
# =============================================================================


class TestGetFormat:
    """Tests for get_format function."""

    def test_get_format_returns_format(self):
        """Test that get_format returns a TikTokFormat."""
        format_obj = get_format("scary-stories", "pov_horror")

        assert format_obj is not None
        assert isinstance(format_obj, TikTokFormat)
        assert format_obj.name == "POV Horror"

    def test_get_format_returns_none_for_unknown_format(self):
        """Test that get_format returns None for unknown format."""
        format_obj = get_format("scary-stories", "nonexistent_format")

        assert format_obj is None

    def test_get_format_returns_none_for_unknown_niche(self):
        """Test that get_format returns None for unknown niche."""
        format_obj = get_format("unknown-niche", "pov_horror")

        assert format_obj is None


# =============================================================================
# GET_ALL_FORMATS_FOR_NICHE TESTS
# =============================================================================


class TestGetAllFormatsForNiche:
    """Tests for get_all_formats_for_niche function."""

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_get_all_formats_returns_dict(self, niche: str):
        """Test that get_all_formats_for_niche returns a dict."""
        formats = get_all_formats_for_niche(niche)

        assert isinstance(formats, dict)
        assert len(formats) > 0

    def test_get_all_formats_unknown_niche(self):
        """Test that unknown niche returns empty dict."""
        formats = get_all_formats_for_niche("unknown-niche")

        assert formats == {}


# =============================================================================
# GET_FORMAT_NAMES TESTS
# =============================================================================


class TestGetFormatNames:
    """Tests for get_format_names function."""

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_get_format_names_returns_list(self, niche: str):
        """Test that get_format_names returns a list of strings."""
        names = get_format_names(niche)

        assert isinstance(names, list)
        assert len(names) > 0
        assert all(isinstance(name, str) for name in names)

    def test_get_format_names_unknown_niche(self):
        """Test that unknown niche returns empty list."""
        names = get_format_names("unknown-niche")

        assert names == []


# =============================================================================
# GET_RANDOM_FORMAT TESTS
# =============================================================================


class TestGetRandomFormat:
    """Tests for get_random_format function."""

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_get_random_format_returns_format(self, niche: str):
        """Test that get_random_format returns a TikTokFormat."""
        format_obj = get_random_format(niche)

        assert format_obj is not None
        assert isinstance(format_obj, TikTokFormat)
        assert format_obj.niche == niche

    def test_get_random_format_unknown_niche(self):
        """Test that unknown niche returns None."""
        format_obj = get_random_format("unknown-niche")

        assert format_obj is None

    def test_get_random_format_variety(self):
        """Test that random selection provides variety."""
        # Get 10 random formats and check we don't always get the same one
        formats = [get_random_format("scary-stories") for _ in range(10)]
        unique_names = {f.name for f in formats}

        # With 6 formats and 10 selections, we should see at least 2 different ones
        assert len(unique_names) >= 2


# =============================================================================
# FORMAT_TO_PROMPT_GUIDANCE TESTS
# =============================================================================


class TestFormatToPromptGuidance:
    """Tests for format_to_prompt_guidance function."""

    def test_format_to_prompt_guidance_returns_string(self):
        """Test that format_to_prompt_guidance returns a string."""
        format_obj = get_format("scary-stories", "pov_horror")
        guidance = format_to_prompt_guidance(format_obj)

        assert isinstance(guidance, str)
        assert len(guidance) > 0

    def test_format_to_prompt_guidance_contains_format_info(self):
        """Test that guidance contains format information."""
        format_obj = get_format("scary-stories", "pov_horror")
        guidance = format_to_prompt_guidance(format_obj)

        assert "FORMAT:" in guidance
        assert "POV Horror" in guidance
        assert "DESCRIPTION:" in guidance
        assert "DURATION:" in guidance
        assert "STRUCTURE:" in guidance
        assert "WHY IT WORKS:" in guidance

    def test_format_to_prompt_guidance_includes_duration(self):
        """Test that guidance includes duration range."""
        format_obj = get_format("luxury", "guess_the_price")
        guidance = format_to_prompt_guidance(format_obj)

        # Check that duration numbers appear
        min_dur, max_dur = format_obj.duration_range
        assert str(min_dur) in guidance
        assert str(max_dur) in guidance

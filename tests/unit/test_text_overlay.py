"""
Tests for the text_overlay module.
Tests text overlay generation and FFmpeg filter creation.
"""

import pytest

from faceless.core.text_overlay import (
    PRESET_STYLES,
    TextAnimation,
    TextOverlay,
    TextPosition,
    TextStyle,
    create_countdown_overlays,
    create_cta_overlay,
    create_hook_overlay,
    create_mid_video_overlay,
    create_pov_overlay,
    generate_overlay_filter_chain,
    overlay_to_ffmpeg_filter,
    position_to_xy,
)

# =============================================================================
# ENUMS AND DATACLASS TESTS
# =============================================================================


class TestEnums:
    """Tests for enum definitions."""

    def test_text_position_values(self):
        """Test that all position values exist."""
        positions = [
            TextPosition.TOP_LEFT,
            TextPosition.TOP_CENTER,
            TextPosition.TOP_RIGHT,
            TextPosition.CENTER_LEFT,
            TextPosition.CENTER,
            TextPosition.CENTER_RIGHT,
            TextPosition.BOTTOM_LEFT,
            TextPosition.BOTTOM_CENTER,
            TextPosition.BOTTOM_RIGHT,
        ]
        assert len(positions) == 9

    def test_text_animation_values(self):
        """Test that all animation values exist."""
        animations = [
            TextAnimation.NONE,
            TextAnimation.FADE_IN,
            TextAnimation.FADE_OUT,
            TextAnimation.FADE_IN_OUT,
            TextAnimation.TYPEWRITER,
            TextAnimation.SCALE_IN,
            TextAnimation.SLIDE_UP,
            TextAnimation.SLIDE_DOWN,
        ]
        assert len(animations) == 8


class TestTextStyle:
    """Tests for TextStyle dataclass."""

    def test_default_style(self):
        """Test default TextStyle values."""
        style = TextStyle()

        assert style.font_size == 48
        assert style.font_color == "white"
        assert style.bold is True
        assert style.outline_width == 3

    def test_custom_style(self):
        """Test custom TextStyle creation."""
        style = TextStyle(
            font_size=72,
            font_color="#FF0000",
            bold=False,
        )

        assert style.font_size == 72
        assert style.font_color == "#FF0000"
        assert style.bold is False


class TestTextOverlay:
    """Tests for TextOverlay dataclass."""

    def test_default_overlay(self):
        """Test default TextOverlay values."""
        overlay = TextOverlay(text="Test")

        assert overlay.text == "Test"
        assert overlay.position == TextPosition.CENTER
        assert overlay.start_time == 0.0
        assert overlay.end_time == 3.0

    def test_custom_overlay(self):
        """Test custom TextOverlay creation."""
        overlay = TextOverlay(
            text="Custom Text",
            position=TextPosition.TOP_CENTER,
            start_time=5.0,
            end_time=10.0,
            animation=TextAnimation.SLIDE_UP,
        )

        assert overlay.text == "Custom Text"
        assert overlay.position == TextPosition.TOP_CENTER
        assert overlay.start_time == 5.0
        assert overlay.end_time == 10.0
        assert overlay.animation == TextAnimation.SLIDE_UP


# =============================================================================
# PRESET STYLES TESTS
# =============================================================================


class TestPresetStyles:
    """Tests for preset style definitions."""

    @pytest.mark.parametrize(
        "style_name",
        [
            "hook_primary",
            "hook_secondary",
            "cta",
            "countdown",
            "subtle",
            "scary",
            "finance",
            "luxury",
        ],
    )
    def test_preset_style_exists(self, style_name: str):
        """Test that all expected preset styles exist."""
        assert style_name in PRESET_STYLES
        assert isinstance(PRESET_STYLES[style_name], TextStyle)

    def test_scary_style_has_red(self):
        """Test that scary style uses appropriate color."""
        style = PRESET_STYLES["scary"]
        # Should have red-ish color
        assert "CC0000" in style.font_color or "red" in style.font_color.lower()

    def test_finance_style_has_green(self):
        """Test that finance style uses money green."""
        style = PRESET_STYLES["finance"]
        assert "CC00" in style.font_color or "green" in style.font_color.lower()


# =============================================================================
# OVERLAY CREATION FUNCTIONS TESTS
# =============================================================================


class TestCreateHookOverlay:
    """Tests for create_hook_overlay function."""

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_creates_overlay_for_all_niches(self, niche: str):
        """Test hook overlay creation for all niches."""
        overlay = create_hook_overlay("Test hook", niche)

        assert isinstance(overlay, TextOverlay)
        assert overlay.text == "Test hook"
        assert overlay.start_time == 0.0

    def test_custom_duration(self):
        """Test custom duration setting."""
        overlay = create_hook_overlay("Test", "scary-stories", duration=5.0)

        assert overlay.end_time == 5.0

    def test_custom_position(self):
        """Test custom position setting."""
        overlay = create_hook_overlay(
            "Test", "finance", position=TextPosition.TOP_CENTER
        )

        assert overlay.position == TextPosition.TOP_CENTER


class TestCreateMidVideoOverlay:
    """Tests for create_mid_video_overlay function."""

    def test_creates_overlay(self):
        """Test mid-video overlay creation."""
        overlay = create_mid_video_overlay("WAIT FOR IT", 15.0)

        assert overlay.text == "WAIT FOR IT"
        assert overlay.start_time == 15.0
        assert overlay.end_time == 17.0  # 15 + 2 default duration

    def test_custom_duration(self):
        """Test custom duration."""
        overlay = create_mid_video_overlay("Keep watching", 20.0, duration=3.0)

        assert overlay.end_time == 23.0


class TestCreateCtaOverlay:
    """Tests for create_cta_overlay function."""

    def test_creates_overlay(self):
        """Test CTA overlay creation."""
        overlay = create_cta_overlay("Follow for more!", 60.0)

        assert overlay.text == "Follow for more!"
        assert overlay.start_time == 56.0  # 60 - 4 default display duration
        assert overlay.end_time == 60.0

    def test_short_video(self):
        """Test CTA on short video."""
        overlay = create_cta_overlay("Subscribe!", 10.0, display_duration=5.0)

        assert overlay.start_time == 5.0  # 10 - 5
        assert overlay.end_time == 10.0


class TestCreateCountdownOverlays:
    """Tests for create_countdown_overlays function."""

    def test_creates_countdown(self):
        """Test countdown overlay creation."""
        overlays = create_countdown_overlays(10.0)

        assert len(overlays) == 3  # 3, 2, 1
        assert overlays[0].text == "3"
        assert overlays[1].text == "2"
        assert overlays[2].text == "1"

    def test_timing(self):
        """Test countdown timing."""
        overlays = create_countdown_overlays(10.0, count_from=3)

        assert overlays[0].start_time == 10.0
        assert overlays[1].start_time == 11.0
        assert overlays[2].start_time == 12.0

    def test_custom_count(self):
        """Test custom count from value."""
        overlays = create_countdown_overlays(5.0, count_from=5)

        assert len(overlays) == 5
        assert overlays[0].text == "5"


class TestCreatePovOverlay:
    """Tests for create_pov_overlay function."""

    def test_creates_pov_overlay(self):
        """Test POV overlay creation."""
        overlay = create_pov_overlay("You hear a noise")

        assert "POV:" in overlay.text
        assert "You hear a noise" in overlay.text
        assert overlay.position == TextPosition.TOP_CENTER


# =============================================================================
# FFMPEG FILTER TESTS
# =============================================================================


class TestPositionToXy:
    """Tests for position_to_xy function."""

    def test_all_positions_have_mapping(self):
        """Test that all positions have x,y mappings."""
        for position in TextPosition:
            x, y = position_to_xy(position)
            assert isinstance(x, str)
            assert isinstance(y, str)

    def test_center_position(self):
        """Test center position calculation."""
        x, y = position_to_xy(TextPosition.CENTER)

        assert "w-text_w" in x  # Width centering
        assert "h-text_h" in y  # Height centering


class TestOverlayToFfmpegFilter:
    """Tests for overlay_to_ffmpeg_filter function."""

    def test_generates_filter_string(self):
        """Test FFmpeg filter string generation."""
        overlay = TextOverlay(text="Test", start_time=0, end_time=3)
        filter_str = overlay_to_ffmpeg_filter(overlay)

        assert "drawtext=" in filter_str
        assert "text='Test'" in filter_str
        assert "enable=" in filter_str

    def test_escapes_special_characters(self):
        """Test that special characters are escaped."""
        overlay = TextOverlay(text="What's up?", start_time=0, end_time=3)
        filter_str = overlay_to_ffmpeg_filter(overlay)

        # Apostrophe should be escaped
        assert "What" in filter_str

    def test_includes_timing(self):
        """Test that timing is included."""
        overlay = TextOverlay(text="Test", start_time=5.0, end_time=10.0)
        filter_str = overlay_to_ffmpeg_filter(overlay)

        assert "5" in filter_str
        assert "10" in filter_str


class TestGenerateOverlayFilterChain:
    """Tests for generate_overlay_filter_chain function."""

    def test_empty_list(self):
        """Test with empty overlay list."""
        result = generate_overlay_filter_chain([])
        assert result == ""

    def test_single_overlay(self):
        """Test with single overlay."""
        overlays = [TextOverlay(text="Test")]
        result = generate_overlay_filter_chain(overlays)

        assert "drawtext=" in result

    def test_multiple_overlays(self):
        """Test with multiple overlays."""
        overlays = [
            TextOverlay(text="First", layer=1),
            TextOverlay(text="Second", layer=2),
        ]
        result = generate_overlay_filter_chain(overlays)

        assert "First" in result
        assert "Second" in result
        assert "," in result  # Should be comma-separated

"""
Tests for the hooks module.
Tests first-frame hooks, pattern interrupts, mid-video retention, and comment bait.
"""

import pytest

from faceless.core.hooks import (
    COMMENT_TRIGGERS,
    FIRST_FRAME_HOOKS,
    LOOP_STRUCTURES,
    MID_VIDEO_HOOKS,
    PATTERN_INTERRUPTS,
    PINNED_COMMENTS,
    generate_engagement_package,
    get_comment_trigger,
    get_first_frame_hook,
    get_loop_structure,
    get_mid_video_hook,
    get_pattern_interrupt,
    get_pinned_comment,
)

# =============================================================================
# FIRST FRAME HOOK TESTS
# =============================================================================


class TestFirstFrameHooks:
    """Tests for first-frame hook generation."""

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_get_first_frame_hook_returns_valid_structure(self, niche: str):
        """Test that get_first_frame_hook returns proper structure."""
        hook = get_first_frame_hook(niche)

        assert "text" in hook
        assert "type" in hook
        assert "niche" in hook
        assert "display_duration" in hook
        assert "position" in hook

        assert isinstance(hook["text"], str)
        assert len(hook["text"]) > 0
        assert hook["niche"] == niche

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_first_frame_hooks_exist_for_all_niches(self, niche: str):
        """Test that hook templates exist for all niches."""
        assert niche in FIRST_FRAME_HOOKS
        hooks = FIRST_FRAME_HOOKS[niche]

        assert "text_question" in hooks
        assert "shocking_statement" in hooks
        assert "number_promise" in hooks
        assert "direct_address" in hooks

        for hook_type, hook_list in hooks.items():
            assert len(hook_list) > 0, f"No hooks for {niche}/{hook_type}"

    def test_get_first_frame_hook_with_specific_type(self):
        """Test requesting specific hook type."""
        hook = get_first_frame_hook("scary-stories", hook_type="text_question")

        assert hook["type"] == "text_question"
        assert "?" in hook["text"]  # Questions should have question marks

    def test_get_first_frame_hook_fallback_niche(self):
        """Test that unknown niche falls back gracefully."""
        hook = get_first_frame_hook("unknown-niche")

        assert hook is not None
        assert "text" in hook

    def test_first_frame_hook_display_duration(self):
        """Test that display duration is reasonable."""
        hook = get_first_frame_hook("scary-stories")

        assert 1.0 <= hook["display_duration"] <= 5.0


# =============================================================================
# PATTERN INTERRUPT TESTS
# =============================================================================


class TestPatternInterrupts:
    """Tests for pattern interrupt generation."""

    def test_pattern_interrupts_have_audio_and_visual(self):
        """Test that both audio and visual interrupts exist."""
        assert "audio" in PATTERN_INTERRUPTS
        assert "visual" in PATTERN_INTERRUPTS

        assert len(PATTERN_INTERRUPTS["audio"]) > 0
        assert len(PATTERN_INTERRUPTS["visual"]) > 0

    @pytest.mark.parametrize("interrupt_type", ["audio", "visual"])
    def test_get_pattern_interrupt_returns_valid_structure(self, interrupt_type: str):
        """Test that get_pattern_interrupt returns proper structure."""
        interrupt = get_pattern_interrupt(interrupt_type)

        assert "type" in interrupt
        assert "technique" in interrupt
        assert "duration" in interrupt

        assert interrupt["type"] == interrupt_type
        assert interrupt["duration"] > 0

    def test_get_pattern_interrupt_random_selection(self):
        """Test that random selection works when no type specified."""
        interrupt = get_pattern_interrupt()

        assert interrupt["type"] in ["audio", "visual"]


# =============================================================================
# MID-VIDEO HOOK TESTS
# =============================================================================


class TestMidVideoHooks:
    """Tests for mid-video retention hook generation."""

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_mid_video_verbal_hooks_exist(self, niche: str):
        """Test that verbal hooks exist for all niches."""
        assert niche in MID_VIDEO_HOOKS["verbal"]
        assert len(MID_VIDEO_HOOKS["verbal"][niche]) > 0

    def test_mid_video_text_overlays_exist(self):
        """Test that text overlay options exist."""
        assert len(MID_VIDEO_HOOKS["text_overlay"]) > 0

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_get_mid_video_hook_returns_valid_structure(self, niche: str):
        """Test that get_mid_video_hook returns proper structure."""
        hook = get_mid_video_hook(niche)

        assert "format" in hook
        assert "content" in hook
        assert "insert_at_percent" in hook

    def test_mid_video_hook_insert_position(self):
        """Test that insertion position is in the 30-50% range."""
        for _ in range(10):  # Test multiple times due to randomness
            hook = get_mid_video_hook("scary-stories")
            assert 30 <= hook["insert_at_percent"] <= 50

    @pytest.mark.parametrize("hook_format", ["verbal", "text_overlay"])
    def test_get_mid_video_hook_with_specific_format(self, hook_format: str):
        """Test requesting specific hook format."""
        hook = get_mid_video_hook("finance", hook_format=hook_format)

        assert hook["format"] == hook_format


# =============================================================================
# COMMENT TRIGGER TESTS
# =============================================================================


class TestCommentTriggers:
    """Tests for comment-triggering content generation."""

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_controversial_endings_exist(self, niche: str):
        """Test that controversial endings exist for all niches."""
        assert niche in COMMENT_TRIGGERS["controversial_endings"]
        assert len(COMMENT_TRIGGERS["controversial_endings"][niche]) > 0

    def test_opinion_requests_exist(self):
        """Test that opinion request templates exist."""
        assert len(COMMENT_TRIGGERS["opinion_requests"]) > 0

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_fill_in_blank_exist(self, niche: str):
        """Test that fill-in-blank templates exist for all niches."""
        assert niche in COMMENT_TRIGGERS["fill_in_blank"]
        templates = COMMENT_TRIGGERS["fill_in_blank"][niche]
        assert len(templates) > 0

        # Each template should have a blank
        for template in templates:
            assert "____" in template

    def test_part_2_bait_exists(self):
        """Test that part 2 bait templates exist."""
        assert len(COMMENT_TRIGGERS["part_2_bait"]) > 0

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_get_comment_trigger_returns_valid_structure(self, niche: str):
        """Test that get_comment_trigger returns proper structure."""
        trigger = get_comment_trigger(niche)

        assert "type" in trigger
        assert "content" in trigger
        assert "niche" in trigger

        assert isinstance(trigger["content"], str)
        assert len(trigger["content"]) > 0

    @pytest.mark.parametrize(
        "trigger_type",
        [
            "controversial_endings",
            "opinion_requests",
            "fill_in_blank",
            "part_2_bait",
        ],
    )
    def test_get_comment_trigger_with_specific_type(self, trigger_type: str):
        """Test requesting specific trigger type."""
        trigger = get_comment_trigger("scary-stories", trigger_type=trigger_type)

        assert trigger["type"] == trigger_type


# =============================================================================
# PINNED COMMENT TESTS
# =============================================================================


class TestPinnedComments:
    """Tests for pinned comment generation."""

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_pinned_comments_exist(self, niche: str):
        """Test that pinned comments exist for all niches."""
        assert niche in PINNED_COMMENTS
        assert len(PINNED_COMMENTS[niche]) > 0

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_get_pinned_comment_returns_string(self, niche: str):
        """Test that get_pinned_comment returns a non-empty string."""
        comment = get_pinned_comment(niche)

        assert isinstance(comment, str)
        assert len(comment) > 0


# =============================================================================
# LOOP STRUCTURE TESTS
# =============================================================================


class TestLoopStructures:
    """Tests for loop structure guidance."""

    def test_loop_structures_exist(self):
        """Test that all loop structure types exist."""
        expected_types = [
            "audio_loop",
            "visual_loop",
            "narrative_loop",
            "question_loop",
        ]

        for loop_type in expected_types:
            assert loop_type in LOOP_STRUCTURES

    def test_loop_structures_have_descriptions(self):
        """Test that all loop structures have descriptions."""
        for _loop_type, structure in LOOP_STRUCTURES.items():
            assert "description" in structure
            assert len(structure["description"]) > 0

    @pytest.mark.parametrize(
        "loop_type", ["audio_loop", "visual_loop", "narrative_loop", "question_loop"]
    )
    def test_get_loop_structure_returns_valid(self, loop_type: str):
        """Test that get_loop_structure returns proper structure."""
        structure = get_loop_structure(loop_type)

        assert "type" in structure
        assert "description" in structure
        assert structure["type"] == loop_type

    def test_get_loop_structure_random_selection(self):
        """Test that random selection works when no type specified."""
        structure = get_loop_structure()

        assert "type" in structure
        assert structure["type"] in LOOP_STRUCTURES


# =============================================================================
# ENGAGEMENT PACKAGE TESTS
# =============================================================================


class TestEngagementPackage:
    """Tests for complete engagement package generation."""

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_generate_engagement_package_structure(self, niche: str):
        """Test that engagement package has all required components."""
        package = generate_engagement_package(niche)

        assert "first_frame_hook" in package
        assert "pattern_interrupt" in package
        assert "mid_video_hook" in package
        assert "comment_trigger" in package
        assert "pinned_comment" in package
        assert "loop_structure" in package

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_engagement_package_components_valid(self, niche: str):
        """Test that each component in package is valid."""
        package = generate_engagement_package(niche)

        # First frame hook
        assert "text" in package["first_frame_hook"]
        assert "type" in package["first_frame_hook"]

        # Pattern interrupt
        assert "technique" in package["pattern_interrupt"]

        # Mid video hook
        assert "content" in package["mid_video_hook"]

        # Comment trigger
        assert "content" in package["comment_trigger"]

        # Pinned comment
        assert isinstance(package["pinned_comment"], str)

        # Loop structure
        assert "type" in package["loop_structure"]

    def test_engagement_package_deterministic_components(self):
        """Test that packages for same niche have consistent structure."""
        packages = [generate_engagement_package("scary-stories") for _ in range(5)]

        for package in packages:
            assert package["first_frame_hook"]["niche"] == "scary-stories"

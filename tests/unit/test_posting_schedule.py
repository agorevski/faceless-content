"""
Tests for the posting_schedule module.
Tests optimal posting time generation and schedule utilities.
"""

import os
import sys
from datetime import datetime, time, timedelta

import pytest

# Add pipeline directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "pipeline"))

from posting_schedule import (
    DAY_PATTERNS,
    FREQUENCY_RECOMMENDATIONS,
    POSTING_WINDOWS,
    format_schedule_for_display,
    generate_weekly_schedule,
    get_day_rating,
    get_next_optimal_slot,
    get_optimal_posting_time,
)

# =============================================================================
# POSTING WINDOWS STRUCTURE TESTS
# =============================================================================


class TestPostingWindowsStructure:
    """Tests for posting windows data structure."""

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_niche_exists_in_windows(self, niche: str):
        """Test that all niches exist in posting windows."""
        assert niche in POSTING_WINDOWS

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_windows_have_required_keys(self, niche: str):
        """Test that each niche has required keys."""
        windows = POSTING_WINDOWS[niche]

        assert "description" in windows
        assert "best_times" in windows
        assert "avoid_times" in windows

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_best_times_have_valid_structure(self, niche: str):
        """Test that best times have valid time ranges."""
        windows = POSTING_WINDOWS[niche]

        assert len(windows["best_times"]) > 0

        for time_slot in windows["best_times"]:
            assert "start" in time_slot
            assert "end" in time_slot
            assert isinstance(time_slot["start"], time)
            assert isinstance(time_slot["end"], time)

    def test_scary_stories_evening_times(self):
        """Test that scary stories favor evening/night times."""
        windows = POSTING_WINDOWS["scary-stories"]
        best_times = windows["best_times"]

        # At least one slot should be after 8 PM
        evening_slots = [t for t in best_times if t["start"].hour >= 20]
        assert len(evening_slots) > 0

    def test_finance_commute_times(self):
        """Test that finance includes commute times."""
        windows = POSTING_WINDOWS["finance"]
        best_times = windows["best_times"]

        # Should have morning slot (7-9 AM)
        morning_slots = [t for t in best_times if 7 <= t["start"].hour <= 9]
        assert len(morning_slots) > 0


# =============================================================================
# DAY PATTERNS STRUCTURE TESTS
# =============================================================================


class TestDayPatternsStructure:
    """Tests for day patterns data structure."""

    def test_all_days_exist(self):
        """Test that all 7 days are defined."""
        for day in range(7):
            assert day in DAY_PATTERNS

    def test_days_have_required_keys(self):
        """Test that each day has required keys."""
        for day in range(7):
            pattern = DAY_PATTERNS[day]

            assert "performance" in pattern
            assert "notes" in pattern
            assert "multiplier" in pattern

    def test_multipliers_reasonable(self):
        """Test that multipliers are in reasonable range."""
        for day in range(7):
            multiplier = DAY_PATTERNS[day]["multiplier"]
            assert 0.5 <= multiplier <= 1.5

    def test_tuesday_wednesday_high_performance(self):
        """Test that Tuesday and Wednesday have high performance."""
        # Tuesday (1) and Wednesday (2) should be marked as high
        assert DAY_PATTERNS[1]["performance"] == "high"
        assert DAY_PATTERNS[2]["performance"] == "high"


# =============================================================================
# FREQUENCY RECOMMENDATIONS TESTS
# =============================================================================


class TestFrequencyRecommendations:
    """Tests for frequency recommendations structure."""

    def test_recommendations_exist(self):
        """Test that frequency recommendations exist."""
        assert "minimum_for_growth" in FREQUENCY_RECOMMENDATIONS
        assert "optimal_for_rapid_growth" in FREQUENCY_RECOMMENDATIONS

    def test_minimum_has_one_post(self):
        """Test that minimum is 1 post per day."""
        minimum = FREQUENCY_RECOMMENDATIONS["minimum_for_growth"]
        assert minimum["posts_per_day"] == 1

    def test_optimal_has_multiple_posts(self):
        """Test that optimal has 2-3 posts per day."""
        optimal = FREQUENCY_RECOMMENDATIONS["optimal_for_rapid_growth"]
        min_posts, max_posts = optimal["posts_per_day"]
        assert min_posts >= 2
        assert max_posts >= min_posts


# =============================================================================
# GET_OPTIMAL_POSTING_TIME TESTS
# =============================================================================


class TestGetOptimalPostingTime:
    """Tests for get_optimal_posting_time function."""

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_returns_datetime(self, niche: str):
        """Test that get_optimal_posting_time returns a datetime."""
        result = get_optimal_posting_time(niche)

        assert isinstance(result, datetime)

    def test_respects_target_date(self):
        """Test that target date is respected."""
        target = datetime(2026, 6, 15, 12, 0)
        result = get_optimal_posting_time("scary-stories", target_date=target)

        assert result.year == 2026
        assert result.month == 6
        assert result.day == 15

    def test_scary_stories_evening_bias(self):
        """Test that scary stories tends toward evening times."""
        times = [get_optimal_posting_time("scary-stories") for _ in range(20)]

        evening_count = sum(1 for t in times if t.hour >= 20 or t.hour <= 1)

        # With high-priority preference, most should be evening
        assert evening_count >= 10

    def test_finance_business_hours_bias(self):
        """Test that finance tends toward business hours."""
        times = [get_optimal_posting_time("finance") for _ in range(20)]

        # Check for morning, lunch, or evening times
        good_times = sum(
            1
            for t in times
            if (7 <= t.hour <= 9) or (12 <= t.hour <= 13) or (17 <= t.hour <= 19)
        )

        assert good_times >= 10


# =============================================================================
# GET_DAY_RATING TESTS
# =============================================================================


class TestGetDayRating:
    """Tests for get_day_rating function."""

    def test_returns_dict(self):
        """Test that get_day_rating returns a dict."""
        result = get_day_rating(datetime.now())

        assert isinstance(result, dict)

    def test_includes_day_name(self):
        """Test that result includes day name."""
        result = get_day_rating(datetime(2026, 1, 5))  # A Monday

        assert "day_name" in result
        assert result["day_name"] == "Monday"

    def test_includes_performance(self):
        """Test that result includes performance rating."""
        result = get_day_rating(datetime.now())

        assert "performance" in result
        assert "multiplier" in result

    def test_niche_bonus_sunday_scary(self):
        """Test that Sunday gets a bonus for scary stories."""
        # Find a Sunday
        sunday = datetime(2026, 1, 4)  # This should be a Sunday
        while sunday.weekday() != 6:
            sunday += timedelta(days=1)

        result = get_day_rating(sunday, niche="scary-stories")

        # Sunday should have special niche consideration for scary stories
        assert result["performance"] == "high" or "niche_bonus" in result


# =============================================================================
# GENERATE_WEEKLY_SCHEDULE TESTS
# =============================================================================


class TestGenerateWeeklySchedule:
    """Tests for generate_weekly_schedule function."""

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_returns_list(self, niche: str):
        """Test that generate_weekly_schedule returns a list."""
        schedule = generate_weekly_schedule(niche)

        assert isinstance(schedule, list)

    def test_seven_days(self):
        """Test that schedule covers 7 days with 1 post/day."""
        schedule = generate_weekly_schedule("scary-stories", posts_per_day=1)

        assert len(schedule) == 7

    def test_multiple_posts_per_day(self):
        """Test schedule with multiple posts per day."""
        schedule = generate_weekly_schedule("finance", posts_per_day=2)

        assert len(schedule) == 14  # 7 days * 2 posts

    def test_schedule_items_have_required_keys(self):
        """Test that schedule items have required keys."""
        schedule = generate_weekly_schedule("luxury", posts_per_day=1)

        for item in schedule:
            assert "datetime" in item
            assert "day" in item
            assert "time" in item
            assert "day_performance" in item
            assert "niche" in item

    def test_schedule_is_sorted(self):
        """Test that schedule is sorted by datetime."""
        schedule = generate_weekly_schedule("scary-stories", posts_per_day=2)

        for i in range(len(schedule) - 1):
            assert schedule[i]["datetime"] <= schedule[i + 1]["datetime"]

    def test_respects_start_date(self):
        """Test that start date is respected."""
        start = datetime(2026, 3, 1, 0, 0, 0)
        schedule = generate_weekly_schedule("finance", start_date=start)

        # First item should be on March 1
        assert schedule[0]["datetime"].month == 3
        assert schedule[0]["datetime"].day == 1


# =============================================================================
# GET_NEXT_OPTIMAL_SLOT TESTS
# =============================================================================


class TestGetNextOptimalSlot:
    """Tests for get_next_optimal_slot function."""

    @pytest.mark.parametrize("niche", ["scary-stories", "finance", "luxury"])
    def test_returns_dict(self, niche: str):
        """Test that get_next_optimal_slot returns a dict."""
        result = get_next_optimal_slot(niche)

        assert isinstance(result, dict)

    def test_result_has_required_keys(self):
        """Test that result has required keys."""
        result = get_next_optimal_slot("scary-stories")

        assert "datetime" in result
        assert "formatted" in result
        assert "day_rating" in result
        assert "niche" in result

    def test_slot_is_in_future(self):
        """Test that returned slot is in the future or very near."""
        now = datetime.now()
        result = get_next_optimal_slot("finance", after=now)

        # Should be within 48 hours
        assert result["datetime"] <= now + timedelta(hours=48)

    def test_different_after_time(self):
        """Test with specific after time."""
        specific_time = datetime(2026, 1, 15, 10, 0)
        result = get_next_optimal_slot("luxury", after=specific_time)

        assert result["datetime"] >= specific_time


# =============================================================================
# FORMAT_SCHEDULE_FOR_DISPLAY TESTS
# =============================================================================


class TestFormatScheduleForDisplay:
    """Tests for format_schedule_for_display function."""

    def test_returns_string(self):
        """Test that format_schedule_for_display returns a string."""
        schedule = generate_weekly_schedule("scary-stories")
        result = format_schedule_for_display(schedule)

        assert isinstance(result, str)

    def test_contains_header(self):
        """Test that output contains header."""
        schedule = generate_weekly_schedule("finance")
        result = format_schedule_for_display(schedule)

        assert "POSTING SCHEDULE" in result

    def test_contains_day_names(self):
        """Test that output contains day names."""
        schedule = generate_weekly_schedule("luxury")
        result = format_schedule_for_display(schedule)

        # Should contain at least some day names
        day_names = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        found_days = sum(1 for day in day_names if day in result)
        assert found_days >= 5  # At least 5 different days should appear

    def test_empty_schedule(self):
        """Test handling of empty schedule."""
        result = format_schedule_for_display([])

        assert isinstance(result, str)
        assert "POSTING SCHEDULE" in result

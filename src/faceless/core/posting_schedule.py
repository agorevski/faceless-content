"""
Posting Schedule Module



Implements optimal posting time strategies from FUTURE_IMPROVEMENTS.md
Provides niche-specific timing recommendations for maximum reach
"""

import random
from datetime import datetime, time, timedelta

from faceless.utils.logging import get_logger

logger = get_logger(__name__)

# =============================================================================
# OPTIMAL POSTING WINDOWS BY NICHE
# =============================================================================

POSTING_WINDOWS = {
    "scary-stories": {
        "description": "Dark content performs better at night; viewers in bed scrolling",
        "best_times": [
            {
                "start": time(21, 0),
                "end": time(23, 59),
                "priority": "high",
            },  # 9PM - midnight
            {
                "start": time(0, 0),
                "end": time(1, 0),
                "priority": "high",
            },  # midnight - 1AM
            {
                "start": time(20, 0),
                "end": time(21, 0),
                "priority": "medium",
            },  # 8PM - 9PM
        ],
        "avoid_times": [
            {"start": time(6, 0), "end": time(11, 0)},  # Morning
            {"start": time(14, 0), "end": time(17, 0)},  # Afternoon
        ],
    },
    "finance": {
        "description": "Morning commute, lunch break, post-work when thinking about money",
        "best_times": [
            {
                "start": time(7, 0),
                "end": time(9, 0),
                "priority": "high",
            },  # Morning commute
            {
                "start": time(12, 0),
                "end": time(13, 0),
                "priority": "high",
            },  # Lunch break
            {"start": time(17, 0), "end": time(19, 0), "priority": "high"},  # Post-work
            {"start": time(20, 0), "end": time(21, 0), "priority": "medium"},  # Evening
        ],
        "avoid_times": [
            {"start": time(0, 0), "end": time(6, 0)},  # Late night
            {"start": time(22, 0), "end": time(23, 59)},  # Late evening
        ],
    },
    "luxury": {
        "description": "Aspirational content during breaks and evening relaxation",
        "best_times": [
            {
                "start": time(11, 0),
                "end": time(14, 0),
                "priority": "high",
            },  # Late morning/lunch
            {
                "start": time(19, 0),
                "end": time(21, 0),
                "priority": "high",
            },  # Evening relaxation
            {
                "start": time(15, 0),
                "end": time(17, 0),
                "priority": "medium",
            },  # Afternoon
        ],
        "avoid_times": [
            {"start": time(5, 0), "end": time(8, 0)},  # Early morning
        ],
    },
}


# =============================================================================
# DAY OF WEEK PATTERNS
# =============================================================================

DAY_PATTERNS = {
    0: {  # Monday
        "performance": "medium",
        "notes": "People catching up, less scroll time",
        "multiplier": 0.85,
    },
    1: {  # Tuesday
        "performance": "high",
        "notes": "Optimal engagement, settled into week",
        "multiplier": 1.1,
    },
    2: {  # Wednesday
        "performance": "high",
        "notes": "Peak mid-week engagement",
        "multiplier": 1.15,
    },
    3: {  # Thursday
        "performance": "high",
        "notes": "Building to weekend, high scroll time",
        "multiplier": 1.1,
    },
    4: {  # Friday
        "performance": "medium-high",
        "notes": "Evening posts perform well",
        "multiplier": 1.0,
    },
    5: {  # Saturday
        "performance": "variable",
        "notes": "Morning and late night best",
        "multiplier": 0.9,
        "special_times": [
            {"start": time(9, 0), "end": time(11, 0)},
            {"start": time(22, 0), "end": time(23, 59)},
        ],
    },
    6: {  # Sunday
        "performance": "high",
        "notes": "'Sunday Scaries' great for scary/finance content",
        "multiplier": 1.05,
        "special_niches": ["scary-stories", "finance"],
    },
}


# =============================================================================
# POSTING FREQUENCY RECOMMENDATIONS
# =============================================================================

FREQUENCY_RECOMMENDATIONS = {
    "minimum_for_growth": {
        "posts_per_day": 1,
        "timing": "same hour daily for consistency",
        "notes": "Minimum viable posting schedule",
    },
    "optimal_for_rapid_growth": {
        "posts_per_day": (2, 3),
        "spacing_hours": (4, 6),
        "timing": "spaced throughout the day",
        "notes": "Varied content types within niche recommended",
    },
    "aggressive_growth": {
        "posts_per_day": (3, 5),
        "spacing_hours": (3, 4),
        "notes": "Only if content quality can be maintained",
    },
}


# =============================================================================
# SCHEDULE GENERATION FUNCTIONS
# =============================================================================


def get_optimal_posting_time(
    niche: str,
    target_date: datetime = None,
    prefer_high_priority: bool = True,
) -> datetime:
    """
    Get the optimal posting time for a niche.

    Args:
        niche: One of "scary-stories", "finance", "luxury"
        target_date: Date to schedule for (defaults to today)
        prefer_high_priority: Whether to prefer high-priority time slots

    Returns:
        datetime with optimal posting time
    """
    if target_date is None:
        target_date = datetime.now()

    if niche not in POSTING_WINDOWS:
        niche = "scary-stories"

    windows = POSTING_WINDOWS[niche]["best_times"]

    if prefer_high_priority:
        high_priority = [w for w in windows if w.get("priority") == "high"]
        if high_priority:
            windows = high_priority

    # Select a random window
    window = random.choice(windows)

    # Generate a random time within the window
    start_minutes = window["start"].hour * 60 + window["start"].minute
    end_minutes = window["end"].hour * 60 + window["end"].minute

    # Handle overnight windows
    if end_minutes < start_minutes:
        end_minutes += 24 * 60

    random_minutes = random.randint(start_minutes, end_minutes) % (24 * 60)
    random_hour = random_minutes // 60
    random_minute = random_minutes % 60

    return target_date.replace(
        hour=random_hour,
        minute=random_minute,
        second=0,
        microsecond=0,
    )


def get_day_rating(
    target_date: datetime,
    niche: str = None,
) -> dict:
    """
    Get the performance rating for a specific day.

    Args:
        target_date: Date to evaluate
        niche: Optional niche for special considerations

    Returns:
        Dict with day rating information
    """
    day_of_week = target_date.weekday()
    pattern = DAY_PATTERNS[day_of_week]

    rating = pattern.copy()
    rating["day_name"] = target_date.strftime("%A")

    # Check for special niche bonuses
    if niche and "special_niches" in pattern and niche in pattern["special_niches"]:
        rating["niche_bonus"] = True
        rating["multiplier"] = pattern["multiplier"] * 1.1

    return rating


def generate_weekly_schedule(
    niche: str,
    posts_per_day: int = 1,
    start_date: datetime = None,
) -> list:
    """
    Generate a full week posting schedule.

    Args:
        niche: One of "scary-stories", "finance", "luxury"
        posts_per_day: Number of posts per day
        start_date: First day of schedule (defaults to tomorrow)

    Returns:
        List of dicts with scheduled posting times
    """
    if start_date is None:
        start_date = datetime.now() + timedelta(days=1)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

    schedule = []

    for day_offset in range(7):
        current_date = start_date + timedelta(days=day_offset)
        day_rating = get_day_rating(current_date, niche)

        for post_num in range(posts_per_day):
            posting_time = get_optimal_posting_time(niche, current_date)

            # Offset for multiple posts
            if post_num > 0:
                spacing = random.randint(4, 6)
                posting_time = posting_time + timedelta(hours=spacing * post_num)
                # Wrap around if past midnight
                if posting_time.hour < 6:
                    posting_time = posting_time.replace(hour=random.randint(18, 21))

            schedule.append(
                {
                    "datetime": posting_time,
                    "day": posting_time.strftime("%A"),
                    "time": posting_time.strftime("%I:%M %p"),
                    "day_performance": day_rating["performance"],
                    "day_notes": day_rating["notes"],
                    "niche": niche,
                    "post_number": post_num + 1,
                }
            )

    # Sort by datetime
    schedule.sort(key=lambda x: x["datetime"])

    return schedule


def get_next_optimal_slot(
    niche: str,
    after: datetime = None,
) -> dict:
    """
    Get the next optimal posting slot after a given time.

    Args:
        niche: One of "scary-stories", "finance", "luxury"
        after: Time to find slot after (defaults to now)

    Returns:
        Dict with next optimal posting time and info
    """
    if after is None:
        after = datetime.now()

    # Check next 48 hours
    for hours_ahead in range(48):
        check_time = after + timedelta(hours=hours_ahead)
        day_rating = get_day_rating(check_time, niche)

        # Skip low-performance days unless necessary
        if day_rating["multiplier"] < 0.9 and hours_ahead < 24:
            continue

        windows = POSTING_WINDOWS[niche]["best_times"]
        for window in windows:
            window_start = check_time.replace(
                hour=window["start"].hour,
                minute=window["start"].minute,
            )
            window_end = check_time.replace(
                hour=window["end"].hour,
                minute=window["end"].minute,
            )

            if window_start <= check_time <= window_end:
                return {
                    "datetime": check_time,
                    "formatted": check_time.strftime("%A, %I:%M %p"),
                    "day_rating": day_rating,
                    "window_priority": window.get("priority", "medium"),
                    "niche": niche,
                }

            if check_time < window_start:
                return {
                    "datetime": window_start,
                    "formatted": window_start.strftime("%A, %I:%M %p"),
                    "day_rating": day_rating,
                    "window_priority": window.get("priority", "medium"),
                    "niche": niche,
                }

    # Fallback to any time tomorrow
    tomorrow = after + timedelta(days=1)
    return {
        "datetime": get_optimal_posting_time(niche, tomorrow),
        "formatted": tomorrow.strftime("%A, %I:%M %p"),
        "day_rating": get_day_rating(tomorrow, niche),
        "window_priority": "medium",
        "niche": niche,
    }


def format_schedule_for_display(schedule: list) -> str:
    """
    Format a schedule list for human-readable display.

    Args:
        schedule: List of schedule dicts from generate_weekly_schedule

    Returns:
        Formatted string for display
    """
    lines = ["📅 POSTING SCHEDULE", "=" * 40]

    current_day = None
    for slot in schedule:
        if slot["day"] != current_day:
            current_day = slot["day"]
            lines.append(f"\n{current_day} ({slot['day_performance']})")
            lines.append(f"  └ {slot['day_notes']}")

        lines.append(f"  • {slot['time']} - Post #{slot['post_number']}")

    return "\n".join(lines)


# =============================================================================
# STANDALONE USAGE
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate optimal posting schedules for TikTok"
    )
    parser.add_argument(
        "--niche",
        "-n",
        choices=["scary-stories", "finance", "luxury"],
        default="scary-stories",
        help="Content niche",
    )
    parser.add_argument(
        "--posts",
        "-p",
        type=int,
        default=1,
        help="Posts per day",
    )
    parser.add_argument(
        "--next",
        action="store_true",
        help="Get next optimal posting slot",
    )
    parser.add_argument(
        "--week",
        "-w",
        action="store_true",
        help="Generate full week schedule",
    )

    args = parser.parse_args()

    if args.next:
        slot = get_next_optimal_slot(args.niche)
        logger.info(
            "Next optimal posting time",
            niche=args.niche,
            formatted=slot["formatted"],
            priority=slot["window_priority"],
            day_rating=slot["day_rating"]["performance"],
        )
    elif args.week:
        schedule = generate_weekly_schedule(args.niche, args.posts)
        logger.info(
            "Weekly schedule generated",
            niche=args.niche,
            posts_per_day=args.posts,
            total_slots=len(schedule),
        )
        logger.debug("Schedule details", schedule=format_schedule_for_display(schedule))
    else:
        optimal = get_optimal_posting_time(args.niche)
        logger.info(
            "Suggested posting time",
            niche=args.niche,
            day=optimal.strftime("%A"),
            time=optimal.strftime("%I:%M %p"),
        )

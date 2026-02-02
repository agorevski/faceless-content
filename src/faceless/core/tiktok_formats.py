"""
TikTok-Native Content Formats Module



Defines specialized content formats optimized for TikTok engagement
Based on FUTURE_IMPROVEMENTS.md format recommendations
"""

from dataclasses import dataclass

from faceless.utils.logging import get_logger

logger = get_logger(__name__)

# =============================================================================
# FORMAT DEFINITIONS
# =============================================================================


@dataclass
class TikTokFormat:
    """Represents a TikTok-native content format."""

    name: str
    description: str
    structure: list
    duration_range: tuple  # (min_seconds, max_seconds)
    visual_requirements: dict
    why_it_works: str
    niche: str


# =============================================================================
# SCARY STORIES FORMATS
# =============================================================================

SCARY_FORMATS = {
    "pov_horror": TikTokFormat(
        name="POV Horror",
        description="First-person immersive content that puts the viewer in the scary situation",
        structure=[
            {"element": "text_overlay", "content": "POV: [situation]", "duration": 2},
            {"element": "camera_movement", "type": "first_person_walking"},
            {
                "element": "narration",
                "style": "second_person",
                "note": "Describe what 'you' experience",
            },
            {"element": "ending", "type": "jump_scare_or_cliffhanger"},
        ],
        duration_range=(30, 60),
        visual_requirements={
            "camera_style": "handheld_pov",
            "lighting": "dark_atmospheric",
            "text_position": "top_center",
        },
        why_it_works="Creates visceral, personal fear response. High save/share rate.",
        niche="scary-stories",
    ),
    "green_screen_storytime": TikTokFormat(
        name="Green Screen Storytime",
        description="Creator appears in corner while story plays out behind them",
        structure=[
            {"element": "creator_face", "position": "bottom_corner", "size": "small"},
            {"element": "background", "type": "ai_generated_scary_images"},
            {"element": "narration", "style": "storytelling"},
            {"element": "creator_reactions", "at": "key_moments"},
        ],
        duration_range=(45, 90),
        visual_requirements={
            "layout": "picture_in_picture",
            "background_style": "cinematic_horror",
            "creator_position": "bottom_right",
        },
        why_it_works="Human face increases retention; reaction builds emotional connection.",
        niche="scary-stories",
    ),
    "ranking_viewer_stories": TikTokFormat(
        name="Ranking Scary Stories You Sent Me",
        description="User-generated content integration with tier ranking",
        structure=[
            {
                "element": "hook",
                "content": "You guys sent me your scary stories, let's rank them",
            },
            {"element": "submissions", "display": "tier_ranking"},
            {"element": "brief_summary", "per_story": True},
            {"element": "cta", "content": "Send me your stories for part 2"},
        ],
        duration_range=(45, 60),
        visual_requirements={
            "layout": "tier_list_style",
            "text_display": "animated_reveals",
        },
        why_it_works="Encourages engagement, creates series potential, builds community.",
        niche="scary-stories",
    ),
    "split_screen_reaction": TikTokFormat(
        name="Split-Screen Reaction",
        description="React to found footage or creepy content",
        structure=[
            {"element": "split_top", "content": "creepy_video_or_image"},
            {"element": "split_bottom", "content": "realtime_reaction"},
            {"element": "commentary", "style": "point_out_details"},
            {"element": "build_to_reveal"},
        ],
        duration_range=(30, 60),
        visual_requirements={
            "layout": "vertical_split",
            "top_ratio": 0.6,
            "bottom_ratio": 0.4,
        },
        why_it_works="Dual content streams increase watch time; reactions are relatable.",
        niche="scary-stories",
    ),
    "rules_of_location": TikTokFormat(
        name="The Rules of [Location]",
        description="Rule-based horror with mysterious implications",
        structure=[
            {
                "element": "hook",
                "template": "If you ever find yourself at [location], follow these rules",
            },
            {"element": "rules_list", "style": "ominous", "count": "5-7"},
            {"element": "no_explanation", "note": "Let imagination fill gaps"},
            {"element": "final_rule", "template": "Rule #X: Never break Rule #1"},
        ],
        duration_range=(45, 60),
        visual_requirements={
            "text_style": "typewriter_effect",
            "background": "related_to_location",
            "mood": "ominous_ambient",
        },
        why_it_works="Mysterious, rewatchable to catch all rules, highly shareable.",
        niche="scary-stories",
    ),
    "creepy_text_messages": TikTokFormat(
        name="Creepy Text Message Stories",
        description="Display format with building tension through text conversation",
        structure=[
            {"element": "text_conversation", "display": "message_by_message"},
            {"element": "sound", "type": "message_notification"},
            {"element": "build_tension", "to": "disturbing_revelation"},
            {"element": "ending", "type": "typing_indicator_or_unread"},
        ],
        duration_range=(30, 60),
        visual_requirements={
            "layout": "imessage_style",
            "animation": "messages_appear_sequentially",
            "sound": "text_notification_sounds",
        },
        why_it_works="Familiar format, easy to follow, perfect for loops.",
        niche="scary-stories",
    ),
}


# =============================================================================
# FINANCE FORMATS
# =============================================================================

FINANCE_FORMATS = {
    "financial_red_flags_dating": TikTokFormat(
        name="Financial Red Flags in Dating",
        description="Crossover content between finance and relationships",
        structure=[
            {"element": "hook", "template": "Financial red flags that mean RUN 🚩"},
            {"element": "list", "content": "concerning_money_behaviors"},
            {"element": "tone", "style": "serious_with_humor"},
            {"element": "cta", "content": "What's the biggest red flag you've seen?"},
        ],
        duration_range=(30, 60),
        visual_requirements={
            "icons": "red_flag_emoji",
            "text_style": "bold_impact",
            "background": "clean_minimal",
        },
        why_it_works="Relationship content performs well; makes finance relatable.",
        niche="finance",
    ),
    "things_that_scream_broke": TikTokFormat(
        name="Things That Scream 'I'm Broke'",
        description="Controversial, shareable observations about spending habits",
        structure=[
            {"element": "hook", "content": "Things that SCREAM 'I'm broke'"},
            {"element": "list", "mix": "obvious_and_unexpected"},
            {"element": "controversy", "level": "mild_debate_worthy"},
            {"element": "cta", "content": "Which of these have you done? Be honest"},
        ],
        duration_range=(30, 45),
        visual_requirements={
            "style": "text_on_screen",
            "pacing": "fast_cuts",
        },
        why_it_works="Triggers self-reflection and defensive comments; highly debatable.",
        niche="finance",
    ),
    "roast_my_spending": TikTokFormat(
        name="Roast My Spending Duets",
        description="Interactive format using TikTok's duet feature",
        structure=[
            {"element": "template_video", "content": "ask_for_spending_submissions"},
            {"element": "duet", "with": "viewer_submissions"},
            {"element": "commentary", "style": "constructive_entertaining"},
            {"element": "actionable_advice", "at": "end"},
        ],
        duration_range=(45, 60),
        visual_requirements={
            "layout": "duet_side_by_side",
            "text": "spending_breakdown_overlay",
        },
        why_it_works="UGC integration, series potential, builds community.",
        niche="finance",
    ),
    "money_hot_takes": TikTokFormat(
        name="Money Hot Takes",
        description="Quick controversial opinion content over trending sounds",
        structure=[
            {"element": "trending_sound", "volume": "background"},
            {"element": "text_overlay", "content": "controversial_money_opinion"},
            {"element": "duration", "range": "7-15_seconds"},
        ],
        duration_range=(7, 15),
        visual_requirements={
            "text_style": "large_bold",
            "background": "simple_or_trending",
        },
        why_it_works="Short form catches scrollers; opinions trigger engagement.",
        niche="finance",
    ),
    "what_x_gets_you": TikTokFormat(
        name="What $X Gets You In [Location]",
        description="Visual comparison of purchasing power",
        structure=[
            {"element": "comparison", "type": "dollar_amounts"},
            {"element": "visuals", "style": "side_by_side_or_sequence"},
            {"element": "locations", "variety": "cities_or_countries"},
            {"element": "cta", "content": "Where would your money go further?"},
        ],
        duration_range=(30, 60),
        visual_requirements={
            "layout": "split_comparison",
            "text": "price_labels",
        },
        why_it_works="Relatable, educational, encourages location-based comments.",
        niche="finance",
    ),
    "i_did_the_math": TikTokFormat(
        name="I Did the Math On [Thing]",
        description="Data-driven revelations with surprising totals",
        structure=[
            {"element": "common_belief", "as": "starting_point"},
            {"element": "calculation", "display": "step_by_step"},
            {"element": "reveal", "type": "surprising_total"},
            {"element": "alternative", "with": "better_math"},
        ],
        duration_range=(30, 60),
        visual_requirements={
            "text_style": "calculator_aesthetic",
            "numbers": "animated_counting",
        },
        why_it_works="Education + shock value; positions you as authority.",
        niche="finance",
    ),
}


# =============================================================================
# LUXURY FORMATS
# =============================================================================

LUXURY_FORMATS = {
    "guess_the_price": TikTokFormat(
        name="Guess the Price Reveals",
        description="Interactive guessing game format",
        structure=[
            {"element": "show_item", "without": "price"},
            {"element": "text", "content": "How much do you think this costs?"},
            {"element": "pause", "duration": "3-5_seconds"},
            {"element": "reveal", "with": "dramatic_sound"},
            {"element": "comparison", "optional": True},
        ],
        duration_range=(15, 30),
        visual_requirements={
            "item_display": "glamour_shot",
            "reveal_animation": "price_drop_in",
            "sound": "dramatic_reveal",
        },
        why_it_works="Interactive, gamified, triggers comments with guesses.",
        niche="luxury",
    ),
    "rich_people_secrets": TikTokFormat(
        name="Things Rich People Do That You Don't Notice",
        description="Insider knowledge format revealing subtle wealth indicators",
        structure=[
            {
                "element": "hook",
                "content": "Things rich people do that you don't notice",
            },
            {"element": "reveals", "mix": "obvious_and_subtle"},
            {"element": "insider_tone"},
            {"element": "cta", "content": "What else have you noticed? 👇"},
        ],
        duration_range=(30, 60),
        visual_requirements={
            "visuals": "subtle_luxury_indicators",
            "text": "revelation_style",
        },
        why_it_works="Makes viewers feel like insiders; shareable observations.",
        niche="luxury",
    ),
    "pov_afford_anything": TikTokFormat(
        name="POV: You Can Afford Anything for 24 Hours",
        description="Aspirational fantasy content",
        structure=[
            {
                "element": "pov_text",
                "content": "POV: You can afford anything for 24 hours",
            },
            {"element": "tour", "style": "first_person"},
            {"element": "escalation", "from": "small_luxuries", "to": "absurd"},
            {"element": "ending", "type": "reality_check_or_motivation"},
        ],
        duration_range=(45, 60),
        visual_requirements={
            "visuals": "aspirational_luxury",
            "style": "dream_sequence",
        },
        why_it_works="Escapism, dream fulfillment, high save rate.",
        niche="luxury",
    ),
    "luxury_asmr": TikTokFormat(
        name="Luxury ASMR / Satisfying Content",
        description="Sensory-focused content with minimal narration",
        structure=[
            {"element": "closeup_shots", "of": "luxury_items"},
            {"element": "sounds", "type": "satisfying_asmr"},
            {"element": "slow_motion", "reveals": True},
            {"element": "narration", "level": "minimal_or_none"},
        ],
        duration_range=(15, 45),
        visual_requirements={
            "shots": "extreme_closeup",
            "audio": "crisp_asmr",
            "pace": "slow_satisfying",
        },
        why_it_works="Highly loopable, satisfying content performs well, cross-audience appeal.",
        niche="luxury",
    ),
    "cheap_vs_expensive": TikTokFormat(
        name="Cheap vs Expensive - Can You Tell?",
        description="Comparison/test format",
        structure=[
            {"element": "show_two_items", "side_by_side": True},
            {"element": "one_real", "one_dupe": True},
            {"element": "ask_viewers", "to": "guess"},
            {"element": "reveal", "with": "explanation"},
        ],
        duration_range=(30, 60),
        visual_requirements={
            "layout": "side_by_side",
            "labels": "A_and_B",
            "reveal": "animated",
        },
        why_it_works="Interactive, educational, encourages comments.",
        niche="luxury",
    ),
    "billionaire_day_in_life": TikTokFormat(
        name="Billionaire Day-in-the-Life",
        description="Aspirational documentary style content",
        structure=[
            {
                "element": "hook",
                "content": "What a billionaire's Tuesday actually looks like",
            },
            {"element": "breakdown", "style": "hour_by_hour"},
            {"element": "mix", "mundane_and_extraordinary": True},
            {"element": "subtle_flex", "on": "differences"},
        ],
        duration_range=(45, 60),
        visual_requirements={
            "style": "documentary",
            "schedule_display": "timeline",
            "visuals": "luxury_lifestyle",
        },
        why_it_works="Voyeuristic appeal, lifestyle content performs well.",
        niche="luxury",
    ),
}


# =============================================================================
# FORMAT REGISTRY
# =============================================================================

ALL_FORMATS = {
    "scary-stories": SCARY_FORMATS,
    "finance": FINANCE_FORMATS,
    "luxury": LUXURY_FORMATS,
}


# =============================================================================
# FORMAT FUNCTIONS
# =============================================================================


def get_format(niche: str, format_name: str) -> TikTokFormat | None:
    """
    Get a specific format by niche and name.

    Args:
        niche: One of "scary-stories", "finance", "luxury"
        format_name: Name of the format

    Returns:
        TikTokFormat object or None if not found
    """
    if niche not in ALL_FORMATS:
        return None
    return ALL_FORMATS[niche].get(format_name)


def get_all_formats_for_niche(niche: str) -> dict:
    """
    Get all formats available for a niche.

    Args:
        niche: One of "scary-stories", "finance", "luxury"

    Returns:
        Dict of format_name -> TikTokFormat
    """
    return ALL_FORMATS.get(niche, {})


def get_format_names(niche: str) -> list:
    """
    Get list of format names for a niche.

    Args:
        niche: One of "scary-stories", "finance", "luxury"

    Returns:
        List of format name strings
    """
    if niche not in ALL_FORMATS:
        return []
    return list(ALL_FORMATS[niche].keys())


def get_random_format(niche: str) -> TikTokFormat | None:
    """
    Get a random format for a niche.

    Args:
        niche: One of "scary-stories", "finance", "luxury"

    Returns:
        Random TikTokFormat object
    """
    import random

    formats = get_all_formats_for_niche(niche)
    if not formats:
        return None
    return random.choice(list(formats.values()))


def format_to_prompt_guidance(format_obj: TikTokFormat) -> str:
    """
    Convert a format to prompt guidance for script enhancement.

    Args:
        format_obj: TikTokFormat object

    Returns:
        String with format guidance for LLM prompts
    """
    structure_desc = "\n".join(
        f"  - {item.get('element', 'unknown')}: {item}" for item in format_obj.structure
    )

    return f"""
FORMAT: {format_obj.name}
DESCRIPTION: {format_obj.description}
DURATION: {format_obj.duration_range[0]}-{format_obj.duration_range[1]} seconds
STRUCTURE:
{structure_desc}
VISUAL REQUIREMENTS: {format_obj.visual_requirements}
WHY IT WORKS: {format_obj.why_it_works}
"""


# =============================================================================
# STANDALONE USAGE
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="TikTok-native content format definitions"
    )
    parser.add_argument(
        "--niche",
        "-n",
        choices=["scary-stories", "finance", "luxury"],
        default="scary-stories",
        help="Content niche",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List all formats for niche",
    )
    parser.add_argument(
        "--format",
        "-f",
        help="Show specific format details",
    )

    args = parser.parse_args()

    if args.list:
        logger.info("Listing formats", niche=args.niche)
        for name in get_format_names(args.niche):
            fmt = get_format(args.niche, name)
            logger.info("Format available", name=name, description=fmt.description[:60])
    elif args.format:
        fmt = get_format(args.niche, args.format)
        if fmt:
            logger.info("Format details", guidance=format_to_prompt_guidance(fmt))
        else:
            logger.warning("Format not found", format_name=args.format, niche=args.niche)
    else:
        fmt = get_random_format(args.niche)
        if fmt:
            logger.info("Random format selected", name=fmt.name)
            logger.info("Format guidance", guidance=format_to_prompt_guidance(fmt))

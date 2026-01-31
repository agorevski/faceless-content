"""
Hashtag Strategy Module
Implements the hashtag ladder system from FUTURE_IMPROVEMENTS.md
Provides niche-specific hashtag recommendations for maximum reach
"""

import random

# =============================================================================
# HASHTAG LADDER SYSTEM
# =============================================================================
# Structure:
# LEVEL 1 (1x): Mega hashtag - 10B+ views
# LEVEL 2 (2x): Niche broad - 100M-1B views
# LEVEL 3 (2x): Niche specific - 1M-100M views
# LEVEL 4 (1x): Trending topic - Currently relevant
# LEVEL 5 (1x): Original series - Your own branding

HASHTAG_LADDER = {
    "scary-stories": {
        "mega": [
            "#fyp",
            "#foryou",
            "#viral",
            "#trending",
            "#foryoupage",
        ],
        "niche_broad": [
            "#scarystory",
            "#horror",
            "#creepy",
            "#scary",
            "#spooky",
            "#haunted",
            "#paranormal",
            "#ghost",
        ],
        "niche_specific": [
            "#nosleep",
            "#redditstories",
            "#truescary",
            "#horrorstory",
            "#creepypasta",
            "#scarystories",
            "#horrortok",
            "#creepytok",
            "#truehorror",
            "#scaryvideos",
            "#nightmarefuel",
            "#darkstories",
        ],
        "series_suggestions": [
            "#MidnightArchives",
            "#3AMStories",
            "#DarkTales",
            "#CreepyCorner",
            "#HauntedHistories",
        ],
    },
    "finance": {
        "mega": [
            "#fyp",
            "#foryou",
            "#viral",
            "#trending",
            "#foryoupage",
        ],
        "niche_broad": [
            "#moneytok",
            "#finance",
            "#investing",
            "#money",
            "#wealth",
            "#stocks",
            "#crypto",
        ],
        "niche_specific": [
            "#financetips",
            "#moneytips",
            "#personalfinance",
            "#debtfree",
            "#budgeting",
            "#financialfreedom",
            "#moneymindset",
            "#investingtips",
            "#stockmarket",
            "#wealthbuilding",
            "#passiveincome",
            "#sidehustle",
        ],
        "series_suggestions": [
            "#MoneyMistakeMonday",
            "#WealthWednesday",
            "#FinanceFriday",
            "#MoneyMindset",
            "#WealthSecrets",
        ],
    },
    "luxury": {
        "mega": [
            "#fyp",
            "#foryou",
            "#viral",
            "#trending",
            "#foryoupage",
        ],
        "niche_broad": [
            "#luxury",
            "#luxurylifestyle",
            "#rich",
            "#wealthy",
            "#millionaire",
            "#billionaire",
        ],
        "niche_specific": [
            "#luxurylife",
            "#expensivethings",
            "#luxurycars",
            "#luxuryhomes",
            "#luxurywatches",
            "#highend",
            "#luxuryliving",
            "#richlifestyle",
            "#luxurytravel",
            "#finerthings",
            "#quietluxury",
            "#oldmoney",
        ],
        "series_suggestions": [
            "#PriceOfPerfection",
            "#BillionaireBreakdown",
            "#GuessThePrice",
            "#QuietLuxurySecrets",
            "#MegaYachtMonday",
        ],
    },
}


# =============================================================================
# TRENDING TOPIC SUGGESTIONS (Updated periodically)
# =============================================================================

TRENDING_TOPICS = {
    "scary-stories": [
        "#storytime",
        "#paranormaltiktok",
        "#hauntedtiktok",
        "#scaryseason",
        "#spookyseason",
        "#truecrime",
    ],
    "finance": [
        "#inflation",
        "#recession",
        "#stocktips",
        "#cryptotok",
        "#realestate",
        "#housingmarket",
    ],
    "luxury": [
        "#luxurytok",
        "#aspirational",
        "#lifestyle",
        "#goals",
        "#dreamlife",
        "#expensive",
    ],
}


# =============================================================================
# HASHTAG GENERATION FUNCTIONS
# =============================================================================


def generate_hashtag_set(
    niche: str,
    series_tag: str = None,
    include_trending: bool = True,
    total_count: int = 7,
) -> list:
    """
    Generate an optimized hashtag set using the ladder system.

    Args:
        niche: One of "scary-stories", "finance", "luxury"
        series_tag: Optional custom series hashtag
        include_trending: Whether to include trending topics
        total_count: Target number of hashtags (5-7 recommended)

    Returns:
        List of hashtags in optimal order
    """
    if niche not in HASHTAG_LADDER:
        niche = "scary-stories"  # Fallback

    ladder = HASHTAG_LADDER[niche]
    hashtags = []

    # Level 1: 1 mega hashtag
    hashtags.append(random.choice(ladder["mega"]))

    # Level 2: 2 niche broad hashtags
    broad_tags = random.sample(
        ladder["niche_broad"], min(2, len(ladder["niche_broad"]))
    )
    hashtags.extend(broad_tags)

    # Level 3: 2 niche specific hashtags
    specific_tags = random.sample(
        ladder["niche_specific"], min(2, len(ladder["niche_specific"]))
    )
    hashtags.extend(specific_tags)

    # Level 4: 1 trending topic (if enabled)
    if include_trending and niche in TRENDING_TOPICS:
        hashtags.append(random.choice(TRENDING_TOPICS[niche]))

    # Level 5: 1 series/original tag
    if series_tag:
        hashtags.append(series_tag if series_tag.startswith("#") else f"#{series_tag}")
    else:
        hashtags.append(random.choice(ladder["series_suggestions"]))

    # Trim to target count
    return hashtags[:total_count]


def generate_hashtag_string(
    niche: str,
    series_tag: str = None,
    include_trending: bool = True,
) -> str:
    """
    Generate hashtags as a ready-to-paste string.

    Args:
        niche: One of "scary-stories", "finance", "luxury"
        series_tag: Optional custom series hashtag
        include_trending: Whether to include trending topics

    Returns:
        Space-separated hashtag string
    """
    hashtags = generate_hashtag_set(niche, series_tag, include_trending)
    return " ".join(hashtags)


def get_series_suggestions(niche: str) -> list:
    """
    Get suggested series hashtags for a niche.

    Args:
        niche: One of "scary-stories", "finance", "luxury"

    Returns:
        List of suggested series hashtags
    """
    if niche not in HASHTAG_LADDER:
        return []
    return HASHTAG_LADDER[niche].get("series_suggestions", [])


def get_all_hashtags(niche: str) -> dict:
    """
    Get all hashtags organized by level for a niche.

    Args:
        niche: One of "scary-stories", "finance", "luxury"

    Returns:
        Dict with hashtags by level
    """
    if niche not in HASHTAG_LADDER:
        return {}

    result = HASHTAG_LADDER[niche].copy()
    if niche in TRENDING_TOPICS:
        result["trending"] = TRENDING_TOPICS[niche]
    return result


def analyze_hashtag_coverage(hashtags: list, niche: str) -> dict:
    """
    Analyze a hashtag set for ladder coverage.

    Args:
        hashtags: List of hashtags to analyze
        niche: One of "scary-stories", "finance", "luxury"

    Returns:
        Dict with analysis of coverage by level
    """
    if niche not in HASHTAG_LADDER:
        return {"error": f"Unknown niche: {niche}"}

    ladder = HASHTAG_LADDER[niche]
    normalized = [h.lower() for h in hashtags]

    analysis = {
        "total_count": len(hashtags),
        "mega_count": sum(
            1 for h in normalized if h in [t.lower() for t in ladder["mega"]]
        ),
        "broad_count": sum(
            1 for h in normalized if h in [t.lower() for t in ladder["niche_broad"]]
        ),
        "specific_count": sum(
            1 for h in normalized if h in [t.lower() for t in ladder["niche_specific"]]
        ),
        "has_series": any(
            h.lower() in [t.lower() for t in ladder["series_suggestions"]]
            for h in normalized
        ),
        "recommendations": [],
    }

    # Generate recommendations
    if analysis["mega_count"] == 0:
        analysis["recommendations"].append(
            "Add at least 1 mega hashtag (#fyp, #foryou)"
        )
    if analysis["broad_count"] < 2:
        analysis["recommendations"].append("Add more niche broad hashtags")
    if analysis["specific_count"] < 2:
        analysis["recommendations"].append("Add more niche specific hashtags")
    if not analysis["has_series"]:
        analysis["recommendations"].append("Consider adding a series/branded hashtag")
    if analysis["total_count"] < 5:
        analysis["recommendations"].append("Use 5-7 hashtags for optimal reach")
    if analysis["total_count"] > 10:
        analysis["recommendations"].append("Consider reducing to 5-7 hashtags")

    return analysis


# =============================================================================
# CONTENT-SPECIFIC HASHTAG SUGGESTIONS
# =============================================================================


def get_format_specific_hashtags(niche: str, format_name: str) -> list:
    """
    Get additional hashtags specific to a content format.

    Args:
        niche: One of "scary-stories", "finance", "luxury"
        format_name: Name of the TikTok format being used

    Returns:
        List of additional format-specific hashtags
    """
    format_hashtags = {
        "scary-stories": {
            "pov_horror": ["#pov", "#povhorror", "#scarypov"],
            "rules_of_location": ["#rules", "#ruleshorror", "#therules"],
            "creepy_text_messages": ["#texthorror", "#creepytexts", "#scarytext"],
            "split_screen_reaction": ["#reaction", "#scaryfootage"],
        },
        "finance": {
            "financial_red_flags_dating": [
                "#redflag",
                "#datingadvice",
                "#moneyredflags",
            ],
            "things_that_scream_broke": ["#broke", "#moneymistakes"],
            "roast_my_spending": ["#roast", "#duet", "#spendinghabits"],
            "i_did_the_math": ["#math", "#calculations", "#themath"],
        },
        "luxury": {
            "guess_the_price": ["#guesstheprice", "#pricereveal", "#expensive"],
            "cheap_vs_expensive": ["#cheapvsexpensive", "#spotthefake", "#realvsfake"],
            "luxury_asmr": ["#asmr", "#satisfying", "#luxuryasmr"],
        },
    }

    if niche not in format_hashtags:
        return []
    return format_hashtags[niche].get(format_name, [])


# =============================================================================
# STANDALONE USAGE
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate optimized hashtags for TikTok content"
    )
    parser.add_argument(
        "--niche",
        "-n",
        choices=["scary-stories", "finance", "luxury"],
        default="scary-stories",
        help="Content niche",
    )
    parser.add_argument(
        "--series",
        "-s",
        help="Custom series hashtag",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List all hashtags for niche",
    )
    parser.add_argument(
        "--analyze",
        "-a",
        nargs="+",
        help="Analyze provided hashtags",
    )

    args = parser.parse_args()

    if args.list:
        print(f"\nHashtags for {args.niche}:\n")
        all_tags = get_all_hashtags(args.niche)
        for level, tags in all_tags.items():
            print(f"  {level.upper()}:")
            print(f"    {', '.join(tags)}\n")
    elif args.analyze:
        analysis = analyze_hashtag_coverage(args.analyze, args.niche)
        print("\nHashtag Analysis:")
        for key, value in analysis.items():
            print(f"  {key}: {value}")
    else:
        hashtags = generate_hashtag_string(args.niche, args.series)
        print(f"\nGenerated hashtags for {args.niche}:")
        print(f"  {hashtags}")

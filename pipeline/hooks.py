"""
Hooks Module - TikTok Retention & Engagement System
Implements first-frame hooks, pattern interrupts, mid-video retention,
and comment bait strategies from FUTURE_IMPROVEMENTS.md
"""

import random

# =============================================================================
# FIRST-FRAME HOOKS (0.5-Second Attention Window)
# =============================================================================

FIRST_FRAME_HOOKS = {
    "scary-stories": {
        "text_question": [
            "Would you enter this door?",
            "Have you ever felt like you're being watched?",
            "What's the scariest thing you've ever seen?",
            "Would you stay in this house alone?",
            "Do you believe in things you can't explain?",
            "What would you do if you heard this at 3AM?",
            "Have you ever seen something you couldn't explain?",
            "Would you open this if you found it?",
            "Do you know what's watching you right now?",
            "Have you checked behind you recently?",
        ],
        "shocking_statement": [
            "I should have listened to my instincts.",
            "That was the last time I ever went there.",
            "I still can't sleep with the lights off.",
            "They never found what made those sounds.",
            "No one believed me until they saw it themselves.",
            "I'll never forget what I saw that night.",
            "Some doors should never be opened.",
            "I wasn't alone in that house.",
            "The scratching stopped. That's when I knew.",
            "It was behind me the whole time.",
        ],
        "number_promise": [
            "3 signs you're not alone in your house",
            "5 things you should NEVER do at 3AM",
            "The 1 rule that saved my life",
            "4 warning signs I ignored",
            "3 sounds that mean you need to RUN",
        ],
        "direct_address": [
            "You know that feeling when something's wrong?",
            "You've felt this before, haven't you?",
            "You're going to want to watch this to the end.",
            "You won't believe what happened next.",
            "You need to hear this before it's too late.",
        ],
    },
    "finance": {
        "text_question": [
            "Are you making this money mistake?",
            "Why are you still broke?",
            "Do you know where your money really goes?",
            "Think you're good with money?",
            "How much are you losing every month?",
            "Would you pass a financial IQ test?",
            "Are you secretly going broke?",
            "Do you know your real net worth?",
        ],
        "shocking_statement": [
            "The #1 reason you'll never be rich.",
            "Rich people NEVER do this.",
            "This one habit keeps you poor.",
            "Your bank is stealing from you.",
            "You're losing money while you sleep.",
            "Stop doing this with your money.",
            "This is why you're always broke.",
            "Your financial advisor lied to you.",
        ],
        "number_promise": [
            "3 money habits of millionaires",
            "5 things keeping you poor",
            "The 1% rule for building wealth",
            "7 money mistakes I wish I knew earlier",
            "3 investments that actually work",
            "5 signs you're secretly going broke",
        ],
        "direct_address": [
            "You're working too hard for too little.",
            "You've been lied to about money.",
            "You're one decision away from wealth.",
            "You need to stop what you're doing with money.",
            "You're making this mistake right now.",
        ],
    },
    "luxury": {
        "text_question": [
            "Guess how much this costs?",
            "Would you pay this much for a watch?",
            "Can you spot the $50,000 detail?",
            "What makes this worth millions?",
            "Would you drive this every day?",
            "Can you tell real from fake?",
        ],
        "shocking_statement": [
            "This costs more than your house.",
            "Only 10 people in the world own this.",
            "This car costs $100,000 PER MONTH.",
            "The waitlist is 5 years long.",
            "They destroy unsold inventory.",
            "This watch took 3 years to make.",
        ],
        "number_promise": [
            "5 things only the ultra-rich buy",
            "3 luxury items that are actually worth it",
            "The $1 million daily routine",
            "7 signs of quiet luxury",
            "3 things billionaires never buy",
        ],
        "direct_address": [
            "You've never seen anything like this.",
            "You won't believe what this costs.",
            "You're looking at pure perfection.",
            "You could own this. Here's how.",
            "You're about to see real luxury.",
        ],
    },
}


# =============================================================================
# PATTERN INTERRUPT OPENERS
# =============================================================================

PATTERN_INTERRUPTS = {
    "audio": [
        "sudden_silence",  # Silence after trending sound
        "record_scratch",  # Classic attention-grabber
        "whisper_start",  # Whispered opening
        "reversed_audio",  # 0.5 sec reversed audio
        "heartbeat",  # Tension builder
        "glass_break",  # Sharp pattern break
    ],
    "visual": [
        "inverted_colors",  # Inverted for first 0.5 sec
        "extreme_closeup",  # Close-up that pulls back
        "black_screen_text",  # Black screen with single word
        "glitch_transition",  # Glitch effect in
        "flash_frame",  # Quick flash of upcoming reveal
        "zoom_blur",  # Blur to sharp focus
    ],
}


# =============================================================================
# MID-VIDEO RETENTION HOOKS (30-50% Mark)
# =============================================================================

MID_VIDEO_HOOKS = {
    "verbal": {
        "scary-stories": [
            "But here's where it gets worse...",
            "Wait until you see what happens next.",
            "That's not even the scary part.",
            "I saved the worst for last.",
            "But they made one mistake...",
            "And then I heard it again.",
            "That's when everything changed.",
            "But I wasn't prepared for what came next.",
            "Little did I know...",
            "And that's when I realized the truth.",
        ],
        "finance": [
            "But here's what they don't tell you...",
            "Wait, it gets better.",
            "This is where it gets interesting.",
            "But the real secret is...",
            "Here's the part that changes everything.",
            "Most people miss this crucial detail.",
            "But there's a catch...",
            "Now here's the game-changer.",
        ],
        "luxury": [
            "But wait until you see inside...",
            "That's not even the impressive part.",
            "Here's what makes it truly special.",
            "But the real luxury is hidden.",
            "This is where it gets exclusive.",
            "Wait until you see the price tag.",
            "But there's something even more rare.",
            "Here's what you don't see.",
        ],
    },
    "text_overlay": [
        "WAIT FOR IT",
        "👀",
        "HERE IT COMES",
        "WATCH THIS",
        "DON'T SCROLL",
        "IT GETS WORSE",
        "KEEP WATCHING",
        "3... 2... 1...",
    ],
    "visual_cues": [
        "arrow_pointing_forward",
        "countdown_timer",
        "flash_of_upcoming",
        "zoom_emphasis",
        "split_second_reveal",
    ],
}


# =============================================================================
# COMMENT BAIT & ENGAGEMENT TRIGGERS
# =============================================================================

COMMENT_TRIGGERS = {
    "controversial_endings": {
        "scary-stories": [
            "I think this is actually NOT that scary - what do you think?",
            "Honestly, I would have stayed. Would you?",
            "Was this real or fake? You decide.",
            "I think they made it up. Change my mind.",
            "The scariest part wasn't even shown. Can you guess?",
        ],
        "finance": [
            "This is why renting is smarter than buying. Fight me.",
            "College is a waste of money. Agree or disagree?",
            "Crypto is dead. Change my mind.",
            "The 9-5 is actually the safest path. Debate me.",
            "Rich people aren't that smart. They're just lucky.",
        ],
        "luxury": [
            "This is overpriced garbage. Change my mind.",
            "Rich people have no taste. Just money.",
            "This is actually tacky. Real wealth is subtle.",
            "You don't need this to be happy. Or do you?",
            "Old money would never buy this.",
        ],
    },
    "opinion_requests": [
        "Rate this from 1-10 👇",
        "Would you do this? Yes or no",
        "Which is better - A or B?",
        "What would YOU have done?",
        "Drop a 🔥 if you agree",
        "Comment your answer below",
        "Tell me I'm wrong 👇",
        "Who else experienced this?",
    ],
    "fill_in_blank": {
        "scary-stories": [
            "The scariest place I've ever been is ____",
            "I'll never forget the time I ____",
            "The creepiest thing that happened to me was ____",
            "My biggest fear is ____",
        ],
        "finance": [
            "My biggest money mistake was ____",
            "I wish I had known ____ about money earlier",
            "The best financial advice I got was ____",
            "I save money by ____",
        ],
        "luxury": [
            "The most expensive thing I own is ____",
            "My dream luxury item is ____",
            "The most overrated luxury brand is ____",
            "I would never pay ____ for anything",
        ],
    },
    "part_2_bait": [
        "Should I make a part 2?",
        "Comment 'MORE' if you want the full story",
        "Part 2? Let me know 👇",
        "This is just the beginning...",
        "Want to know what happened next?",
        "Follow for part 2",
        "The rest of the story drops tomorrow",
    ],
}


# =============================================================================
# PINNED COMMENT TEMPLATES
# =============================================================================

PINNED_COMMENTS = {
    "scary-stories": [
        "What's the scariest thing that's ever happened to you? 👇",
        "Fun fact: the original story was even longer. Want the full version?",
        "This happened in [location]. Anyone else from there? 👀",
        "I have 10 more stories like this. Which one should I post next?",
        "POV: You're reading this at 3AM 💀",
        "The ending isn't even the scariest part... comment if you caught it",
    ],
    "finance": [
        "Okay but which of these money mistakes have YOU made? Be honest 😂",
        "Drop your biggest money regret below 👇",
        "What's your net worth goal for this year?",
        "Controversial take: most financial advice is garbage. Agree?",
        "Which tip are you implementing first? Let me know!",
        "I learned this the hard way. Don't make my mistakes.",
    ],
    "luxury": [
        "Would you buy this if you could afford it? 👇",
        "Guess the price before I reveal it!",
        "What's on your luxury wishlist?",
        "Real or fake? Can you tell the difference?",
        "What's the most you've ever spent on one item?",
        "Drop a 💎 if this is your dream",
    ],
}


# =============================================================================
# LOOP STRUCTURE TEMPLATES
# =============================================================================

LOOP_STRUCTURES = {
    "audio_loop": {
        "description": "End and begin with the same sound/music beat",
        "technique": "Match last 0.5s audio to first 0.5s",
    },
    "visual_loop": {
        "description": "Last frame matches or leads into first frame",
        "technique": "End on same visual element as opening",
    },
    "narrative_loop": {
        "description": "End mid-sentence, continue from the start",
        "examples": [
            "And that's when I realized... [loop to start]",
            "I still don't know what it was, but... [loop]",
            "To this day, I wonder... [loop]",
        ],
    },
    "question_loop": {
        "description": "End with question that the video answers",
        "examples": [
            "Why did I go back? [loop to start showing why]",
            "How did I survive? [loop to story]",
            "What was watching me? [loop to reveal]",
        ],
    },
}


# =============================================================================
# HOOK GENERATION FUNCTIONS
# =============================================================================


def get_first_frame_hook(
    niche: str,
    hook_type: str = None,
    custom_context: str = None,
) -> dict:
    """
    Get a first-frame hook for a video.

    Args:
        niche: One of "scary-stories", "finance", "luxury"
        hook_type: Optional specific type (text_question, shocking_statement, etc.)
        custom_context: Optional context to customize the hook

    Returns:
        Dict with hook text and metadata
    """
    if niche not in FIRST_FRAME_HOOKS:
        niche = "scary-stories"  # Fallback

    hooks = FIRST_FRAME_HOOKS[niche]

    if hook_type and hook_type in hooks:
        hook_list = hooks[hook_type]
    else:
        # Random type selection with weights
        types = list(hooks.keys())
        weights = [0.3, 0.3, 0.2, 0.2]  # Favor questions and statements
        hook_type = random.choices(types, weights=weights)[0]
        hook_list = hooks[hook_type]

    hook_text = random.choice(hook_list)

    return {
        "text": hook_text,
        "type": hook_type,
        "niche": niche,
        "display_duration": 3.0,  # Seconds to display
        "position": "center",  # Where to overlay text
    }


def get_pattern_interrupt(interrupt_type: str = None) -> dict:
    """
    Get a pattern interrupt technique.

    Args:
        interrupt_type: "audio" or "visual", or None for random

    Returns:
        Dict with interrupt details
    """
    if interrupt_type is None:
        interrupt_type = random.choice(["audio", "visual"])

    technique = random.choice(PATTERN_INTERRUPTS[interrupt_type])

    return {
        "type": interrupt_type,
        "technique": technique,
        "duration": 0.5,  # Seconds
    }


def get_mid_video_hook(niche: str, hook_format: str = None) -> dict:
    """
    Get a mid-video retention hook.

    Args:
        niche: One of "scary-stories", "finance", "luxury"
        hook_format: "verbal", "text_overlay", or "visual_cues"

    Returns:
        Dict with hook details
    """
    if hook_format is None:
        hook_format = random.choice(["verbal", "text_overlay"])

    if hook_format == "verbal":
        if niche not in MID_VIDEO_HOOKS["verbal"]:
            niche = "scary-stories"
        hook_content = random.choice(MID_VIDEO_HOOKS["verbal"][niche])
    elif hook_format == "text_overlay":
        hook_content = random.choice(MID_VIDEO_HOOKS["text_overlay"])
    else:
        hook_content = random.choice(MID_VIDEO_HOOKS["visual_cues"])

    return {
        "format": hook_format,
        "content": hook_content,
        "insert_at_percent": random.randint(30, 50),  # 30-50% mark
        "duration": 2.0 if hook_format == "text_overlay" else None,
    }


def get_comment_trigger(niche: str, trigger_type: str = None) -> dict:
    """
    Get a comment-triggering ending.

    Args:
        niche: One of "scary-stories", "finance", "luxury"
        trigger_type: Type of trigger or None for random

    Returns:
        Dict with trigger details
    """
    if trigger_type is None:
        trigger_type = random.choice(
            [
                "controversial_endings",
                "opinion_requests",
                "fill_in_blank",
                "part_2_bait",
            ]
        )

    if trigger_type == "controversial_endings":
        if niche not in COMMENT_TRIGGERS["controversial_endings"]:
            niche = "scary-stories"
        content = random.choice(COMMENT_TRIGGERS["controversial_endings"][niche])
    elif trigger_type == "opinion_requests":
        content = random.choice(COMMENT_TRIGGERS["opinion_requests"])
    elif trigger_type == "fill_in_blank":
        if niche not in COMMENT_TRIGGERS["fill_in_blank"]:
            niche = "scary-stories"
        content = random.choice(COMMENT_TRIGGERS["fill_in_blank"][niche])
    else:
        content = random.choice(COMMENT_TRIGGERS["part_2_bait"])

    return {
        "type": trigger_type,
        "content": content,
        "niche": niche,
    }


def get_pinned_comment(niche: str) -> str:
    """
    Get a pinned comment suggestion.

    Args:
        niche: One of "scary-stories", "finance", "luxury"

    Returns:
        Suggested pinned comment text
    """
    if niche not in PINNED_COMMENTS:
        niche = "scary-stories"
    return random.choice(PINNED_COMMENTS[niche])


def get_loop_structure(loop_type: str = None) -> dict:
    """
    Get loop structure guidance.

    Args:
        loop_type: Specific loop type or None for recommendation

    Returns:
        Dict with loop structure details
    """
    if loop_type is None:
        loop_type = random.choice(list(LOOP_STRUCTURES.keys()))

    structure = LOOP_STRUCTURES[loop_type].copy()
    structure["type"] = loop_type

    return structure


def generate_engagement_package(niche: str) -> dict:
    """
    Generate a complete engagement package for a video.

    Args:
        niche: One of "scary-stories", "finance", "luxury"

    Returns:
        Dict with all engagement elements
    """
    return {
        "first_frame_hook": get_first_frame_hook(niche),
        "pattern_interrupt": get_pattern_interrupt(),
        "mid_video_hook": get_mid_video_hook(niche),
        "comment_trigger": get_comment_trigger(niche),
        "pinned_comment": get_pinned_comment(niche),
        "loop_structure": get_loop_structure(),
    }


# =============================================================================
# STANDALONE USAGE
# =============================================================================

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Generate engagement hooks for TikTok content"
    )
    parser.add_argument(
        "--niche",
        "-n",
        choices=["scary-stories", "finance", "luxury"],
        default="scary-stories",
        help="Content niche",
    )
    parser.add_argument(
        "--full",
        "-f",
        action="store_true",
        help="Generate full engagement package",
    )

    args = parser.parse_args()

    if args.full:
        package = generate_engagement_package(args.niche)
        print(json.dumps(package, indent=2))
    else:
        hook = get_first_frame_hook(args.niche)
        print(f"Hook: {hook['text']}")
        print(f"Type: {hook['type']}")

"""
Script Enhancer Module - LEGACY WRAPPER.

⚠️ DEPRECATED: This module is a backward-compatibility wrapper.
Please use faceless.services.enhancer_service.EnhancerService for new code.

Uses Azure OpenAI GPT to enhance scripts for maximum engagement on YouTube/TikTok
Focuses on catchy storytelling, visual consistency, and scroll-stopping content

Enhanced with TikTok retention strategies from FUTURE_IMPROVEMENTS.md:
- First-frame hooks for 0.5-second attention window
- Mid-video retention hooks at 30-50% mark
- Comment-bait endings for engagement
- Loop structure support for replay optimization
"""

import json
import os
import warnings
from datetime import datetime

import requests

# Issue deprecation warning on import
warnings.warn(
    "pipeline/script_enhancer.py is deprecated. "
    "Use faceless.services.enhancer_service.EnhancerService instead.",
    DeprecationWarning,
    stacklevel=2,
)

from env_config import (
    AZURE_OPENAI_CHAT_API_VERSION,
    AZURE_OPENAI_CHAT_DEPLOYMENT,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
)
from faceless.utils.logging import get_logger

logger = get_logger(__name__)

# Import hook system for engagement generation
try:
    from hooks import (  # noqa: F401
        get_comment_trigger,
        get_first_frame_hook,
        get_loop_structure,
        get_mid_video_hook,
    )

    HOOKS_AVAILABLE = True
except ImportError:
    HOOKS_AVAILABLE = False


# =============================================================================
# ENHANCEMENT PROMPTS BY NICHE
# =============================================================================

ENHANCEMENT_PROMPTS = {
    "scary-stories": {
        "system": """You are a master horror storyteller and viral content creator specializing in
short-form video content for YouTube Shorts and TikTok. Your expertise combines:

1. STORYTELLING: Crafting narratives that grip viewers from the first second
2. PACING: Perfect rhythm that builds tension and prevents scroll-away
3. VISUAL DIRECTION: Creating cinematic image descriptions that captivate
4. HOOK MASTERY: Opening lines that stop thumbs mid-scroll

Your goal is to transform scripts into viral-worthy content that viewers CANNOT scroll past.""",
        "user_template": """Enhance this horror story script for maximum engagement on YouTube/TikTok.

ORIGINAL SCRIPT:
{script_json}

REQUIREMENTS:

1. HOOK OPTIMIZATION (Critical for first 3 seconds):
   - The first scene's narration MUST start with an irresistible hook
   - Use techniques like: shocking statement, direct address ("You know that feeling..."),
     mysterious question, or visceral sensory detail
   - Avoid slow buildups - grab attention IMMEDIATELY

2. NARRATION ENHANCEMENT:
   - Make each scene's narration punchy and tension-filled
   - Add micro-cliffhangers between scenes to prevent scrolling
   - Use sensory language (sounds, textures, temperatures, smells)
   - Keep sentences short and impactful for voiceover pacing
   - Each scene should end with something unresolved or unsettling
   - Maintain first-person perspective for immersion

3. IMAGE PROMPT ENHANCEMENT:
   - Create detailed, cinematic image prompts that would work for AI image generation
   - Include: camera angle, lighting, atmosphere, specific visual details
   - Ensure visual CONSISTENCY across scenes (same character appearance, location details)
   - Add elements of visual horror that complement but don't spoil the narration
   - Reference specific cinematography styles (A24 horror, found footage, etc.)

4. VISUAL STYLE SECTION:
   - Create a cohesive "visual_style" object with:
     - environment: Detailed consistent setting description
     - color_mood: Specific color palette and emotional tone
     - texture: Surface and material details for consistency
     - recurring_elements: Named visual elements that appear across scenes

5. ENGAGEMENT OPTIMIZATION:
   - Structure for 45-90 second total runtime (TikTok sweet spot)
   - Build to a satisfying but haunting conclusion
   - Leave viewers with an image/thought they can't shake
   - Make them want to share and comment

6. TIKTOK RETENTION STRUCTURE (Critical for algorithm):
   - 0-3 sec: HOOK - Pattern interrupt + curiosity gap (first scene MUST hook immediately)
   - 3-10 sec: PROMISE - What they'll learn/see/feel
   - 30-50% mark: MID-VIDEO HOOK - Add retention phrase like "But here's where it gets worse..."
   - Final scene: LOOP/CTA - End with comment-bait question or seamless loop setup
   - Include "first_frame_hook" field with the exact text overlay for the first frame
   - Include "mid_video_hook" with the retention phrase to insert
   - Include "comment_trigger" with the engagement ending

OUTPUT FORMAT:
Return ONLY valid JSON matching this structure (no markdown, no explanation):
{{
  "title": "Enhanced title (catchy, intriguing)",
  "source": "{source}",
  "author": "{author}",
  "url": "{url}",
  "niche": "scary-stories",
  "created_at": "{created_at}",
  "enhanced_at": "{enhanced_at}",
  "first_frame_hook": {{
    "text": "The exact text to overlay on first frame (question or shocking statement)",
    "type": "text_question|shocking_statement|number_promise|direct_address"
  }},
  "mid_video_hook": {{
    "text": "But here's where it gets worse...",
    "insert_after_scene": 2
  }},
  "comment_trigger": {{
    "text": "Would you have stayed? Comment below 👇",
    "type": "opinion_request|controversial|fill_in_blank|part_2_bait"
  }},
  "loop_structure": {{
    "type": "narrative_loop|question_loop|audio_loop",
    "description": "How the ending connects back to beginning"
  }},
  "visual_style": {{
    "environment": "Detailed environment description for consistency",
    "color_mood": "Color palette and emotional lighting guidelines",
    "texture": "Surface and material details",
    "recurring_elements": {{
      "element_name": "Detailed description of recurring visual element"
    }}
  }},
  "scenes": [
    {{
      "scene_number": 1,
      "narration": "Enhanced narration text",
      "image_prompt": "Detailed cinematic image generation prompt",
      "duration_estimate": 30
    }}
  ]
}}""",
    },
    "finance": {
        "system": """You are a viral financial content creator who makes money topics
irresistibly engaging. You combine practical finance wisdom with scroll-stopping presentation
that works on YouTube Shorts and TikTok. Your content makes people feel like they're getting
insider secrets that will change their financial future.

You understand TikTok's algorithm rewards:
- High retention from the first 0.5 seconds
- Mid-video hooks that prevent scroll-away
- Comment-triggering endings that boost engagement
- Loop-worthy content that gets rewatched""",
        "user_template": """Enhance this finance script for maximum engagement on YouTube/TikTok.

ORIGINAL SCRIPT:
{script_json}

REQUIREMENTS:

1. HOOK OPTIMIZATION:
   - Start with a money-related shock or revelation
   - Use phrases like "The #1 mistake...", "Rich people never...", "Stop doing this..."
   - Create immediate FOMO or curiosity

2. NARRATION ENHANCEMENT:
   - Make financial concepts feel like valuable secrets
   - Use concrete numbers and specific examples
   - Add urgency without being scammy
   - Keep language accessible but authoritative

3. IMAGE PROMPT ENHANCEMENT:
   - Create professional, aspirational visuals
   - Use clean modern aesthetics with money/success imagery
   - Include data visualizations, lifestyle shots, or conceptual representations

4. VISUAL STYLE:
   - Create consistent "visual_style" with professional color palette
   - Green/gold for wealth, clean whites for trust
   - Modern, minimalist aesthetic

5. TIKTOK RETENTION (Critical):
   - Include "first_frame_hook" with attention-grabbing text overlay
   - Include "mid_video_hook" at 30-50% mark to retain viewers
   - Include "comment_trigger" ending that sparks debate/engagement
   - Include "loop_structure" describing how end connects to beginning

OUTPUT FORMAT:
Return ONLY valid JSON with: title, source, author, url, niche, created_at, enhanced_at,
first_frame_hook (text, type), mid_video_hook (text, insert_after_scene),
comment_trigger (text, type), loop_structure (type, description),
visual_style, and scenes array.""",
    },
    "luxury": {
        "system": """You are a luxury lifestyle content creator who showcases the world's
most exclusive experiences, products, and lifestyles. Your content makes viewers feel like
they're getting an exclusive peek into a world of wealth and refinement that they aspire to.

You understand TikTok's algorithm rewards:
- Aspirational first-frame hooks that stop the scroll
- "Wait for it" moments that keep viewers watching
- Interactive elements like "Guess the price" that drive comments
- Satisfying loops that get replayed""",
        "user_template": """Enhance this luxury lifestyle script for maximum engagement on YouTube/TikTok.

ORIGINAL SCRIPT:
{script_json}

REQUIREMENTS:

1. HOOK OPTIMIZATION:
   - Open with the most exclusive/expensive/rare element
   - Use specific impressive numbers or exclusive details
   - Create aspiration and fascination

2. NARRATION ENHANCEMENT:
   - Emphasize exclusivity, craftsmanship, rarity
   - Add sensory details (feel of materials, scents, sounds)
   - Include fascinating facts about the luxury items/experiences

3. IMAGE PROMPT ENHANCEMENT:
   - Ultra-premium visual quality with elegant compositions
   - Rich textures, perfect lighting, aspirational settings
   - Gold, black, champagne color palette

4. VISUAL STYLE:
   - Create consistent "visual_style" with luxurious aesthetic
   - Cinematic elegance throughout

5. TIKTOK RETENTION (Critical):
   - Include "first_frame_hook" with aspirational/shocking text overlay
   - Include "mid_video_hook" at 30-50% mark (e.g., "But wait until you see inside...")
   - Include "comment_trigger" ending that invites interaction
   - Include "loop_structure" for replay optimization

OUTPUT FORMAT:
Return ONLY valid JSON with: title, source, author, url, niche, created_at, enhanced_at,
first_frame_hook (text, type), mid_video_hook (text, insert_after_scene),
comment_trigger (text, type), loop_structure (type, description),
visual_style, and scenes array.""",
    },
    "true-crime": {
        "system": """You are a master true crime storyteller and viral content creator specializing in
short-form video content for YouTube Shorts and TikTok. Your expertise combines:

1. INVESTIGATIVE STORYTELLING: Crafting narratives that reveal shocking truths
2. TENSION BUILDING: Perfect pacing that keeps viewers hooked on the mystery
3. VISUAL DIRECTION: Creating documentary-style image descriptions
4. ETHICAL SENSITIVITY: Handling real cases with appropriate gravity

Your goal is to transform scripts into compelling content that educates while captivating.""",
        "user_template": """Enhance this true crime script for maximum engagement on YouTube/TikTok.

ORIGINAL SCRIPT:
{script_json}

REQUIREMENTS:

1. HOOK OPTIMIZATION (Critical for first 3 seconds):
   - Start with a shocking fact, unanswered question, or chilling detail
   - Use techniques like: "They never found...", "The police missed one detail...", "No one suspected..."

2. NARRATION ENHANCEMENT:
   - Build suspense through careful revelation of facts
   - Use precise details (dates, locations, evidence) for credibility
   - Maintain respectful tone while keeping engagement high
   - End scenes with unresolved tension

3. IMAGE PROMPT ENHANCEMENT:
   - Documentary-style visuals: evidence photos, location shots, timeline graphics
   - Dark, investigative atmosphere with noir lighting
   - Include: investigation boards, shadowy scenes, dramatic reenactment style

4. VISUAL STYLE: Create cohesive visual_style with investigation aesthetic

5. TIKTOK RETENTION: Include first_frame_hook, mid_video_hook, comment_trigger, loop_structure

OUTPUT FORMAT:
Return ONLY valid JSON with: title, source, author, url, niche ("true-crime"), created_at, enhanced_at,
first_frame_hook, mid_video_hook, comment_trigger, loop_structure, visual_style, and scenes array.""",
    },
    "psychology-facts": {
        "system": """You are a psychology educator and viral content creator who makes the human mind
fascinating and accessible. You combine scientific accuracy with scroll-stopping presentation
that works on YouTube Shorts and TikTok. Your content makes people feel like they're unlocking
secrets about themselves and others.""",
        "user_template": """Enhance this psychology script for maximum engagement on YouTube/TikTok.

ORIGINAL SCRIPT:
{script_json}

REQUIREMENTS:

1. HOOK OPTIMIZATION:
   - Start with a relatable behavior or surprising psychological fact
   - Use: "Your brain is lying to you...", "Why you always...", "The psychology behind..."

2. NARRATION ENHANCEMENT:
   - Make concepts personally relatable ("You've probably noticed...")
   - Include specific study references for credibility
   - Use "aha moment" structure that makes viewers feel smarter

3. IMAGE PROMPT ENHANCEMENT:
   - Clean, modern educational visuals
   - Brain imagery, human silhouettes, conceptual illustrations
   - Infographic style with clear visual metaphors

4. VISUAL STYLE: Educational, clean, purple/teal color palette

5. TIKTOK RETENTION: Include first_frame_hook, mid_video_hook, comment_trigger, loop_structure

OUTPUT FORMAT:
Return ONLY valid JSON with niche ("psychology-facts") and all required fields.""",
    },
    "history": {
        "system": """You are a history storyteller who brings the past to life with cinematic drama.
You combine historical accuracy with compelling narrative that makes ancient events feel
immediate and relevant. Your content makes viewers feel like they're witnessing history unfold.""",
        "user_template": """Enhance this history script for maximum engagement on YouTube/TikTok.

ORIGINAL SCRIPT:
{script_json}

REQUIREMENTS:

1. HOOK OPTIMIZATION:
   - Start with a dramatic moment, surprising fact, or "What if" scenario
   - Use: "In 1347, something arrived...", "They had 24 hours to decide...", "History forgot..."

2. NARRATION ENHANCEMENT:
   - Create vivid scenes with sensory details of the era
   - Connect historical events to modern relevance
   - Use dramatic irony ("Little did they know...")
   - Build to significant turning points

3. IMAGE PROMPT ENHANCEMENT:
   - Epic historical cinematography, museum-quality recreations
   - Period-accurate details, dramatic lighting
   - Sepia/bronze color grading, aged aesthetic

4. VISUAL STYLE: Epic, cinematic, historically authentic

5. TIKTOK RETENTION: Include first_frame_hook, mid_video_hook, comment_trigger, loop_structure

OUTPUT FORMAT:
Return ONLY valid JSON with niche ("history") and all required fields.""",
    },
    "motivation": {
        "system": """You are a motivational content creator who inspires action and transformation.
You combine powerful messaging with visual impact that moves people emotionally.
Your content makes viewers feel empowered to change their lives immediately.""",
        "user_template": """Enhance this motivation script for maximum engagement on YouTube/TikTok.

ORIGINAL SCRIPT:
{script_json}

REQUIREMENTS:

1. HOOK OPTIMIZATION:
   - Start with a powerful truth bomb or relatable struggle
   - Use: "You're not lazy, you're...", "The difference between success and failure...", "Stop waiting for..."

2. NARRATION ENHANCEMENT:
   - Build emotional momentum toward action
   - Use second person ("You") for direct connection
   - Include specific, actionable insights
   - End with a powerful call to action

3. IMAGE PROMPT ENHANCEMENT:
   - Inspirational imagery: sunrise, mountains, achievement moments
   - Dynamic, empowering compositions
   - Warm, energizing color palette (gold, orange, deep blue)

4. VISUAL STYLE: Empowering, dynamic, aspirational

5. TIKTOK RETENTION: Include first_frame_hook, mid_video_hook, comment_trigger, loop_structure

OUTPUT FORMAT:
Return ONLY valid JSON with niche ("motivation") and all required fields.""",
    },
    "space-astronomy": {
        "system": """You are a space science communicator who makes the cosmos accessible and awe-inspiring.
You combine scientific accuracy with wonder-inducing presentation that makes viewers feel
the vastness and mystery of the universe. Your content sparks curiosity about our place in space.""",
        "user_template": """Enhance this space/astronomy script for maximum engagement on YouTube/TikTok.

ORIGINAL SCRIPT:
{script_json}

REQUIREMENTS:

1. HOOK OPTIMIZATION:
   - Start with a mind-bending scale comparison or cosmic mystery
   - Use: "If Earth were the size of a marble...", "There's a star that...", "We just discovered..."

2. NARRATION ENHANCEMENT:
   - Use scale comparisons to make cosmic concepts relatable
   - Build wonder through progressive revelation
   - Include latest discoveries and missions
   - Connect space facts to human experience

3. IMAGE PROMPT ENHANCEMENT:
   - NASA/ESA quality space imagery
   - Nebulae, galaxies, planetary surfaces, cosmic phenomena
   - Deep space blacks with vibrant cosmic colors

4. VISUAL STYLE: Cosmic wonder, scientific accuracy, deep space aesthetic

5. TIKTOK RETENTION: Include first_frame_hook, mid_video_hook, comment_trigger, loop_structure

OUTPUT FORMAT:
Return ONLY valid JSON with niche ("space-astronomy") and all required fields.""",
    },
    "conspiracy-mysteries": {
        "system": """You are a mysteries and unexplained phenomena content creator who presents
intriguing theories and hidden information in an engaging way. You balance intrigue with
critical thinking, presenting multiple perspectives while keeping viewers captivated.""",
        "user_template": """Enhance this conspiracy/mystery script for maximum engagement on YouTube/TikTok.

ORIGINAL SCRIPT:
{script_json}

REQUIREMENTS:

1. HOOK OPTIMIZATION:
   - Start with a shocking claim or hidden connection
   - Use: "They don't want you to know...", "This was hidden for decades...", "Connect the dots..."

2. NARRATION ENHANCEMENT:
   - Present evidence in compelling sequence
   - Use "revelation" structure that builds to bigger picture
   - Include skeptical counterpoints for credibility
   - End with thought-provoking questions

3. IMAGE PROMPT ENHANCEMENT:
   - Mysterious, shadowy visuals
   - Evidence boards, redacted documents, symbolic imagery
   - Dark green/red color palette with noir shadows

4. VISUAL STYLE: Mysterious, investigative, enigmatic

5. TIKTOK RETENTION: Include first_frame_hook, mid_video_hook, comment_trigger, loop_structure

OUTPUT FORMAT:
Return ONLY valid JSON with niche ("conspiracy-mysteries") and all required fields.""",
    },
    "animal-facts": {
        "system": """You are a wildlife educator who makes animal facts irresistibly fascinating.
You combine scientific accuracy with wonder and humor that makes viewers fall in love with
the animal kingdom. Your content showcases nature's incredible adaptations and behaviors.""",
        "user_template": """Enhance this animal facts script for maximum engagement on YouTube/TikTok.

ORIGINAL SCRIPT:
{script_json}

REQUIREMENTS:

1. HOOK OPTIMIZATION:
   - Start with the most surprising or unbelievable animal fact
   - Use: "This animal can...", "You won't believe what [animal] does...", "Scientists just discovered..."

2. NARRATION ENHANCEMENT:
   - Lead with the "wow factor" of each fact
   - Use relatable comparisons ("That's like a human...")
   - Add personality and humor where appropriate
   - Build to increasingly amazing facts

3. IMAGE PROMPT ENHANCEMENT:
   - BBC Planet Earth quality wildlife photography
   - Animals in action, behavior shots, habitat imagery
   - Rich natural colors, intimate wildlife portraits

4. VISUAL STYLE: Nature documentary, vibrant, wildlife-focused

5. TIKTOK RETENTION: Include first_frame_hook, mid_video_hook, comment_trigger, loop_structure

OUTPUT FORMAT:
Return ONLY valid JSON with niche ("animal-facts") and all required fields.""",
    },
    "health-wellness": {
        "system": """You are a health and wellness educator who makes healthy living accessible
and actionable. You combine evidence-based information with motivating presentation
that empowers viewers to improve their wellbeing. Your content is practical and achievable.""",
        "user_template": """Enhance this health/wellness script for maximum engagement on YouTube/TikTok.

ORIGINAL SCRIPT:
{script_json}

REQUIREMENTS:

1. HOOK OPTIMIZATION:
   - Start with a common health mistake or surprising benefit
   - Use: "Stop doing this to your body...", "The one thing doctors wish you knew...", "Your body is telling you..."

2. NARRATION ENHANCEMENT:
   - Make health tips specific and actionable
   - Include the "why" behind recommendations
   - Use encouraging, non-judgmental tone
   - End with clear takeaway action

3. IMAGE PROMPT ENHANCEMENT:
   - Clean, bright wellness imagery
   - Healthy foods, fitness, nature, self-care moments
   - Fresh greens, clean whites, calming blues

4. VISUAL STYLE: Fresh, healthy, lifestyle-focused

5. TIKTOK RETENTION: Include first_frame_hook, mid_video_hook, comment_trigger, loop_structure

OUTPUT FORMAT:
Return ONLY valid JSON with niche ("health-wellness") and all required fields.""",
    },
    "relationship-advice": {
        "system": """You are a relationship coach who provides insightful, emotionally intelligent advice.
You combine psychology-backed insights with relatable scenarios that help viewers
navigate love, dating, and relationships. Your content is empathetic and actionable.""",
        "user_template": """Enhance this relationship advice script for maximum engagement on YouTube/TikTok.

ORIGINAL SCRIPT:
{script_json}

REQUIREMENTS:

1. HOOK OPTIMIZATION:
   - Start with a relatable relationship scenario or red flag
   - Use: "If they do this, run...", "The sign you're missing...", "Why your relationships always..."

2. NARRATION ENHANCEMENT:
   - Use specific, relatable examples
   - Balance validation with growth-oriented advice
   - Include psychological insights
   - End with empowering message

3. IMAGE PROMPT ENHANCEMENT:
   - Warm, emotionally authentic imagery
   - Couples, intimate moments, emotional scenarios
   - Soft pinks, warm lighting, cozy aesthetics

4. VISUAL STYLE: Warm, authentic, emotionally resonant

5. TIKTOK RETENTION: Include first_frame_hook, mid_video_hook, comment_trigger, loop_structure

OUTPUT FORMAT:
Return ONLY valid JSON with niche ("relationship-advice") and all required fields.""",
    },
    "tech-gadgets": {
        "system": """You are a tech reviewer and gadget enthusiast who makes technology exciting
and accessible. You combine technical knowledge with engaging presentation that helps
viewers understand and desire the latest innovations. Your content is informative yet entertaining.""",
        "user_template": """Enhance this tech/gadgets script for maximum engagement on YouTube/TikTok.

ORIGINAL SCRIPT:
{script_json}

REQUIREMENTS:

1. HOOK OPTIMIZATION:
   - Start with the most impressive feature or capability
   - Use: "This gadget can...", "You've never seen anything like...", "The future is here..."

2. NARRATION ENHANCEMENT:
   - Lead with "wow" features before specs
   - Use relatable use cases
   - Compare to familiar technology
   - Build excitement progressively

3. IMAGE PROMPT ENHANCEMENT:
   - Premium product photography
   - Clean studio shots, feature close-ups
   - Tech blue, clean white, neon accents

4. VISUAL STYLE: Sleek, modern, product-focused

5. TIKTOK RETENTION: Include first_frame_hook, mid_video_hook, comment_trigger, loop_structure

OUTPUT FORMAT:
Return ONLY valid JSON with niche ("tech-gadgets") and all required fields.""",
    },
    "life-hacks": {
        "system": """You are a life hacks expert who shares clever solutions to everyday problems.
You combine practical ingenuity with satisfying demonstrations that make viewers
want to try your tips immediately. Your content is useful, surprising, and shareable.""",
        "user_template": """Enhance this life hacks script for maximum engagement on YouTube/TikTok.

ORIGINAL SCRIPT:
{script_json}

REQUIREMENTS:

1. HOOK OPTIMIZATION:
   - Start with the problem everyone has or the surprising solution
   - Use: "You've been doing this wrong...", "The hack that changes everything...", "Why didn't I know this sooner..."

2. NARRATION ENHANCEMENT:
   - Clear step-by-step when needed
   - Emphasize the "before and after" difference
   - Add the satisfaction factor
   - Include variations or bonus tips

3. IMAGE PROMPT ENHANCEMENT:
   - Clear demonstration imagery
   - Before/after comparisons, step-by-step visuals
   - Bright, practical aesthetic

4. VISUAL STYLE: Bright, practical, demonstration-focused

5. TIKTOK RETENTION: Include first_frame_hook, mid_video_hook, comment_trigger, loop_structure

OUTPUT FORMAT:
Return ONLY valid JSON with niche ("life-hacks") and all required fields.""",
    },
    "mythology-folklore": {
        "system": """You are a mythology storyteller who brings ancient legends to life with epic drama.
You combine scholarly knowledge with captivating narrative that makes gods, heroes, and
mythical creatures feel real and relevant. Your content transports viewers to legendary realms.""",
        "user_template": """Enhance this mythology/folklore script for maximum engagement on YouTube/TikTok.

ORIGINAL SCRIPT:
{script_json}

REQUIREMENTS:

1. HOOK OPTIMIZATION:
   - Start with the most dramatic moment or fascinating creature
   - Use: "In ancient times...", "The gods once...", "This creature could..."

2. NARRATION ENHANCEMENT:
   - Create vivid, epic imagery in narration
   - Connect myths to human nature and modern relevance
   - Build dramatic tension like ancient storytellers
   - End with lasting impact or moral

3. IMAGE PROMPT ENHANCEMENT:
   - Epic mythological artwork style
   - Gods, creatures, legendary scenes
   - Ancient gold, mystical purple, ethereal lighting

4. VISUAL STYLE: Epic, mythological, legendary

5. TIKTOK RETENTION: Include first_frame_hook, mid_video_hook, comment_trigger, loop_structure

OUTPUT FORMAT:
Return ONLY valid JSON with niche ("mythology-folklore") and all required fields.""",
    },
    "unsolved-mysteries": {
        "system": """You are an unsolved mysteries investigator who presents baffling cases that
defy explanation. You combine thorough research with suspenseful presentation that
keeps viewers guessing. Your content respects the unknown while captivating curiosity.""",
        "user_template": """Enhance this unsolved mystery script for maximum engagement on YouTube/TikTok.

ORIGINAL SCRIPT:
{script_json}

REQUIREMENTS:

1. HOOK OPTIMIZATION:
   - Start with the central mystery or most puzzling detail
   - Use: "To this day, no one knows...", "This case has baffled experts...", "The evidence makes no sense..."

2. NARRATION ENHANCEMENT:
   - Present clues that deepen the mystery
   - Include expert theories and their flaws
   - Build suspense through unanswered questions
   - End with the haunting unknown

3. IMAGE PROMPT ENHANCEMENT:
   - Dark, mysterious documentary style
   - Evidence photos, mysterious locations, investigation imagery
   - Cold blues, shadow blacks, aged browns

4. VISUAL STYLE: Mysterious, investigative, unresolved

5. TIKTOK RETENTION: Include first_frame_hook, mid_video_hook, comment_trigger, loop_structure

OUTPUT FORMAT:
Return ONLY valid JSON with niche ("unsolved-mysteries") and all required fields.""",
    },
    "geography-facts": {
        "system": """You are a geography educator who makes our world endlessly fascinating.
You combine geographic knowledge with stunning visuals that make viewers want to explore
every corner of Earth. Your content reveals surprising facts about places and landscapes.""",
        "user_template": """Enhance this geography script for maximum engagement on YouTube/TikTok.

ORIGINAL SCRIPT:
{script_json}

REQUIREMENTS:

1. HOOK OPTIMIZATION:
   - Start with the most surprising geographic fact or comparison
   - Use: "This country is actually...", "You won't believe where...", "The strangest place on Earth..."

2. NARRATION ENHANCEMENT:
   - Use scale comparisons for impact
   - Include human stories connected to places
   - Build from surprising fact to mind-blowing conclusion
   - Connect geography to viewer's world

3. IMAGE PROMPT ENHANCEMENT:
   - Stunning landscape photography
   - Aerial views, maps, geographic features
   - Natural colors, dramatic landscapes

4. VISUAL STYLE: World explorer, stunning landscapes, educational

5. TIKTOK RETENTION: Include first_frame_hook, mid_video_hook, comment_trigger, loop_structure

OUTPUT FORMAT:
Return ONLY valid JSON with niche ("geography-facts") and all required fields.""",
    },
    "ai-future-tech": {
        "system": """You are a futurist and AI expert who makes emerging technology accessible
and exciting. You combine technical understanding with visionary presentation that
helps viewers glimpse tomorrow. Your content balances wonder with realistic assessment.""",
        "user_template": """Enhance this AI/future tech script for maximum engagement on YouTube/TikTok.

ORIGINAL SCRIPT:
{script_json}

REQUIREMENTS:

1. HOOK OPTIMIZATION:
   - Start with the most mind-bending capability or prediction
   - Use: "AI can now...", "By 2030...", "This technology will change..."

2. NARRATION ENHANCEMENT:
   - Make complex tech concepts accessible
   - Include real examples and demonstrations
   - Balance optimism with realistic timelines
   - End with thought-provoking implications

3. IMAGE PROMPT ENHANCEMENT:
   - Futuristic, sci-fi inspired visuals
   - AI interfaces, robots, holographic displays
   - Cyber blue, hologram cyan, chrome accents

4. VISUAL STYLE: Futuristic, technological, visionary

5. TIKTOK RETENTION: Include first_frame_hook, mid_video_hook, comment_trigger, loop_structure

OUTPUT FORMAT:
Return ONLY valid JSON with niche ("ai-future-tech") and all required fields.""",
    },
    "philosophy": {
        "system": """You are a philosophy communicator who makes deep ideas accessible and relevant.
You combine philosophical wisdom with engaging presentation that makes viewers think
differently about life. Your content provides genuine insight without being pretentious.""",
        "user_template": """Enhance this philosophy script for maximum engagement on YouTube/TikTok.

ORIGINAL SCRIPT:
{script_json}

REQUIREMENTS:

1. HOOK OPTIMIZATION:
   - Start with a thought-provoking question or paradox
   - Use: "What if everything you believe is...", "The ancient Greeks knew...", "This question changes everything..."

2. NARRATION ENHANCEMENT:
   - Make abstract concepts concrete with examples
   - Connect philosophy to everyday decisions
   - Build to genuine insight or "aha" moment
   - End with lingering question

3. IMAGE PROMPT ENHANCEMENT:
   - Contemplative, aesthetic imagery
   - Classical references, symbolic visuals, thoughtful scenes
   - Wisdom grey, thought blue, classic warmth

4. VISUAL STYLE: Contemplative, intellectual, timeless

5. TIKTOK RETENTION: Include first_frame_hook, mid_video_hook, comment_trigger, loop_structure

OUTPUT FORMAT:
Return ONLY valid JSON with niche ("philosophy") and all required fields.""",
    },
    "book-summaries": {
        "system": """You are a book content creator who distills powerful ideas from great books.
You combine key insights with engaging presentation that gives viewers the value of
reading without the time investment. Your content inspires further learning.""",
        "user_template": """Enhance this book summary script for maximum engagement on YouTube/TikTok.

ORIGINAL SCRIPT:
{script_json}

REQUIREMENTS:

1. HOOK OPTIMIZATION:
   - Start with the book's most powerful or surprising idea
   - Use: "This book reveals...", "The one idea that...", "[Author] discovered..."

2. NARRATION ENHANCEMENT:
   - Distill to 3-5 key takeaways maximum
   - Use specific examples from the book
   - Make ideas immediately applicable
   - End with compelling reason to apply or read more

3. IMAGE PROMPT ENHANCEMENT:
   - Modern book visualization
   - Book imagery, conceptual illustrations
   - Literary warmth, reading lamp gold

4. VISUAL STYLE: Literary, modern, educational

5. TIKTOK RETENTION: Include first_frame_hook, mid_video_hook, comment_trigger, loop_structure

OUTPUT FORMAT:
Return ONLY valid JSON with niche ("book-summaries") and all required fields.""",
    },
    "celebrity-net-worth": {
        "system": """You are a celebrity wealth analyst who reveals the business behind the fame.
You combine research with entertaining presentation that satisfies curiosity about
celebrity fortunes. Your content is informative and aspirational.""",
        "user_template": """Enhance this celebrity net worth script for maximum engagement on YouTube/TikTok.

ORIGINAL SCRIPT:
{script_json}

REQUIREMENTS:

1. HOOK OPTIMIZATION:
   - Start with the most shocking number or comparison
   - Use: "[Celebrity] makes $X per...", "You won't believe how much...", "From broke to billions..."

2. NARRATION ENHANCEMENT:
   - Use specific, verifiable numbers
   - Break down income sources
   - Include surprising facts about their wealth
   - Compare to relatable amounts

3. IMAGE PROMPT ENHANCEMENT:
   - Glamorous celebrity imagery
   - Wealth indicators, luxury items, red carpet
   - Money green, gold, celebrity glamour

4. VISUAL STYLE: Glamorous, wealthy, celebrity-focused

5. TIKTOK RETENTION: Include first_frame_hook, mid_video_hook, comment_trigger, loop_structure

OUTPUT FORMAT:
Return ONLY valid JSON with niche ("celebrity-net-worth") and all required fields.""",
    },
    "survival-tips": {
        "system": """You are a survival expert who teaches life-saving skills in engaging ways.
You combine practical knowledge with urgent presentation that makes viewers feel
prepared for anything. Your content is actionable and potentially life-saving.""",
        "user_template": """Enhance this survival tips script for maximum engagement on YouTube/TikTok.

ORIGINAL SCRIPT:
{script_json}

REQUIREMENTS:

1. HOOK OPTIMIZATION:
   - Start with a dangerous scenario or crucial mistake
   - Use: "If you ever find yourself...", "This mistake kills...", "The one thing that could save your life..."

2. NARRATION ENHANCEMENT:
   - Make tips specific and memorable
   - Include "why" behind each tip
   - Use urgency without fear-mongering
   - End with actionable takeaway

3. IMAGE PROMPT ENHANCEMENT:
   - Rugged outdoor survival imagery
   - Wilderness scenarios, survival gear, demonstration shots
   - Forest green, survival orange, earth tones

4. VISUAL STYLE: Rugged, practical, outdoor survival

5. TIKTOK RETENTION: Include first_frame_hook, mid_video_hook, comment_trigger, loop_structure

OUTPUT FORMAT:
Return ONLY valid JSON with niche ("survival-tips") and all required fields.""",
    },
    "sleep-relaxation": {
        "system": """You are a sleep and relaxation guide who creates calming, soothing content.
You combine sleep science with peaceful presentation that helps viewers unwind.
Your content is gentle, calming, and genuinely relaxing.""",
        "user_template": """Enhance this sleep/relaxation script for maximum engagement on YouTube/TikTok.

ORIGINAL SCRIPT:
{script_json}

REQUIREMENTS:

1. HOOK OPTIMIZATION:
   - Start with a calming promise or relatable sleep struggle
   - Use: "Can't sleep? Try this...", "The secret to falling asleep in...", "Your mind needs this..."

2. NARRATION ENHANCEMENT:
   - Use slow, calming language
   - Keep sentences gentle and flowing
   - Include breathing cues or relaxation prompts
   - End peacefully

3. IMAGE PROMPT ENHANCEMENT:
   - Peaceful, dreamy imagery
   - Night skies, calm water, soft clouds
   - Sleep blue, peaceful lavender, soft gradients

4. VISUAL STYLE: Peaceful, calming, dreamlike

5. TIKTOK RETENTION: Include first_frame_hook, mid_video_hook, comment_trigger, loop_structure

OUTPUT FORMAT:
Return ONLY valid JSON with niche ("sleep-relaxation") and all required fields.""",
    },
    "netflix-recommendations": {
        "system": """You are a streaming entertainment expert who creates compelling TV and movie
recommendation content. You combine insider knowledge of shows and films with engaging presentation
that makes viewers add titles to their watchlist immediately. Your content helps viewers discover
their next binge-worthy obsession.""",
        "user_template": """Enhance this Netflix/streaming recommendation script for maximum engagement on YouTube/TikTok.

ORIGINAL SCRIPT:
{script_json}

REQUIREMENTS:

1. HOOK OPTIMIZATION:
   - Start with the most compelling hook about the show/movie
   - Use: "Stop scrolling if you...", "The show Netflix is hiding from you...", "You haven't watched this yet?!"

2. NARRATION ENHANCEMENT:
   - Tease plot without major spoilers
   - Mention standout elements (acting, twist, genre-blending)
   - Use comparison hooks ("If you loved X, you'll love this")
   - Build genuine excitement and urgency

3. IMAGE PROMPT ENHANCEMENT:
   - Cinematic, binge-worthy visuals
   - Cozy watching setups, movie poster aesthetics
   - Netflix red, cinema black, screen glow

4. VISUAL STYLE: Entertainment, cinematic, streaming platform aesthetic

5. TIKTOK RETENTION: Include first_frame_hook, mid_video_hook, comment_trigger, loop_structure

OUTPUT FORMAT:
Return ONLY valid JSON with niche ("netflix-recommendations") and all required fields.""",
    },
    "mockumentary-howmade": {
        "system": """You are a comedy writer specializing in absurdist mockumentary content in the style of "How It's Made" parodies.
You transform mundane topics into hilariously over-produced explanations with deadpan delivery.

Your goal: Create content that makes viewers laugh while maintaining the serious documentary narrator tone.

CRITICAL RULES:
1. Maintain deadpan, serious narrator tone throughout - the humor comes from treating absurd things seriously
2. Use authentic "How It's Made" documentary language and pacing
3. Include fake technical jargon and ridiculous made-up facts
4. Add unnecessary precision (e.g., "exactly 47.3 rotations per minute")
5. Reference fictional factories, specialists, and processes
6. Keep segments snappy for TikTok - punch up the absurdity quickly
7. End with a callback or absurd twist

VOICE STYLE: Documentary narrator - calm, informative, completely serious about ridiculous things.
Think: David Attenborough meets Tim Robinson meets actual How It's Made.""",
        "user": """TRANSFORM this content into an absurdist "How It's Made" mockumentary script.

ORIGINAL CONTENT:
{original_script}

REQUIREMENTS:
1. SCRIPT ENHANCEMENT:
   - Add documentary narrator language ("Here at the facility...", "The process begins...")
   - Include fake technical details and ridiculous statistics
   - Add deadpan descriptions of absurd processes
   - Include fictional expert names and factory locations
   - Maintain completely serious tone about insane content
   - Target 45-60 seconds when read aloud

2. COMEDIC ELEMENTS:
   - Fake factory/facility names (e.g., "The Consolidated Thought Processing Plant in Gary, Indiana")
   - Made-up job titles (e.g., "Chief Concept Wrangler")
   - Unnecessary precision in numbers
   - Deadpan delivery of absurd claims
   - Anti-climactic or bizarre endings

3. IMAGE PROMPTS (generate 3-5):
   - Factory/industrial aesthetic
   - Conveyor belt and machinery shots
   - Workers in industrial settings
   - Close-ups of "manufacturing" processes
   - Documentary B-roll style

4. VISUAL STYLE: Industrial documentary, factory footage, How It's Made TV aesthetic

5. TIKTOK RETENTION: Include first_frame_hook, mid_video_hook, comment_trigger, loop_structure

OUTPUT FORMAT:
Return ONLY valid JSON with niche ("mockumentary-howmade") and all required fields.""",
    },
}


def call_gpt(system_prompt: str, user_prompt: str) -> str:
    """
    Call Azure OpenAI GPT API for chat completion.

    Args:
        system_prompt: The system message defining the AI's role
        user_prompt: The user message with the task

    Returns:
        The assistant's response text
    """
    url = (
        f"{AZURE_OPENAI_ENDPOINT}openai/deployments/"
        f"{AZURE_OPENAI_CHAT_DEPLOYMENT}/chat/completions"
        f"?api-version={AZURE_OPENAI_CHAT_API_VERSION}"
    )

    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_OPENAI_KEY,
    }

    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.8,  # Some creativity for engaging content
        "max_tokens": 8000,  # Enough for full script
        "response_format": {"type": "json_object"},  # Ensure JSON response
    }

    logger.info("Calling GPT for enhancement")

    response = requests.post(url, headers=headers, json=payload, timeout=180)
    response.raise_for_status()

    result = response.json()
    return result["choices"][0]["message"]["content"]


def _ensure_engagement_elements(script: dict, niche: str) -> dict:
    """
    Ensure the enhanced script has all required TikTok engagement elements.
    Adds fallback values from the hooks module if elements are missing.

    Args:
        script: The enhanced script dict
        niche: Content niche

    Returns:
        Script dict with guaranteed engagement elements
    """
    if not HOOKS_AVAILABLE:
        # If hooks module not available, just return as-is
        return script

    # Import here to avoid circular imports
    from hooks import (
        get_comment_trigger,
        get_first_frame_hook,
        get_loop_structure,
        get_mid_video_hook,
    )

    # Ensure first_frame_hook exists
    if "first_frame_hook" not in script or not script["first_frame_hook"]:
        hook = get_first_frame_hook(niche)
        script["first_frame_hook"] = {
            "text": hook["text"],
            "type": hook["type"],
        }
        logger.info("Added fallback first-frame hook")

    # Ensure mid_video_hook exists
    if "mid_video_hook" not in script or not script["mid_video_hook"]:
        mid_hook = get_mid_video_hook(niche, hook_format="verbal")
        num_scenes = len(script.get("scenes", []))
        insert_after = max(1, num_scenes // 2 - 1)
        script["mid_video_hook"] = {
            "text": mid_hook["content"],
            "insert_after_scene": insert_after,
        }
        logger.info("Added fallback mid-video hook")

    # Ensure comment_trigger exists
    if "comment_trigger" not in script or not script["comment_trigger"]:
        trigger = get_comment_trigger(niche)
        script["comment_trigger"] = {
            "text": trigger["content"],
            "type": trigger["type"],
        }
        logger.info("Added fallback comment trigger")

    # Ensure loop_structure exists
    if "loop_structure" not in script or not script["loop_structure"]:
        loop = get_loop_structure()
        script["loop_structure"] = {
            "type": loop["type"],
            "description": loop["description"],
        }
        logger.info("Added fallback loop structure")

    return script


def enhance_script(
    script_path: str,
    niche: str,
    output_path: str = None,
    backup_original: bool = True,
) -> str:
    """
    Enhance a script using GPT for maximum engagement.

    Args:
        script_path: Path to the original script JSON
        niche: One of "scary-stories", "finance", "luxury"
        output_path: Optional custom output path (defaults to overwriting original)
        backup_original: Whether to backup the original script

    Returns:
        Path to the enhanced script
    """
    logger.info("Enhancing script", script=os.path.basename(script_path), niche=niche)

    # Load original script
    with open(script_path, encoding="utf-8") as f:
        original_script = json.load(f)

    # Check if already enhanced
    if original_script.get("enhanced_at"):
        logger.info("Script already enhanced, skipping", script=os.path.basename(script_path))
        return script_path

    # Backup original if requested
    if backup_original:
        backup_path = script_path.replace(".json", "_original.json")
        if not os.path.exists(backup_path):
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(original_script, f, indent=2, ensure_ascii=False)
            logger.info("Backup saved", backup=os.path.basename(backup_path))

    # Get enhancement prompts for this niche
    if niche not in ENHANCEMENT_PROMPTS:
        logger.warning("No enhancement prompts for niche, using generic", niche=niche)
        prompts = ENHANCEMENT_PROMPTS["scary-stories"]  # Fallback
    else:
        prompts = ENHANCEMENT_PROMPTS[niche]

    # Build the user prompt with script data
    user_prompt = prompts["user_template"].format(
        script_json=json.dumps(original_script, indent=2),
        source=original_script.get("source", ""),
        author=original_script.get("author", ""),
        url=original_script.get("url", ""),
        created_at=original_script.get("created_at", ""),
        enhanced_at=datetime.now().isoformat(),
    )

    try:
        # Call GPT for enhancement
        enhanced_json = call_gpt(prompts["system"], user_prompt)

        # Parse the response
        enhanced_script = json.loads(enhanced_json)

        # Validate required fields
        if "scenes" not in enhanced_script:
            raise ValueError("Enhanced script missing 'scenes' array")

        # Ensure we have the enhanced_at timestamp
        enhanced_script["enhanced_at"] = datetime.now().isoformat()

        # Ensure engagement elements are present (add fallbacks if missing)
        enhanced_script = _ensure_engagement_elements(enhanced_script, niche)

        # Determine output path
        if output_path is None:
            output_path = script_path

        # Save enhanced script
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(enhanced_script, f, indent=2, ensure_ascii=False)

        logger.info("Enhanced script saved", output_path=output_path, scenes=len(enhanced_script['scenes']))

        if "visual_style" in enhanced_script:
            logger.info("Visual style generated")

        # Report engagement elements
        if "first_frame_hook" in enhanced_script:
            logger.info("Hook generated", hook=enhanced_script['first_frame_hook'].get('text', 'N/A')[:50])
        if "comment_trigger" in enhanced_script:
            logger.info("CTA generated", cta=enhanced_script['comment_trigger'].get('text', 'N/A')[:50])

        return output_path

    except requests.exceptions.RequestException as e:
        response_text = e.response.text[:500] if hasattr(e, "response") and e.response is not None else None
        logger.error("API error during enhancement", error=str(e), response=response_text)
        raise
    except json.JSONDecodeError as e:
        logger.error("JSON parse error", error=str(e), response=enhanced_json[:500])
        raise
    except Exception as e:
        logger.error("Enhancement failed", error=str(e))
        raise


def enhance_scripts_batch(
    script_paths: list,
    niche: str,
) -> list:
    """
    Enhance multiple scripts.

    Args:
        script_paths: List of script file paths
        niche: Content niche

    Returns:
        List of enhanced script paths
    """
    enhanced_paths = []

    for path in script_paths:
        try:
            enhanced_path = enhance_script(path, niche)
            enhanced_paths.append(enhanced_path)
        except Exception as e:
            logger.warning("Skipping script due to error", path=path, error=str(e))
            enhanced_paths.append(path)  # Keep original on failure

    return enhanced_paths


# =============================================================================
# STANDALONE USAGE
# =============================================================================

# All available niches for CLI
ALL_NICHES = [
    "scary-stories",
    "finance",
    "luxury",
    "true-crime",
    "psychology-facts",
    "history",
    "motivation",
    "space-astronomy",
    "conspiracy-mysteries",
    "animal-facts",
    "health-wellness",
    "relationship-advice",
    "tech-gadgets",
    "life-hacks",
    "mythology-folklore",
    "unsolved-mysteries",
    "geography-facts",
    "ai-future-tech",
    "philosophy",
    "book-summaries",
    "celebrity-net-worth",
    "survival-tips",
    "sleep-relaxation",
]

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Enhance scripts for maximum engagement"
    )
    parser.add_argument("script", help="Path to the script JSON file")
    parser.add_argument(
        "--niche",
        "-n",
        choices=ALL_NICHES,
        required=True,
        help="Content niche",
    )
    parser.add_argument(
        "--output", "-o", help="Output path (defaults to overwriting original)"
    )
    parser.add_argument(
        "--no-backup", action="store_true", help="Don't backup the original script"
    )

    args = parser.parse_args()

    enhance_script(
        args.script,
        args.niche,
        output_path=args.output,
        backup_original=not args.no_backup,
    )

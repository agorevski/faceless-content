"""
Script Enhancer Module
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
from datetime import datetime

import requests
from env_config import (
    AZURE_OPENAI_CHAT_API_VERSION,
    AZURE_OPENAI_CHAT_DEPLOYMENT,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
)

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

    print("   🤖 Calling GPT for enhancement...")

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
        print("   🪝 Added fallback first-frame hook")

    # Ensure mid_video_hook exists
    if "mid_video_hook" not in script or not script["mid_video_hook"]:
        mid_hook = get_mid_video_hook(niche, hook_format="verbal")
        num_scenes = len(script.get("scenes", []))
        insert_after = max(1, num_scenes // 2 - 1)
        script["mid_video_hook"] = {
            "text": mid_hook["content"],
            "insert_after_scene": insert_after,
        }
        print("   📍 Added fallback mid-video hook")

    # Ensure comment_trigger exists
    if "comment_trigger" not in script or not script["comment_trigger"]:
        trigger = get_comment_trigger(niche)
        script["comment_trigger"] = {
            "text": trigger["content"],
            "type": trigger["type"],
        }
        print("   💬 Added fallback comment trigger")

    # Ensure loop_structure exists
    if "loop_structure" not in script or not script["loop_structure"]:
        loop = get_loop_structure()
        script["loop_structure"] = {
            "type": loop["type"],
            "description": loop["description"],
        }
        print("   🔄 Added fallback loop structure")

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
    print(f"\n✨ Enhancing script: {os.path.basename(script_path)}")
    print(f"   Niche: {niche}")

    # Load original script
    with open(script_path, encoding="utf-8") as f:
        original_script = json.load(f)

    # Check if already enhanced
    if original_script.get("enhanced_at"):
        print("   ℹ️ Script already enhanced, skipping...")
        return script_path

    # Backup original if requested
    if backup_original:
        backup_path = script_path.replace(".json", "_original.json")
        if not os.path.exists(backup_path):
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(original_script, f, indent=2, ensure_ascii=False)
            print(f"   📋 Backup saved: {os.path.basename(backup_path)}")

    # Get enhancement prompts for this niche
    if niche not in ENHANCEMENT_PROMPTS:
        print(f"   ⚠️ No enhancement prompts for niche: {niche}")
        print("   Using generic enhancement...")
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

        print(f"   ✅ Enhanced script saved: {output_path}")
        print(f"   📊 Scenes: {len(enhanced_script['scenes'])}")

        if "visual_style" in enhanced_script:
            print("   🎨 Visual style: Generated")

        # Report engagement elements
        if "first_frame_hook" in enhanced_script:
            print(
                f"   🪝 Hook: {enhanced_script['first_frame_hook'].get('text', 'N/A')[:50]}..."
            )
        if "comment_trigger" in enhanced_script:
            print(
                f"   💬 CTA: {enhanced_script['comment_trigger'].get('text', 'N/A')[:50]}..."
            )

        return output_path

    except requests.exceptions.RequestException as e:
        print(f"   ❌ API Error: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"   Response: {e.response.text[:500]}")
        raise
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON Parse Error: {e}")
        print(f"   Response was: {enhanced_json[:500]}...")
        raise
    except Exception as e:
        print(f"   ❌ Enhancement failed: {e}")
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
            print(f"   ⚠️ Skipping {path}: {e}")
            enhanced_paths.append(path)  # Keep original on failure

    return enhanced_paths


# =============================================================================
# STANDALONE USAGE
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Enhance scripts for maximum engagement"
    )
    parser.add_argument("script", help="Path to the script JSON file")
    parser.add_argument(
        "--niche",
        "-n",
        choices=["scary-stories", "finance", "luxury"],
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

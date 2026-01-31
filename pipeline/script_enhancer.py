"""
Script Enhancer Module
Uses Azure OpenAI GPT to enhance scripts for maximum engagement on YouTube/TikTok
Focuses on catchy storytelling, visual consistency, and scroll-stopping content
"""

import os
import json
import requests
from datetime import datetime
from typing import Optional
from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_CHAT_DEPLOYMENT,
    AZURE_OPENAI_CHAT_API_VERSION,
    PATHS,
)


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
insider secrets that will change their financial future.""",

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

OUTPUT FORMAT:
Return ONLY valid JSON (no markdown, no explanation) with the enhanced script.""",
    },

    "luxury": {
        "system": """You are a luxury lifestyle content creator who showcases the world's 
most exclusive experiences, products, and lifestyles. Your content makes viewers feel like 
they're getting an exclusive peek into a world of wealth and refinement that they aspire to.""",

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

OUTPUT FORMAT:
Return ONLY valid JSON (no markdown, no explanation) with the enhanced script.""",
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
    with open(script_path, "r", encoding="utf-8") as f:
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
        
        return output_path
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ API Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
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
    parser.add_argument(
        "script",
        help="Path to the script JSON file"
    )
    parser.add_argument(
        "--niche", "-n",
        choices=["scary-stories", "finance", "luxury"],
        required=True,
        help="Content niche"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output path (defaults to overwriting original)"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Don't backup the original script"
    )
    
    args = parser.parse_args()
    
    enhance_script(
        args.script,
        args.niche,
        output_path=args.output,
        backup_original=not args.no_backup,
    )
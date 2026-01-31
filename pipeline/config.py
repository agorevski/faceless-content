"""
Configuration for Faceless Content Pipeline
Replace placeholder values with your actual API keys
"""

# =============================================================================
# AZURE OPENAI CONFIGURATION
# =============================================================================

# Base Azure OpenAI resource
AZURE_OPENAI_ENDPOINT = "https://xxxxx.openai.azure.com/"
AZURE_OPENAI_KEY = "xxxxx"

# Image Generation (GPT-Image-1)
AZURE_OPENAI_IMAGE_DEPLOYMENT = "gpt-image-1"
AZURE_OPENAI_IMAGE_API_VERSION = "2025-04-01-preview"

# Chat/Completion Model for Script Enhancement (GPT-4o or GPT-4o-mini)
# This is used to enhance scripts with better storytelling and image prompts
AZURE_OPENAI_CHAT_DEPLOYMENT = "gpt-4o"  # Change to your deployment name
AZURE_OPENAI_CHAT_API_VERSION = "2024-08-01-preview"

# Text-to-Speech (Azure OpenAI TTS - gpt-4o-mini-tts)
AZURE_OPENAI_TTS_DEPLOYMENT = "gpt-4o-mini-tts"
AZURE_OPENAI_TTS_API_VERSION = "2025-03-01-preview"

# Legacy Azure Speech TTS (not used - keeping for compatibility)
AZURE_TTS_ENDPOINT = ""
AZURE_TTS_KEY = ""
AZURE_TTS_REGION = ""

# =============================================================================
# ELEVENLABS CONFIGURATION (Future - leave empty for now)
# =============================================================================

ELEVENLABS_API_KEY = ""
ELEVENLABS_VOICE_ID = ""  # You'll pick a voice later

# =============================================================================
# VOICE SETTINGS PER NICHE
# =============================================================================

# Azure TTS voices - pick based on style
# Full list: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support

# Azure OpenAI TTS voice options: alloy, echo, fable, onyx, nova, shimmer
# For scary stories: "onyx" (deep, serious) or "fable" (dramatic)
# For finance: "onyx" (authoritative) or "alloy" (neutral professional)
# For luxury: "nova" (warm, sophisticated) or "shimmer" (elegant)

VOICE_SETTINGS = {
    "scary-stories": {
        "openai_voice": "onyx",  # Deep, serious male voice - perfect for horror
        "openai_speed": 0.9,  # Slightly slower for tension (0.25 to 4.0)
        "elevenlabs_voice_id": "",  # Fill later
    },
    "finance": {
        "openai_voice": "onyx",  # Authoritative, trustworthy
        "openai_speed": 1.0,  # Normal pace
        "elevenlabs_voice_id": "",
    },
    "luxury": {
        "openai_voice": "nova",  # Warm, sophisticated female voice
        "openai_speed": 0.95,  # Slightly slower, elegant
        "elevenlabs_voice_id": "",
    },
}

# =============================================================================
# IMAGE GENERATION SETTINGS PER NICHE
# =============================================================================

# GPT-Image-1 supported sizes: 1024x1024, 1024x1536, 1536x1024, auto
IMAGE_SETTINGS = {
    "scary-stories": {
        "style": "dark cinematic horror",
        "color_palette": "dark blue, black, deep red, shadows",
        "quality": "high",
        "size": "1536x1024",  # Landscape for YouTube (closest to 16:9)
        "size_tiktok": "1024x1536",  # Portrait for TikTok (9:16)
        # Enhanced prompt engineering for high-quality horror imagery
        "prompt_template": {
            "prefix": "Cinematic still from a prestige A24-style horror film, shot on 35mm film with anamorphic lens.",
            "photography": "Shallow depth of field, masterful composition following rule of thirds, atmospheric perspective.",
            "lighting": "Diffused volumetric lighting, deep shadows with subtle rim lighting, god rays through fog or canopy.",
            "color_grading": "Desaturated color palette with deep teal shadows and muted amber/sepia highlights, film grain texture.",
            "mood": "Overwhelming sense of dread, liminal space aesthetic, uncanny valley atmosphere, isolated and oppressive.",
            "quality_suffix": "Photorealistic, 8K resolution, hyperdetailed, award-winning cinematography, Denis Villeneuve meets Ari Aster visual style.",
            "artistic_references": "Visual style inspired by Roger Deakins cinematography, Zdzisław Beksiński surrealist horror, and Simon Stålenhag's eerie atmosphere.",
        },
        # Default visual continuity elements (can be overridden in script JSON)
        "default_visual_style": {
            "environment": "Dense old-growth forest with towering ancient trees, thick atmospheric fog, perpetual twilight or overcast.",
            "color_mood": "Cold, desaturated blues and teals dominating shadows, with occasional warm amber highlights creating unease.",
            "texture": "Weathered wood, moss-covered surfaces, mist-dampened everything, organic decay meeting unnatural perfection.",
        },
    },
    "finance": {
        "style": "clean professional modern",
        "color_palette": "green, gold, white, navy blue",
        "quality": "high",
        "size": "1536x1024",
        "size_tiktok": "1024x1536",
    },
    "luxury": {
        "style": "cinematic luxury elegant",
        "color_palette": "gold, black, white, champagne",
        "quality": "high",
        "size": "1536x1024",
        "size_tiktok": "1024x1536",
    },
}

# =============================================================================
# OUTPUT SETTINGS
# =============================================================================

OUTPUT_SETTINGS = {
    "youtube": {
        "resolution": "1920x1080",
        "fps": 30,
        "format": "mp4",
        "codec": "libx264",
    },
    "tiktok": {
        "resolution": "1080x1920",
        "fps": 30,
        "format": "mp4",
        "codec": "libx264",
    },
}

# =============================================================================
# PATHS
# =============================================================================

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PATHS = {
    "scary-stories": {
        "scripts": os.path.join(BASE_DIR, "scary-stories", "scripts"),
        "images": os.path.join(BASE_DIR, "scary-stories", "images"),
        "audio": os.path.join(BASE_DIR, "scary-stories", "audio"),
        "videos": os.path.join(BASE_DIR, "scary-stories", "videos"),
        "output": os.path.join(BASE_DIR, "scary-stories", "output"),
    },
    "finance": {
        "scripts": os.path.join(BASE_DIR, "finance", "scripts"),
        "images": os.path.join(BASE_DIR, "finance", "images"),
        "audio": os.path.join(BASE_DIR, "finance", "audio"),
        "videos": os.path.join(BASE_DIR, "finance", "videos"),
        "output": os.path.join(BASE_DIR, "finance", "output"),
    },
    "luxury": {
        "scripts": os.path.join(BASE_DIR, "luxury", "scripts"),
        "images": os.path.join(BASE_DIR, "luxury", "images"),
        "audio": os.path.join(BASE_DIR, "luxury", "audio"),
        "videos": os.path.join(BASE_DIR, "luxury", "videos"),
        "output": os.path.join(BASE_DIR, "luxury", "output"),
    },
    "shared": {
        "templates": os.path.join(BASE_DIR, "shared", "templates"),
        "prompts": os.path.join(BASE_DIR, "shared", "prompts"),
        "music": os.path.join(BASE_DIR, "shared", "music"),
    },
}

# =============================================================================
# USE ELEVENLABS INSTEAD OF AZURE?
# =============================================================================

USE_ELEVENLABS = False  # Set to True when you get ElevenLabs API key

"""
Image Generation Prompt Templates and Settings.

This module contains per-niche image generation settings including:
- Image sizes for different platforms
- Visual style configurations
- Cinematographic prompt engineering templates
- Default visual continuity elements
"""

from typing import Any

# =============================================================================
# SCARY STORIES - Cinematic Horror Style
# =============================================================================

SCARY_STORIES_IMAGE_SETTINGS: dict[str, Any] = {
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
}

# =============================================================================
# FINANCE - Clean Professional Modern Style
# =============================================================================

FINANCE_IMAGE_SETTINGS: dict[str, Any] = {
    "style": "clean professional modern",
    "color_palette": "green, gold, white, navy blue",
    "quality": "high",
    "size": "1536x1024",
    "size_tiktok": "1024x1536",
    # Prompt engineering for finance content
    "prompt_template": {
        "prefix": "Professional stock photography style, clean modern aesthetic.",
        "photography": "Sharp focus, even lighting, clean composition.",
        "lighting": "Bright, professional studio lighting or natural daylight.",
        "color_grading": "Clean, vibrant colors with professional color balance.",
        "mood": "Trustworthy, authoritative, aspirational yet accessible.",
        "quality_suffix": "High resolution, professional photography, corporate quality.",
        "artistic_references": "Bloomberg, Forbes, modern fintech marketing style.",
    },
    "default_visual_style": {
        "environment": "Modern office spaces, clean data visualizations, urban professional settings.",
        "color_mood": "Trust-inspiring greens, gold accents for wealth, clean whites and navy blues.",
        "texture": "Polished surfaces, modern materials, clean lines.",
    },
}

# =============================================================================
# LUXURY - Cinematic Elegance Style
# =============================================================================

LUXURY_IMAGE_SETTINGS: dict[str, Any] = {
    "style": "cinematic luxury elegant",
    "color_palette": "gold, black, white, champagne",
    "quality": "high",
    "size": "1536x1024",
    "size_tiktok": "1024x1536",
    # Prompt engineering for luxury content
    "prompt_template": {
        "prefix": "Ultra-luxury lifestyle photography, magazine-quality editorial style.",
        "photography": "Perfect composition, elegant framing, aspirational perspective.",
        "lighting": "Soft, flattering lighting with golden hour warmth, dramatic shadows.",
        "color_grading": "Rich, warm tones with gold and champagne highlights, deep blacks.",
        "mood": "Exclusive, sophisticated, aspirational, refined elegance.",
        "quality_suffix": "Ultra high resolution, magazine editorial quality, luxury brand aesthetic.",
        "artistic_references": "Vogue, Architectural Digest, luxury brand campaigns, yacht lifestyle.",
    },
    "default_visual_style": {
        "environment": "Exclusive venues, yacht interiors, private jets, luxury estates, five-star settings.",
        "color_mood": "Gold and champagne warmth, rich blacks, pristine whites, jewel tone accents.",
        "texture": "Fine leather, polished marble, crystal, silk, precious metals.",
    },
}

# =============================================================================
# TRUE CRIME - Documentary Investigation Style
# =============================================================================

TRUE_CRIME_IMAGE_SETTINGS: dict[str, Any] = {
    "style": "dark documentary investigative",
    "color_palette": "muted colors, noir shadows, police blue, crime scene yellow",
    "quality": "high",
    "size": "1536x1024",
    "size_tiktok": "1024x1536",
    "prompt_template": {
        "prefix": "Documentary-style still from a true crime investigation series, shot with gritty realism.",
        "photography": "Handheld documentary feel, natural framing, investigative perspective.",
        "lighting": "Low-key lighting, harsh shadows, neon accents, street lighting at night.",
        "color_grading": "Desaturated with cold blue undertones, high contrast, film noir influence.",
        "mood": "Tense, investigative, unsettling, journalistic authenticity.",
        "quality_suffix": "Photorealistic, documentary quality, crime investigation aesthetic.",
        "artistic_references": "Netflix true crime documentary style, Mindhunter visual aesthetic.",
    },
    "default_visual_style": {
        "environment": "Urban crime scenes, interrogation rooms, evidence boards, dimly lit streets.",
        "color_mood": "Cold blues, harsh whites, police tape yellow, evidence marker orange.",
        "texture": "Worn paper, grainy photographs, worn surfaces, institutional spaces.",
    },
}

# =============================================================================
# PSYCHOLOGY FACTS - Clean Educational Style
# =============================================================================

PSYCHOLOGY_FACTS_IMAGE_SETTINGS: dict[str, Any] = {
    "style": "clean educational scientific",
    "color_palette": "purple, teal, white, soft gradients",
    "quality": "high",
    "size": "1536x1024",
    "size_tiktok": "1024x1536",
    "prompt_template": {
        "prefix": "Modern educational infographic style, clean scientific visualization.",
        "photography": "Clean composition, centered subjects, professional educational aesthetic.",
        "lighting": "Soft, even lighting with subtle gradients.",
        "color_grading": "Vibrant but professional, clean whites, accent colors.",
        "mood": "Intellectual, curious, enlightening, accessible science.",
        "quality_suffix": "High resolution, modern infographic quality, educational clarity.",
        "artistic_references": "TED-Ed visual style, modern psychology textbook illustrations.",
    },
    "default_visual_style": {
        "environment": "Abstract brain imagery, human silhouettes, conceptual psychology visuals.",
        "color_mood": "Calm purples and teals, white space, clean gradients.",
        "texture": "Smooth gradients, clean lines, minimal texture.",
    },
}

# =============================================================================
# HISTORY - Epic Historical Documentary Style
# =============================================================================

HISTORY_IMAGE_SETTINGS: dict[str, Any] = {
    "style": "epic historical cinematic",
    "color_palette": "sepia, bronze, aged parchment, deep earth tones",
    "quality": "high",
    "size": "1536x1024",
    "size_tiktok": "1024x1536",
    "prompt_template": {
        "prefix": "Epic historical documentary cinematography, museum-quality historical recreation.",
        "photography": "Grand composition, historical accuracy, sweeping perspectives.",
        "lighting": "Natural period-appropriate lighting, candlelight for interiors, dramatic skies.",
        "color_grading": "Warm sepia tones, aged photograph aesthetic, rich earth colors.",
        "mood": "Majestic, educational, awe-inspiring, timeless grandeur.",
        "quality_suffix": "Photorealistic historical recreation, documentary quality.",
        "artistic_references": "BBC History documentaries, National Geographic historical recreations.",
    },
    "default_visual_style": {
        "environment": "Ancient monuments, historical battlefields, period architecture, artifacts.",
        "color_mood": "Warm sepia and bronze, aged parchment tones, dramatic shadows.",
        "texture": "Weathered stone, aged wood, antique materials, historical authenticity.",
    },
}

# =============================================================================
# MOTIVATION - Inspirational Empowering Style
# =============================================================================

MOTIVATION_IMAGE_SETTINGS: dict[str, Any] = {
    "style": "inspirational empowering dynamic",
    "color_palette": "sunrise orange, powerful red, gold, deep blue",
    "quality": "high",
    "size": "1536x1024",
    "size_tiktok": "1024x1536",
    "prompt_template": {
        "prefix": "Inspirational photography, empowering visual storytelling, peak moment capture.",
        "photography": "Dynamic angles, hero shots, aspirational framing.",
        "lighting": "Golden hour warmth, dramatic backlighting, powerful rim lighting.",
        "color_grading": "Warm, vibrant, high contrast, sunrise/sunset tones.",
        "mood": "Empowering, uplifting, determined, victorious.",
        "quality_suffix": "High resolution, motivational poster quality, inspirational impact.",
        "artistic_references": "Nike campaign aesthetics, TED Talk visuals, success imagery.",
    },
    "default_visual_style": {
        "environment": "Mountain peaks, sunrise vistas, athletic achievements, success moments.",
        "color_mood": "Warm oranges and golds, powerful reds, triumphant lighting.",
        "texture": "Dynamic movement, sharp focus on achievement, aspirational scenes.",
    },
}

# =============================================================================
# SPACE & ASTRONOMY - Cosmic Wonder Style
# =============================================================================

SPACE_ASTRONOMY_IMAGE_SETTINGS: dict[str, Any] = {
    "style": "cosmic wonder scientific",
    "color_palette": "deep space purple, nebula pink, star white, cosmic blue",
    "quality": "high",
    "size": "1536x1024",
    "size_tiktok": "1024x1536",
    "prompt_template": {
        "prefix": "NASA-quality space photography, cosmic wonder visualization, astronomical precision.",
        "photography": "Vast cosmic scales, detailed celestial bodies, awe-inspiring perspectives.",
        "lighting": "Starlight illumination, planetary lighting, cosmic radiation glow.",
        "color_grading": "Deep space blacks, vibrant nebula colors, stellar highlights.",
        "mood": "Awe-inspiring, mysterious, scientifically fascinating, cosmic wonder.",
        "quality_suffix": "Ultra high resolution, NASA/ESA quality, scientifically accurate.",
        "artistic_references": "Hubble Space Telescope imagery, James Webb visuals, NASA visualization.",
    },
    "default_visual_style": {
        "environment": "Deep space, planetary surfaces, nebulae, galaxies, cosmic phenomena.",
        "color_mood": "Deep purples and blues, vibrant nebula pinks, brilliant starlight.",
        "texture": "Cosmic dust, planetary surfaces, stellar phenomena, space textures.",
    },
}

# =============================================================================
# CONSPIRACY & MYSTERIES - Dark Enigmatic Style
# =============================================================================

CONSPIRACY_MYSTERIES_IMAGE_SETTINGS: dict[str, Any] = {
    "style": "dark enigmatic mysterious",
    "color_palette": "dark green, conspiracy red, shadowy black, illuminati gold",
    "quality": "high",
    "size": "1536x1024",
    "size_tiktok": "1024x1536",
    "prompt_template": {
        "prefix": "Mysterious documentary style, hidden truth aesthetic, enigmatic visualization.",
        "photography": "Shadowy compositions, revealing angles, hidden detail emphasis.",
        "lighting": "Dramatic shadows, selective illumination, spotlight reveals.",
        "color_grading": "Dark, desaturated with green/red accents, noir influence.",
        "mood": "Mysterious, thought-provoking, revelatory, unsettling truth.",
        "quality_suffix": "High quality, mysterious atmosphere, conspiracy documentary style.",
        "artistic_references": "X-Files visual style, conspiracy documentary aesthetics.",
    },
    "default_visual_style": {
        "environment": "Secret facilities, hidden symbols, redacted documents, shadowy meetings.",
        "color_mood": "Dark greens and reds, shadowy blacks, occasional gold accents.",
        "texture": "Classified documents, mysterious symbols, hidden evidence.",
    },
}

# =============================================================================
# ANIMAL FACTS - Nature Documentary Style
# =============================================================================

ANIMAL_FACTS_IMAGE_SETTINGS: dict[str, Any] = {
    "style": "nature documentary wildlife",
    "color_palette": "natural greens, earth browns, vibrant wildlife colors",
    "quality": "high",
    "size": "1536x1024",
    "size_tiktok": "1024x1536",
    "prompt_template": {
        "prefix": "BBC Planet Earth quality wildlife photography, nature documentary cinematography.",
        "photography": "Intimate wildlife portraits, behavior capture, natural habitat framing.",
        "lighting": "Natural lighting, golden hour wildlife, dappled forest light.",
        "color_grading": "Rich natural colors, vibrant wildlife tones, organic warmth.",
        "mood": "Wonder at nature, educational fascination, respect for wildlife.",
        "quality_suffix": "Ultra high resolution, National Geographic quality, wildlife photography.",
        "artistic_references": "David Attenborough documentaries, National Geographic wildlife.",
    },
    "default_visual_style": {
        "environment": "Natural habitats, wildlife in action, pristine ecosystems.",
        "color_mood": "Lush greens, earth tones, vibrant animal colors.",
        "texture": "Fur, feathers, scales, natural textures, organic materials.",
    },
}

# =============================================================================
# HEALTH & WELLNESS - Clean Lifestyle Style
# =============================================================================

HEALTH_WELLNESS_IMAGE_SETTINGS: dict[str, Any] = {
    "style": "clean wellness lifestyle",
    "color_palette": "fresh green, clean white, calming blue, natural tones",
    "quality": "high",
    "size": "1536x1024",
    "size_tiktok": "1024x1536",
    "prompt_template": {
        "prefix": "Clean wellness lifestyle photography, health-focused visual content.",
        "photography": "Bright, airy compositions, healthy lifestyle imagery.",
        "lighting": "Soft natural light, bright and welcoming, clean illumination.",
        "color_grading": "Fresh, vibrant, clean whites, natural color balance.",
        "mood": "Healthy, energizing, balanced, achievable wellness.",
        "quality_suffix": "High resolution, lifestyle magazine quality, wellness aesthetic.",
        "artistic_references": "Wellness magazine aesthetics, healthy lifestyle campaigns.",
    },
    "default_visual_style": {
        "environment": "Clean kitchens, fitness spaces, nature settings, healthy foods.",
        "color_mood": "Fresh greens, clean whites, calming blues, natural warmth.",
        "texture": "Fresh produce, clean surfaces, natural materials, organic textures.",
    },
}

# =============================================================================
# RELATIONSHIP ADVICE - Warm Emotional Style
# =============================================================================

RELATIONSHIP_ADVICE_IMAGE_SETTINGS: dict[str, Any] = {
    "style": "warm emotional authentic",
    "color_palette": "warm pink, soft rose, intimate lighting, cozy tones",
    "quality": "high",
    "size": "1536x1024",
    "size_tiktok": "1024x1536",
    "prompt_template": {
        "prefix": "Authentic emotional photography, intimate relationship moments, genuine connection.",
        "photography": "Intimate framing, emotional authenticity, relatable scenarios.",
        "lighting": "Warm, soft lighting, intimate atmosphere, romantic glow.",
        "color_grading": "Warm tones, soft contrast, romantic color palette.",
        "mood": "Emotionally authentic, relatable, supportive, understanding.",
        "quality_suffix": "High quality, emotionally resonant, authentic lifestyle.",
        "artistic_references": "Relationship blog aesthetics, emotional storytelling imagery.",
    },
    "default_visual_style": {
        "environment": "Cozy interiors, intimate moments, everyday relationship scenes.",
        "color_mood": "Warm pinks and roses, soft lighting, intimate tones.",
        "texture": "Soft fabrics, warm interiors, authentic lived-in spaces.",
    },
}

# =============================================================================
# TECH & GADGETS - Modern Tech Review Style
# =============================================================================

TECH_GADGETS_IMAGE_SETTINGS: dict[str, Any] = {
    "style": "modern tech sleek",
    "color_palette": "tech blue, clean white, accent neon, dark mode black",
    "quality": "high",
    "size": "1536x1024",
    "size_tiktok": "1024x1536",
    "prompt_template": {
        "prefix": "Premium tech product photography, modern gadget showcase, sleek technology.",
        "photography": "Product hero shots, detail close-ups, tech-forward angles.",
        "lighting": "Studio product lighting, clean highlights, accent lighting.",
        "color_grading": "Clean, modern, high contrast, tech aesthetic.",
        "mood": "Innovative, cutting-edge, desirable, future-forward.",
        "quality_suffix": "Ultra high resolution, Apple-quality product photography.",
        "artistic_references": "Apple product launches, MKBHD review aesthetics, tech magazines.",
    },
    "default_visual_style": {
        "environment": "Clean product displays, modern tech setups, minimal backgrounds.",
        "color_mood": "Tech blues, clean whites, dark mode accents, neon highlights.",
        "texture": "Polished metal, premium glass, sleek plastics, precision engineering.",
    },
}

# =============================================================================
# LIFE HACKS - Practical DIY Style
# =============================================================================

LIFE_HACKS_IMAGE_SETTINGS: dict[str, Any] = {
    "style": "practical DIY helpful",
    "color_palette": "bright yellow, action orange, clean white, practical colors",
    "quality": "high",
    "size": "1536x1024",
    "size_tiktok": "1024x1536",
    "prompt_template": {
        "prefix": "Practical demonstration photography, clear how-to visualization, helpful imagery.",
        "photography": "Clear step-by-step framing, practical angles, instructional clarity.",
        "lighting": "Bright, even lighting, clear visibility, no shadows on subject.",
        "color_grading": "Bright, cheerful, high visibility, practical aesthetic.",
        "mood": "Helpful, practical, clever, satisfying solutions.",
        "quality_suffix": "High resolution, instructional quality, clear demonstration.",
        "artistic_references": "5-Minute Crafts aesthetics, practical DIY tutorials.",
    },
    "default_visual_style": {
        "environment": "Home settings, everyday objects, before/after demonstrations.",
        "color_mood": "Bright yellows and oranges, clean whites, practical tones.",
        "texture": "Everyday materials, practical objects, relatable settings.",
    },
}

# =============================================================================
# MYTHOLOGY & FOLKLORE - Epic Fantasy Style
# =============================================================================

MYTHOLOGY_FOLKLORE_IMAGE_SETTINGS: dict[str, Any] = {
    "style": "epic fantasy mythological",
    "color_palette": "ancient gold, mystical purple, ethereal blue, legendary colors",
    "quality": "high",
    "size": "1536x1024",
    "size_tiktok": "1024x1536",
    "prompt_template": {
        "prefix": "Epic mythological artwork, legendary creature visualization, ancient story illustration.",
        "photography": "Grand mythological compositions, legendary scale, epic framing.",
        "lighting": "Ethereal godly lighting, mystical glow, dramatic atmosphere.",
        "color_grading": "Rich mythological colors, ancient gold, mystical purples.",
        "mood": "Legendary, awe-inspiring, mystical, ancient wonder.",
        "quality_suffix": "Ultra high resolution, museum-quality mythological art.",
        "artistic_references": "Greek mythology art, Norse legend illustrations, fantasy concept art.",
    },
    "default_visual_style": {
        "environment": "Ancient temples, mythological landscapes, legendary creatures.",
        "color_mood": "Ancient golds, mystical purples, ethereal blues.",
        "texture": "Ancient stone, mystical energy, legendary materials.",
    },
}

# =============================================================================
# UNSOLVED MYSTERIES - Dark Investigation Style
# =============================================================================

UNSOLVED_MYSTERIES_IMAGE_SETTINGS: dict[str, Any] = {
    "style": "dark investigation mysterious",
    "color_palette": "mystery blue, case file brown, evidence yellow, shadow black",
    "quality": "high",
    "size": "1536x1024",
    "size_tiktok": "1024x1536",
    "prompt_template": {
        "prefix": "Unsolved case documentary style, mysterious investigation, unresolved tension.",
        "photography": "Evidence-focused framing, mystery atmosphere, investigative angles.",
        "lighting": "Low-key dramatic lighting, selective illumination, noir shadows.",
        "color_grading": "Desaturated mystery tones, cold blues, aged document browns.",
        "mood": "Mysterious, unresolved, haunting, questions unanswered.",
        "quality_suffix": "Documentary quality, mystery investigation aesthetic.",
        "artistic_references": "Unsolved Mysteries TV show, cold case documentary style.",
    },
    "default_visual_style": {
        "environment": "Case files, mysterious locations, evidence boards, abandoned scenes.",
        "color_mood": "Cold mystery blues, aged browns, evidence yellows.",
        "texture": "Aged documents, worn evidence, mysterious locations.",
    },
}

# =============================================================================
# GEOGRAPHY FACTS - World Explorer Style
# =============================================================================

GEOGRAPHY_FACTS_IMAGE_SETTINGS: dict[str, Any] = {
    "style": "world explorer educational",
    "color_palette": "map brown, ocean blue, terrain green, earth tones",
    "quality": "high",
    "size": "1536x1024",
    "size_tiktok": "1024x1536",
    "prompt_template": {
        "prefix": "World geography visualization, stunning landscape photography, educational exploration.",
        "photography": "Sweeping landscape vistas, aerial perspectives, geographic detail.",
        "lighting": "Natural geographic lighting, dramatic landscapes, varied conditions.",
        "color_grading": "Rich natural colors, geographic accuracy, earth tones.",
        "mood": "Exploratory wonder, educational fascination, world discovery.",
        "quality_suffix": "Ultra high resolution, National Geographic quality.",
        "artistic_references": "National Geographic photography, world atlas visualizations.",
    },
    "default_visual_style": {
        "environment": "Stunning landscapes, geographic features, world locations, maps.",
        "color_mood": "Ocean blues, terrain greens, earth browns, sky variations.",
        "texture": "Natural landscapes, geographic features, terrain textures.",
    },
}

# =============================================================================
# AI & FUTURE TECH - Futuristic Sci-Fi Style
# =============================================================================

AI_FUTURE_TECH_IMAGE_SETTINGS: dict[str, Any] = {
    "style": "futuristic sci-fi technological",
    "color_palette": "cyber blue, AI purple, hologram cyan, future chrome",
    "quality": "high",
    "size": "1536x1024",
    "size_tiktok": "1024x1536",
    "prompt_template": {
        "prefix": "Futuristic technology visualization, AI concept art, near-future sci-fi.",
        "photography": "Cutting-edge tech aesthetics, futuristic angles, sci-fi atmosphere.",
        "lighting": "Holographic lighting, neon accents, futuristic illumination.",
        "color_grading": "Cyber blues and purples, hologram effects, chrome highlights.",
        "mood": "Futuristic wonder, technological possibility, AI revolution.",
        "quality_suffix": "Ultra high resolution, concept art quality, futuristic visualization.",
        "artistic_references": "Blade Runner aesthetics, modern sci-fi concept art, AI visualizations.",
    },
    "default_visual_style": {
        "environment": "Futuristic cities, AI interfaces, robotic systems, tech landscapes.",
        "color_mood": "Cyber blues, AI purples, hologram cyans, chrome accents.",
        "texture": "Holographic surfaces, sleek metals, digital interfaces.",
    },
}

# =============================================================================
# PHILOSOPHY - Contemplative Aesthetic Style
# =============================================================================

PHILOSOPHY_IMAGE_SETTINGS: dict[str, Any] = {
    "style": "contemplative aesthetic intellectual",
    "color_palette": "wisdom grey, thought blue, parchment cream, classic tones",
    "quality": "high",
    "size": "1536x1024",
    "size_tiktok": "1024x1536",
    "prompt_template": {
        "prefix": "Contemplative philosophical imagery, intellectual visual metaphors, deep thought aesthetic.",
        "photography": "Thoughtful compositions, symbolic framing, intellectual atmosphere.",
        "lighting": "Soft contemplative lighting, library warmth, study atmosphere.",
        "color_grading": "Muted intellectual tones, classic warmth, timeless aesthetic.",
        "mood": "Contemplative, intellectual, thought-provoking, timeless wisdom.",
        "quality_suffix": "High resolution, artistic quality, philosophical depth.",
        "artistic_references": "Classical philosophy imagery, School of Athens aesthetic, intellectual art.",
    },
    "default_visual_style": {
        "environment": "Libraries, study spaces, nature contemplation, symbolic imagery.",
        "color_mood": "Wisdom greys, thought blues, warm parchment tones.",
        "texture": "Aged books, classic materials, contemplative spaces.",
    },
}

# =============================================================================
# BOOK SUMMARIES - Literary Educational Style
# =============================================================================

BOOK_SUMMARIES_IMAGE_SETTINGS: dict[str, Any] = {
    "style": "literary educational modern",
    "color_palette": "book brown, reading lamp gold, page cream, accent colors",
    "quality": "high",
    "size": "1536x1024",
    "size_tiktok": "1024x1536",
    "prompt_template": {
        "prefix": "Modern book visualization, literary concept art, reading-focused imagery.",
        "photography": "Book-centered compositions, literary atmosphere, educational clarity.",
        "lighting": "Reading lamp warmth, library lighting, inviting atmosphere.",
        "color_grading": "Warm literary tones, book-inspired colors, readable aesthetic.",
        "mood": "Intellectually engaging, inviting, knowledge-focused, accessible.",
        "quality_suffix": "High resolution, modern publishing quality, literary aesthetic.",
        "artistic_references": "Modern book cover design, Blinkist visual style, literary magazines.",
    },
    "default_visual_style": {
        "environment": "Cozy reading spaces, book stacks, conceptual book themes.",
        "color_mood": "Warm book browns, reading lamp golds, page cream tones.",
        "texture": "Book pages, leather bindings, cozy reading textures.",
    },
}

# =============================================================================
# CELEBRITY NET WORTH - Glamorous Wealth Style
# =============================================================================

CELEBRITY_NET_WORTH_IMAGE_SETTINGS: dict[str, Any] = {
    "style": "glamorous wealth celebrity",
    "color_palette": "money green, gold, paparazzi flash, celebrity red",
    "quality": "high",
    "size": "1536x1024",
    "size_tiktok": "1024x1536",
    "prompt_template": {
        "prefix": "Celebrity lifestyle photography, wealth visualization, red carpet glamour.",
        "photography": "Glamorous framing, wealth indicators, celebrity atmosphere.",
        "lighting": "Red carpet lighting, glamorous highlights, wealth showcase.",
        "color_grading": "Rich, saturated, wealth-indicating colors, celebrity glow.",
        "mood": "Glamorous, aspirational, celebrity lifestyle, wealth display.",
        "quality_suffix": "High resolution, entertainment magazine quality, celebrity aesthetic.",
        "artistic_references": "Forbes celebrity photography, entertainment magazine style.",
    },
    "default_visual_style": {
        "environment": "Mansions, luxury cars, red carpets, wealth indicators.",
        "color_mood": "Money greens, rich golds, celebrity reds, luxury tones.",
        "texture": "Luxury materials, celebrity lifestyle, wealth textures.",
    },
}

# =============================================================================
# SURVIVAL TIPS - Rugged Outdoor Style
# =============================================================================

SURVIVAL_TIPS_IMAGE_SETTINGS: dict[str, Any] = {
    "style": "rugged outdoor survival",
    "color_palette": "forest green, survival orange, earth brown, tactical tan",
    "quality": "high",
    "size": "1536x1024",
    "size_tiktok": "1024x1536",
    "prompt_template": {
        "prefix": "Survival scenario photography, wilderness skills demonstration, outdoor rugged aesthetic.",
        "photography": "Practical survival framing, outdoor conditions, demonstration angles.",
        "lighting": "Natural outdoor lighting, campfire glow, wilderness atmosphere.",
        "color_grading": "Natural rugged tones, survival aesthetic, outdoor colors.",
        "mood": "Prepared, capable, wilderness-ready, survival focused.",
        "quality_suffix": "High resolution, outdoor documentary quality, survival aesthetic.",
        "artistic_references": "Bear Grylls show aesthetics, survival documentary style.",
    },
    "default_visual_style": {
        "environment": "Wilderness settings, survival scenarios, outdoor skills.",
        "color_mood": "Forest greens, survival oranges, earth browns.",
        "texture": "Natural materials, survival gear, rugged outdoor textures.",
    },
}

# =============================================================================
# SLEEP & RELAXATION - Calm Ambient Style
# =============================================================================

SLEEP_RELAXATION_IMAGE_SETTINGS: dict[str, Any] = {
    "style": "calm ambient peaceful",
    "color_palette": "sleep blue, peaceful lavender, cloud white, dream gradients",
    "quality": "high",
    "size": "1536x1024",
    "size_tiktok": "1024x1536",
    "prompt_template": {
        "prefix": "Peaceful ambient imagery, calming sleep visualization, relaxation aesthetic.",
        "photography": "Soft, dreamy compositions, peaceful framing, calming perspectives.",
        "lighting": "Soft twilight, peaceful glow, calming ambient light.",
        "color_grading": "Soft pastels, calming blues, dreamy gradients, peaceful tones.",
        "mood": "Deeply calming, peaceful, sleep-inducing, tranquil.",
        "quality_suffix": "High resolution, ambient quality, meditation aesthetic.",
        "artistic_references": "Calm app aesthetics, sleep app visuals, meditation imagery.",
    },
    "default_visual_style": {
        "environment": "Peaceful nature, night skies, calming interiors, dream imagery.",
        "color_mood": "Sleep blues, peaceful lavenders, soft whites, dream gradients.",
        "texture": "Soft clouds, gentle water, peaceful natural textures.",
    },
}

# =============================================================================
# NETFLIX RECOMMENDATIONS - Entertainment Streaming Style
# =============================================================================

NETFLIX_RECOMMENDATIONS_IMAGE_SETTINGS: dict[str, Any] = {
    "style": "cinematic entertainment streaming",
    "color_palette": "netflix red, cinema black, screen glow, popcorn gold",
    "quality": "high",
    "size": "1536x1024",
    "size_tiktok": "1024x1536",
    "prompt_template": {
        "prefix": "Cinematic entertainment imagery, movie poster aesthetic, streaming platform style.",
        "photography": "Dramatic movie-poster compositions, theatrical lighting, entertainment focus.",
        "lighting": "Cinema lighting, dramatic spotlights, screen glow ambiance.",
        "color_grading": "Rich cinematic colors, Netflix red accents, movie poster contrast.",
        "mood": "Exciting, binge-worthy, must-watch, entertainment anticipation.",
        "quality_suffix": "High resolution, movie poster quality, streaming platform aesthetic.",
        "artistic_references": "Netflix thumbnails, movie posters, entertainment marketing.",
    },
    "default_visual_style": {
        "environment": "Cozy watching setups, cinema vibes, TV screens, popcorn moments.",
        "color_mood": "Netflix reds, cinema blacks, warm screen glows, cozy tones.",
        "texture": "Soft blankets, glowing screens, movie theater ambiance.",
    },
}

# =============================================================================
# MOCKUMENTARY HOW IT'S MADE - Absurdist Comedy Documentary Style
# =============================================================================

MOCKUMENTARY_HOWMADE_IMAGE_SETTINGS: dict[str, Any] = {
    "style": "documentary parody industrial absurdist",
    "color_palette": "factory grey, industrial orange, sterile white, safety yellow",
    "quality": "high",
    "size": "1536x1024",
    "size_tiktok": "1024x1536",
    "prompt_template": {
        "prefix": "Industrial documentary photography style, factory footage aesthetic, How It's Made TV show look.",
        "photography": "Wide factory shots, conveyor belt close-ups, industrial machinery, worker perspectives.",
        "lighting": "Harsh fluorescent factory lighting, industrial overhead lights, sterile manufacturing environment.",
        "color_grading": "Slightly desaturated industrial tones, factory grey and orange, clinical aesthetic.",
        "mood": "Deadpan serious documentary style, absurdly mundane, hilariously over-produced for simple topics.",
        "quality_suffix": "High resolution, documentary quality, industrial manufacturing aesthetic.",
        "artistic_references": "How It's Made TV show, Discovery Channel factory tours, industrial B-roll footage.",
    },
    "default_visual_style": {
        "environment": "Factory floors, assembly lines, conveyor belts, industrial machinery, sterile labs.",
        "color_mood": "Industrial greys, safety oranges, sterile whites, caution yellows.",
        "texture": "Metal machinery, rubber conveyor belts, plastic molds, industrial equipment.",
    },
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_image_settings(niche: str) -> dict[str, Any]:
    """
    Get image settings for a specific niche.

    Args:
        niche: The niche identifier (e.g., "scary-stories", "finance", etc.)

    Returns:
        Dictionary containing image settings for the niche

    Raises:
        ValueError: If niche is not recognized
    """
    settings_map = {
        "scary-stories": SCARY_STORIES_IMAGE_SETTINGS,
        "finance": FINANCE_IMAGE_SETTINGS,
        "luxury": LUXURY_IMAGE_SETTINGS,
        "true-crime": TRUE_CRIME_IMAGE_SETTINGS,
        "psychology-facts": PSYCHOLOGY_FACTS_IMAGE_SETTINGS,
        "history": HISTORY_IMAGE_SETTINGS,
        "motivation": MOTIVATION_IMAGE_SETTINGS,
        "space-astronomy": SPACE_ASTRONOMY_IMAGE_SETTINGS,
        "conspiracy-mysteries": CONSPIRACY_MYSTERIES_IMAGE_SETTINGS,
        "animal-facts": ANIMAL_FACTS_IMAGE_SETTINGS,
        "health-wellness": HEALTH_WELLNESS_IMAGE_SETTINGS,
        "relationship-advice": RELATIONSHIP_ADVICE_IMAGE_SETTINGS,
        "tech-gadgets": TECH_GADGETS_IMAGE_SETTINGS,
        "life-hacks": LIFE_HACKS_IMAGE_SETTINGS,
        "mythology-folklore": MYTHOLOGY_FOLKLORE_IMAGE_SETTINGS,
        "unsolved-mysteries": UNSOLVED_MYSTERIES_IMAGE_SETTINGS,
        "geography-facts": GEOGRAPHY_FACTS_IMAGE_SETTINGS,
        "ai-future-tech": AI_FUTURE_TECH_IMAGE_SETTINGS,
        "philosophy": PHILOSOPHY_IMAGE_SETTINGS,
        "book-summaries": BOOK_SUMMARIES_IMAGE_SETTINGS,
        "celebrity-net-worth": CELEBRITY_NET_WORTH_IMAGE_SETTINGS,
        "survival-tips": SURVIVAL_TIPS_IMAGE_SETTINGS,
        "sleep-relaxation": SLEEP_RELAXATION_IMAGE_SETTINGS,
        "netflix-recommendations": NETFLIX_RECOMMENDATIONS_IMAGE_SETTINGS,
        "mockumentary-howmade": MOCKUMENTARY_HOWMADE_IMAGE_SETTINGS,
    }

    if niche not in settings_map:
        raise ValueError(
            f"Unknown niche: {niche}. Must be one of: {list(settings_map.keys())}"
        )

    return settings_map[niche]


def build_enhanced_prompt(
    base_prompt: str,
    niche: str,
    visual_style: dict[str, Any] | None = None,
) -> str:
    """
    Build a cinematically-enhanced prompt for high-quality image generation.

    Args:
        base_prompt: The original scene description
        niche: One of "scary-stories", "finance", "luxury"
        visual_style: Optional story-level visual style overrides from script

    Returns:
        Enhanced prompt string optimized for image generation
    """
    settings = get_image_settings(niche)

    # Check if this niche has enhanced prompt templates
    if "prompt_template" not in settings:
        # Fall back to legacy simple enhancement
        return (
            f"{base_prompt}. Style: {settings['style']}. "
            f"Color palette: {settings['color_palette']}. "
            f"High quality, detailed, professional."
        )

    template = settings["prompt_template"]
    default_style = settings.get("default_visual_style", {})

    # Merge default visual style with any script-specific overrides
    effective_style = {**default_style}
    if visual_style:
        effective_style.update(visual_style)

    # Build the enhanced prompt in a structured way
    prompt_parts = []

    # 1. Cinematic prefix
    prompt_parts.append(template.get("prefix", ""))

    # 2. Core scene description (the original prompt, enhanced)
    prompt_parts.append(base_prompt)

    # 3. Visual continuity elements from story style
    if effective_style:
        style_elements = []
        if "environment" in effective_style:
            style_elements.append(f"Setting: {effective_style['environment']}")
        if "recurring_elements" in effective_style:
            for element_name, element_desc in effective_style[
                "recurring_elements"
            ].items():
                style_elements.append(f"{element_name}: {element_desc}")
        if style_elements:
            prompt_parts.append(" | ".join(style_elements))

    # 4. Technical photography details
    prompt_parts.append(template.get("photography", ""))

    # 5. Lighting direction
    prompt_parts.append(template.get("lighting", ""))

    # 6. Color grading
    if "color_mood" in effective_style:
        prompt_parts.append(f"Color grading: {effective_style['color_mood']}")
    else:
        prompt_parts.append(template.get("color_grading", ""))

    # 7. Mood and atmosphere
    prompt_parts.append(template.get("mood", ""))

    # 8. Texture details
    if "texture" in effective_style:
        prompt_parts.append(f"Textures: {effective_style['texture']}")

    # 9. Quality and artistic reference suffix
    prompt_parts.append(template.get("quality_suffix", ""))
    prompt_parts.append(template.get("artistic_references", ""))

    # Filter out empty parts and join
    enhanced_prompt = " ".join(part for part in prompt_parts if part.strip())

    return enhanced_prompt

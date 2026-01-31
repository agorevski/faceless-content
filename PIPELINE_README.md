# Faceless Content Production Pipeline

## What's New (January 2026)

- ✅ **Configuration Validator** - Catch errors before running the pipeline
- ✅ **Thumbnail Generator** - Create A/B testable thumbnails automatically
- ✅ **Subtitle Generator** - SRT/VTT captions with TikTok-style animation data
- ✅ **Checkpointing** - Resume failed runs without losing progress
- ✅ **Enhanced CLI** - New flags for thumbnails, subtitles, and validation

## Quick Start

### 1. Install Requirements

```powershell
# Install Python dependencies
pip install requests

# Install FFmpeg (required for video processing)
# Option A: Using winget
winget install FFmpeg

# Option B: Using Chocolatey
choco install ffmpeg

# Option C: Manual download from https://ffmpeg.org/download.html
# Add to PATH after installing
```

### 2. Configure API Keys

Edit `pipeline/config.py` and replace the placeholder values:

```python
# Azure OpenAI (for image generation)
AZURE_OPENAI_IMAGE_ENDPOINT = "https://YOUR-RESOURCE.openai.azure.com/"
AZURE_OPENAI_IMAGE_KEY = "your-api-key-here"
AZURE_OPENAI_IMAGE_DEPLOYMENT = "dall-e-3"  # or "gpt-image-1"

# Azure TTS (for voiceovers)
AZURE_TTS_KEY = "your-speech-key-here"
AZURE_TTS_REGION = "eastus"  # your region
```

### 3. Run the Pipeline

```powershell
cd faceless-content/pipeline

# Generate 1 scary story video (both platforms)
python pipeline.py --niche scary-stories

# Generate 3 finance videos for YouTube only
python pipeline.py --niche finance --count 3 --platform youtube

# Process existing scripts (skip Reddit fetch)
python pipeline.py --niche luxury --skip-fetch

# Process a specific script
python pipeline.py --niche scary-stories --script "../scary-stories/scripts/my-story_script.json"
```

---

## Pipeline Modules

### 1. Story Scraper (`story_scraper.py`)
Fetches content from Reddit and converts to video scripts.

```powershell
# Fetch 5 scary stories
python story_scraper.py --niche scary-stories --count 5

# Fetch from a specific subreddit
python story_scraper.py --niche scary-stories --subreddit LetsNotMeet --count 3
```

**Output:** JSON script files in `{niche}/scripts/`

### 2. Image Generator (`image_generator.py`)
Generates images using Azure OpenAI (DALL-E 3 or GPT-Image-1).

```powershell
# Generate a single image
python image_generator.py "A dark forest at night with fog" --niche scary-stories --name forest_scene

# Generate from a script file (all scenes)
python -c "from image_generator import generate_from_script; generate_from_script('path/to/script.json', 'scary-stories')"
```

**Output:** PNG images in `{niche}/images/`

### 3. TTS Generator (`tts_generator.py`)
Creates voiceovers using Azure TTS (or ElevenLabs later).

```powershell
# Generate a single audio clip
python tts_generator.py "This is a test narration" --niche scary-stories --name test_audio

# Generate from a script file
python -c "from tts_generator import generate_from_script; generate_from_script('path/to/script.json', 'scary-stories')"
```

**Output:** MP3 audio files in `{niche}/audio/`

### 4. Video Assembler (`video_assembler.py`)
Combines images + audio into final videos using FFmpeg.

```powershell
# Assemble a video from a script
python video_assembler.py path/to/script.json --niche scary-stories --platform youtube

# Add background music
python video_assembler.py path/to/script.json --niche scary-stories --music ../shared/music/horror_ambient.mp3
```

**Output:** MP4 videos in `{niche}/output/`

### 5. Config Validator (`config_validator.py`) 🆕
Validates all API keys and settings before running the pipeline.

```powershell
# Validate configuration
python config_validator.py

# Test actual API connections
python config_validator.py --test-connections

# Validate for a specific niche
python config_validator.py --niche scary-stories
```

**Output:** Pass/fail status for each configuration item

### 6. Thumbnail Generator (`thumbnail_generator.py`) 🆕
Creates click-worthy thumbnails with A/B testing variants.

```powershell
# Generate thumbnails for a video title
python thumbnail_generator.py "The Stairs That Shouldn't Be There" --niche scary-stories

# Generate 3 variants with specific concept
python thumbnail_generator.py "7 Money Mistakes" --niche finance --variants 3 --concept warning

# Available concepts: reaction, reveal, versus, before_after, countdown, mystery, warning, secret
```

**Output:** PNG thumbnails in `{niche}/images/thumbnails/`

### 7. Subtitle Generator (`subtitle_generator.py`) 🆕
Creates SRT/VTT subtitle files and animated caption data.

```powershell
# Generate subtitles from script
python subtitle_generator.py path/to/script.json --niche scary-stories

# Generate animated caption JSON (for TikTok-style word-by-word)
python subtitle_generator.py path/to/script.json --niche scary-stories --animated

# Burn subtitles into video
python subtitle_generator.py path/to/script.json --niche scary-stories --burn path/to/video.mp4
```

**Output:** SRT, VTT, and caption JSON files in `{niche}/audio/`

---

## New CLI Options

The main pipeline now supports additional flags:

```powershell
# Generate thumbnails along with video
python pipeline.py --niche scary-stories --script path/to/script.json --thumbnails

# Generate subtitles
python pipeline.py --niche finance --script path/to/script.json --subtitles

# Burn subtitles directly into video
python pipeline.py --niche luxury --script path/to/script.json --burn-subs

# Validate configuration only (no processing)
python pipeline.py --niche scary-stories --validate-only

# Skip validation (if you know config is good)
python pipeline.py --niche scary-stories --no-validate

# Full production with all features
python pipeline.py --niche scary-stories --script path/to/script.json \
    --enhance --thumbnails --subtitles --music path/to/music.mp3
```

---

## Directory Structure

```
faceless-content/
├── scary-stories/
│   ├── scripts/      # Story scripts (JSON)
│   ├── images/       # Generated images
│   ├── audio/        # Generated voiceovers
│   ├── videos/       # Video segments
│   └── output/       # Final videos
├── finance/
│   └── (same structure)
├── luxury/
│   └── (same structure)
├── shared/
│   ├── templates/    # Reusable templates
│   ├── prompts/      # Image prompt templates
│   └── music/        # Background music files
└── pipeline/
    ├── config.py           # API keys & settings
    ├── story_scraper.py    # Content fetching
    ├── image_generator.py  # AI image generation
    ├── tts_generator.py    # Text-to-speech
    ├── video_assembler.py  # FFmpeg video assembly
    └── pipeline.py         # Main orchestrator
```

---

## Script Format

Scripts are JSON files with this structure:

```json
{
  "title": "The Story Title",
  "source": "r/nosleep",
  "author": "username",
  "url": "https://reddit.com/...",
  "niche": "scary-stories",
  "created_at": "2025-01-29T19:00:00",
  "scenes": [
    {
      "scene_number": 1,
      "narration": "Text that will be spoken...",
      "image_prompt": "Description for AI image generation...",
      "duration_estimate": 15.5
    },
    {
      "scene_number": 2,
      "narration": "More narration text...",
      "image_prompt": "Another image description...",
      "duration_estimate": 12.0
    }
  ]
}
```

You can create these manually for custom content!

---

## Manual Workflow

If you prefer more control, run each step separately:

```powershell
# Step 1: Fetch stories
python story_scraper.py --niche scary-stories --count 5

# Step 2: Review and edit scripts in scary-stories/scripts/
# (Adjust narration, improve image prompts, etc.)

# Step 3: Generate images
python image_generator.py --help  # For options

# Step 4: Generate audio
python tts_generator.py --help

# Step 5: Assemble video
python video_assembler.py --help
```

---

## Custom Content

To create a video from your own content:

```python
from pipeline import quick_generate

result = quick_generate(
    niche="scary-stories",
    title="My Custom Horror Story",
    content="""
    Your story text goes here...
    
    It will be automatically split into scenes.
    Each paragraph becomes a scene with its own
    image and audio segment.
    """,
    platforms=["youtube", "tiktok"]
)
```

Or create a script JSON manually and run:
```powershell
python pipeline.py --niche scary-stories --script path/to/your_script.json
```

---

## Voice Settings

Edit `config.py` to change voice settings per niche:

```python
VOICE_SETTINGS = {
    "scary-stories": {
        "azure_voice": "en-US-GuyNeural",  # Deep male voice
        "azure_style": "serious",
        "azure_rate": "-10%",  # Slower
        "azure_pitch": "-5%",  # Lower
    },
    # ... other niches
}
```

Available Azure voices: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support

---

## Switching to ElevenLabs

When you get an ElevenLabs API key:

1. Edit `config.py`:
```python
ELEVENLABS_API_KEY = "your-key-here"
USE_ELEVENLABS = True

VOICE_SETTINGS = {
    "scary-stories": {
        # ... existing settings ...
        "elevenlabs_voice_id": "your-voice-id",
    },
}
```

2. That's it! The pipeline will automatically use ElevenLabs.

---

## Free Music Sources

Download royalty-free music and place in `shared/music/`:

- **Pixabay Music:** https://pixabay.com/music/
- **YouTube Audio Library:** (via YouTube Studio)
- **FreePD:** https://freepd.com/
- **Incompetech:** https://incompetech.com/music/

---

## Tips

1. **Review scripts before generating** - The auto-generated image prompts are basic. Edit them for better results.

2. **Batch process** - Generate all images first, review them, then generate audio.

3. **Keep originals** - Don't delete intermediate files until you're happy with the final video.

4. **Test with one scene** - Before processing a full story, test the pipeline with a single scene to verify API keys work.

5. **TikTok cuts** - The pipeline automatically creates 60-second cuts from YouTube videos. Find them in `{niche}/output/tiktok_cuts/`.

---

## Troubleshooting

**"FFmpeg not found"**
- Make sure FFmpeg is installed and in your PATH
- Try running `ffmpeg -version` in terminal

**"API key invalid"**
- Double-check your Azure endpoint URL and key
- Ensure the deployment name matches your Azure setup

**"Rate limited"**
- Add delays between API calls in the scripts
- Azure has per-minute quotas

**"Image generation failed"**
- Check your Azure OpenAI quota
- Some prompts may be rejected by content filters - edit the prompt

---

## Need Help?

Ask me to:
- Generate a specific type of content
- Modify the pipeline for your needs
- Add new features (thumbnails, subtitles, etc.)
- Debug any issues

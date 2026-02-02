# Faceless Content Pipeline

[![CI](https://github.com/agorevski/faceless-content/actions/workflows/ci.yml/badge.svg)](https://github.com/agorevski/faceless-content/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AI-powered content production pipeline for creating "faceless" videos with AI-generated images, text-to-speech narration, and automated video assembly.

## ✨ Features

- **Multi-Niche Support**: 23 content niches including scary stories, finance, luxury, true crime, psychology, and more
- **AI Image Generation**: Azure OpenAI (GPT-Image-1/DALL-E) for scene illustrations
- **Text-to-Speech**: Azure OpenAI TTS or ElevenLabs for narration
- **Automated Video Assembly**: FFmpeg-based video production
- **Multi-Platform Output**: YouTube (16:9) and TikTok (9:16) formats
- **Smart Checkpointing**: Resume interrupted jobs automatically
- **Thumbnail Generation**: A/B testing variants for CTR optimization
- **Subtitle Generation**: SRT/VTT formats with optional burn-in
- **Deep Research**: AI-powered topic research with configurable depth levels
- **Quality Scoring**: Hook analysis, retention prediction, and quality gates
- **Trend Discovery**: Find trending topics from Reddit with viral potential scoring

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- FFmpeg installed and in PATH
- Azure OpenAI account with deployed models

### Installation

```bash
# Clone the repository
git clone https://github.com/agorevski/faceless-content.git
cd faceless-content

# Create virtual environment and install
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Edit `.env` with your credentials:

```env
# Azure OpenAI (required)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key

# Model deployments
AZURE_OPENAI_IMAGE_DEPLOYMENT=gpt-image-1
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o
AZURE_OPENAI_TTS_DEPLOYMENT=gpt-4o-mini-tts
```

### Basic Usage

```bash
# Validate configuration
faceless validate --test-connections

# Generate a scary story video
faceless generate scary-stories

# Generate 3 finance videos for YouTube only
faceless generate finance -c 3 -p youtube

# Process a specific script with enhancement
faceless generate scary-stories -s path/to/script.json --enhance
```

## 📁 Project Structure

```
faceless-content/
├── src/faceless/           # Main package
│   ├── cli/                # Command-line interface
│   ├── clients/            # API clients (Azure, ElevenLabs, Reddit)
│   ├── config/             # Configuration management
│   ├── core/               # Domain models, enums, exceptions
│   ├── services/           # Business logic services
│   └── utils/              # Utilities (logging, helpers)
├── tests/                  # Test suite
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
├── documentation/          # Project documentation
├── output/                 # Generated content (gitignored)
├── shared/                 # Shared resources
│   ├── music/              # Background music
│   ├── prompts/            # Prompt templates
│   └── templates/          # Video templates
├── pyproject.toml          # Project configuration
└── .env                    # Environment variables (gitignored)
```

## 🎬 Pipeline Workflow

1. **Content Acquisition**: Fetch stories from Reddit or load existing scripts
2. **Script Enhancement** (optional): Use GPT to improve engagement and pacing
3. **Image Generation**: Create AI images for each scene
4. **Audio Generation**: Convert narration text to speech
5. **Video Assembly**: Combine images and audio with FFmpeg
6. **Post-Processing**: Generate thumbnails, subtitles, and TikTok cuts

### Key Capabilities

- **Checkpointing**: Resume failed runs without losing progress
- **Multi-Platform**: Optimized output for YouTube (16:9) and TikTok (9:16)
- **TikTok Cuts**: Automatically segments long videos into 60-second clips
- **A/B Thumbnails**: Generate multiple thumbnail variants for testing
- **Animated Subtitles**: TikTok-style word-by-word caption data

## 📝 Script Format

Scripts use JSON format with the following structure:

```json
{
  "title": "The House at the End of the Street",
  "niche": "scary-stories",
  "source": "r/nosleep",
  "author": "original_author",
  "visual_style": {
    "environment": "Dark foggy suburban neighborhood",
    "color_mood": "Deep blues, grays, amber highlights"
  },
  "scenes": [
    {
      "scene_number": 1,
      "narration": "The old house stood silent...",
      "image_prompt": "A dark Victorian house at night",
      "duration_estimate": 15.0
    }
  ]
}
```

## 🧪 Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=src/faceless --cov-report=html

# Run linting
ruff check src/ tests/

# Run type checking
mypy src/

# Format code
ruff format src/ tests/

# Install pre-commit hooks
pre-commit install
```

## 📚 Documentation

- [Architecture Overview](documentation/ARCHITECTURE.md)
- [Setup Guide](documentation/SETUP_GUIDE.md)
- [Pipeline Reference](documentation/PIPELINE_README.md)
- [Future Improvements](documentation/FUTURE_IMPROVEMENTS.md)
- [Improvement Suggestions](documentation/SUGGESTIONS.md)

## 🔧 CLI Reference

```
Usage: faceless [OPTIONS] COMMAND [ARGS]...

Commands:
  generate   Generate faceless video content
  validate   Validate configuration and API connections
  init       Initialize project directories
  info       Show pipeline configuration information
  research   Research a topic for content creation
  quality    Evaluate script quality before production
  trending   Discover trending topics for a niche
```

### Generate Command

```
Usage: faceless generate NICHE [OPTIONS]

Arguments:
  NICHE  Content niche (scary-stories, finance, luxury, etc.)

Options:
  -c, --count INTEGER       Number of videos to generate [default: 1]
  -p, --platform PLATFORM   Target platform(s) [default: youtube, tiktok]
  -s, --script PATH         Path to existing script file
  --skip-fetch              Skip fetching new stories
  -e, --enhance             Enhance scripts with GPT
  -t, --thumbnails          Generate thumbnail variants [default: True]
  --subtitles               Generate subtitle files [default: True]
  -m, --music PATH          Path to background music file
```

### Research Command

```
Usage: faceless research TOPIC [OPTIONS]

Research a topic for content creation with AI-powered deep research.

Arguments:
  TOPIC  Topic to research

Options:
  -n, --niche NICHE         Content niche for context [default: finance]
  -d, --depth TEXT          Research depth: quick, standard, deep, investigative
  -s, --structure           Generate content structure recommendation
  -o, --output PATH         Save research to JSON file

Examples:
  faceless research "Why diamonds are expensive" -n finance -d deep
  faceless research "Scary hotel stories" -n scary-stories -o research.json
```

### Quality Command

```
Usage: faceless quality SCRIPT_PATH [OPTIONS]

Evaluate script quality before production.

Arguments:
  SCRIPT_PATH  Path to script JSON file

Options:
  --strict                  Require all quality gates to pass
  -i, --improve-hooks       Generate improved hook alternatives
  -o, --output PATH         Save quality report to JSON file

Examples:
  faceless quality scripts/my-script.json --strict
  faceless quality scripts/my-script.json --improve-hooks -o report.json
```

### Trending Command

```
Usage: faceless trending NICHE [OPTIONS]

Discover trending topics for a niche.

Arguments:
  NICHE  Content niche to get trends for

Options:
  -c, --count INTEGER       Number of topics to show [default: 10]
  -a, --analyze TOPIC       Analyze a specific topic's potential
  --calendar                Show content calendar suggestions
  -o, --output PATH         Save trend report to JSON file

Examples:
  faceless trending scary-stories --calendar
  faceless trending finance --analyze "Why Gen Z is broke"
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure:
- All tests pass (`pytest`)
- Code is formatted (`ruff format`)
- No linting errors (`ruff check`)
- Types are correct (`mypy src/`)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for educational and entertainment purposes. Always:
- Respect content creators' rights and obtain proper permissions
- Follow platform terms of service
- Ensure generated content complies with applicable laws
- Credit original authors when using scraped content
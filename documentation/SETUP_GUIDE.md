# Faceless Content Pipeline - Setup Guide

Complete setup instructions for the Faceless Content Production Pipeline.

---

## 📋 Prerequisites

### 1. Python 3.10+

**Option A: Microsoft Store (Windows - Easiest)**
```powershell
# Open Microsoft Store and search for "Python 3.12" or run:
winget install Python.Python.3.12
```

**Option B: Direct Download**
1. Go to https://www.python.org/downloads/
2. Download Python 3.11 or later
3. **IMPORTANT:** Check "Add Python to PATH" during installation

**Option C: macOS/Linux**
```bash
# macOS with Homebrew
brew install python@3.12

# Ubuntu/Debian
sudo apt update && sudo apt install python3.12 python3.12-venv
```

Verify installation:
```bash
python --version    # Should show 3.10+
pip --version       # Should be available
```

### 2. FFmpeg (Video Processing)

**Windows:**
```powershell
# Using winget (recommended)
winget install FFmpeg

# Or using Chocolatey
choco install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

**Manual Installation (Windows):**
1. Go to https://ffmpeg.org/download.html
2. Click "Windows" → "Windows builds from gyan.dev"
3. Download "ffmpeg-release-essentials.zip"
4. Extract to `C:\ffmpeg`
5. Add `C:\ffmpeg\bin` to your system PATH:
   - Search "Environment Variables" in Start menu
   - Edit "Path" under System variables
   - Add `C:\ffmpeg\bin`
   - Restart terminal

Verify installation:
```bash
ffmpeg -version
ffprobe -version
```

---

## 🚀 Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/agorevski/faceless-content.git
cd faceless-content
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate (Windows Command Prompt)
.\.venv\Scripts\activate.bat

# Activate (macOS/Linux)
source .venv/bin/activate
```

### Step 3: Install the Package

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Or install without dev dependencies
pip install -e .
```

### Step 4: Verify Installation

```bash
# Check CLI is available
faceless --version

# Should output: Faceless Content Pipeline v1.0.0
```

---

## 🔑 Configuration

### Step 1: Create Environment File

```bash
# Copy the example environment file
cp .env.example .env
```

### Step 2: Edit `.env` with Your API Keys

Open `.env` in your text editor and fill in your credentials:

```env
# =============================================================================
# AZURE OPENAI CONFIGURATION (Required)
# =============================================================================

# Your Azure OpenAI resource endpoint
AZURE_OPENAI_ENDPOINT=https://YOUR-RESOURCE-NAME.openai.azure.com/

# Your Azure OpenAI API key
AZURE_OPENAI_API_KEY=your-api-key-here

# Model deployment names (update if different)
AZURE_OPENAI_IMAGE_DEPLOYMENT=gpt-image-1
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o
AZURE_OPENAI_TTS_DEPLOYMENT=gpt-4o-mini-tts

# API version
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# =============================================================================
# OPTIONAL SETTINGS
# =============================================================================

# Output directory (default: output)
OUTPUT_DIR=output

# Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Enable debug mode
DEBUG=false

# Enable checkpointing for resume support
ENABLE_CHECKPOINTING=true

# Request settings
REQUEST_TIMEOUT=120
MAX_RETRIES=3
MAX_CONCURRENT_REQUESTS=5
```

### Where to Find Azure OpenAI Credentials

1. **Azure Portal:** https://portal.azure.com
2. Navigate to your **Azure OpenAI** resource
3. Go to **Keys and Endpoint** section:
   - **Endpoint:** Copy the endpoint URL
   - **API Key:** Copy Key 1 or Key 2
4. Go to **Model Deployments** section:
   - Note your deployment names for each model type

### Step 3: Validate Configuration

```bash
# Check if configuration is valid
faceless validate

# Test API connections
faceless validate --test-connections
```

Expected output:
```
╭─ 🔍 Checking Configuration ─╮
│ Configuration Validation    │
╰─────────────────────────────╯
                  Configuration Status
┏━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Setting      ┃ Status ┃ Details                       ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Azure OpenAI │ ✓      │ Configured                    │
│ ElevenLabs   │ –      │ Not enabled (using Azure TTS) │
│ FFmpeg       │ ✓      │ Installed                     │
└──────────────┴────────┴───────────────────────────────┘

✓ Configuration is valid!
```

---

## 📁 Project Structure

After installation, your project should look like this:

```
faceless-content/
├── src/faceless/           # Main Python package
│   ├── cli/                # CLI commands
│   ├── clients/            # API clients
│   ├── config/             # Configuration
│   ├── core/               # Models, enums, exceptions
│   ├── pipeline/           # Orchestrator
│   ├── services/           # Business logic
│   └── utils/              # Utilities
├── tests/                  # Test suite
├── documentation/          # Documentation
├── output/                 # Generated content (created on first run)
│   ├── scary-stories/
│   ├── finance/
│   └── luxury/
├── shared/                 # Shared resources
│   ├── music/              # Background music files
│   ├── prompts/            # Prompt templates
│   └── templates/          # Video templates
├── .env                    # Your configuration (gitignored)
├── .env.example            # Configuration template
└── pyproject.toml          # Project configuration
```

---

## 🎬 Usage

### Initialize Directories

```bash
# Create output directories for a niche
faceless init scary-stories
faceless init finance
faceless init luxury
```

### Show Current Configuration

```bash
faceless info
```

### Generate Content

```bash
# Generate 1 scary story video for all platforms
faceless generate scary-stories

# Generate 3 finance videos for YouTube only
faceless generate finance -c 3 -p youtube

# Process a specific script file
faceless generate scary-stories -s path/to/script.json

# Generate with script enhancement
faceless generate scary-stories --enhance

# Generate with background music
faceless generate scary-stories -m shared/music/ambient.mp3

# Skip thumbnails or subtitles
faceless generate finance --no-thumbnails --no-subtitles
```

### CLI Reference

```
Usage: faceless [OPTIONS] COMMAND [ARGS]...

Commands:
  generate   Generate faceless video content
  validate   Validate configuration and API connections
  init       Initialize project directories
  info       Show pipeline configuration information

Global Options:
  -v, --version  Show version and exit
  --debug        Enable debug logging
  --help         Show help message
```

---

## 🧪 Development Setup

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src/faceless --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py -v
```

### Code Quality Tools

```bash
# Run linter
ruff check src/ tests/

# Auto-fix lint issues
ruff check --fix src/ tests/

# Format code
ruff format src/ tests/

# Type checking
mypy src/

# Run all checks at once
pre-commit run --all-files
```

### Install Pre-commit Hooks

```bash
# Install hooks (run once)
pre-commit install

# Hooks will now run automatically on git commit
```

---

## 🎨 Optional Tools

### Video Editing (For Final Touches)

**DaVinci Resolve (Free, Professional)**
- Download: https://www.blackmagicdesign.com/products/davinciresolve
- Full editing suite, color grading, effects

**CapCut (Free, Simple)**
- Download: https://www.capcut.com/
- Great for TikTok/short-form editing

### Image Editing (For Thumbnails)

**GIMP (Free)**
- Download: https://www.gimp.org/downloads/

**Photopea (Free, Browser-based)**
- URL: https://www.photopea.com/
- Photoshop alternative, no install needed

---

## ✅ Setup Checklist

- [ ] Install Python 3.10+ and verify with `python --version`
- [ ] Install FFmpeg and verify with `ffmpeg -version`
- [ ] Clone repository and navigate to directory
- [ ] Create virtual environment: `python -m venv .venv`
- [ ] Activate virtual environment
- [ ] Install package: `pip install -e ".[dev]"`
- [ ] Copy environment file: `cp .env.example .env`
- [ ] Edit `.env` with your Azure OpenAI credentials
- [ ] Validate configuration: `faceless validate`
- [ ] Initialize directories: `faceless init scary-stories`
- [ ] Test generate command: `faceless generate --help`

---

## 🔧 Troubleshooting

### "faceless: command not found"

Make sure you:
1. Installed the package with `pip install -e .`
2. Have your virtual environment activated
3. Try: `python -m faceless --version`

### "Azure OpenAI: Missing endpoint or API key"

Check your `.env` file:
1. Verify `AZURE_OPENAI_ENDPOINT` starts with `https://`
2. Verify `AZURE_OPENAI_API_KEY` is set correctly
3. Make sure there are no extra spaces or quotes

### "FFmpeg not found"

1. Verify FFmpeg is installed: `ffmpeg -version`
2. If installed but not found, add it to your PATH
3. Restart your terminal after PATH changes

### "ModuleNotFoundError: No module named 'faceless'"

1. Make sure you ran `pip install -e .` in the project directory
2. Check that your virtual environment is activated
3. Try reinstalling: `pip uninstall faceless-content && pip install -e .`

### Image Generation Fails

1. Verify your Azure OpenAI deployment supports image generation
2. Check the deployment name matches `AZURE_OPENAI_IMAGE_DEPLOYMENT`
3. Some prompts may be rejected by content filters - try simpler prompts

### Tests Failing

```bash
# Run with verbose output
pytest -v --tb=long

# Run specific test
pytest tests/unit/test_models.py::TestScene::test_create_valid_scene -v
```

---

## 📚 Next Steps

1. Read the [Architecture Overview](ARCHITECTURE.md) to understand the system
2. Review sample scripts in the `output/{niche}/scripts/` directories
3. Create your first video: `faceless generate scary-stories`

---

## 🆘 Getting Help

- Check existing documentation in `documentation/`
- Review error messages - they usually contain helpful hints
- Run commands with `--debug` for more detailed output
- Check the GitHub repository for issues and updates
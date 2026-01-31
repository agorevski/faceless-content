# Architecture Overview

This document describes the system architecture, data flow, and component interactions of the Faceless Content Production Pipeline.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FACELESS CONTENT PIPELINE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                           CLI LAYER                                   │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │ │
│  │  │  generate   │  │  validate   │  │    init     │  │    info     │  │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                    │                                        │
│                                    ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                      PIPELINE ORCHESTRATOR                            │ │
│  │                                                                       │ │
│  │   Load Scripts → Enhance → Images → Audio → Video → Post-process     │ │
│  │                                                                       │ │
│  │   Features: Checkpointing, Resume, Progress Tracking                  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                    │                                        │
│           ┌────────────────────────┼────────────────────────┐              │
│           ▼                        ▼                        ▼              │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │ EnhancerService │    │  ImageService   │    │   TTSService    │        │
│  │                 │    │                 │    │                 │        │
│  │  Script GPT     │    │  Scene Images   │    │  Voice Audio    │        │
│  │  Enhancement    │    │  Per Platform   │    │  Per Scene      │        │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│           │                        │                        │              │
│           └────────────────────────┼────────────────────────┘              │
│                                    ▼                                        │
│                        ┌─────────────────┐                                 │
│                        │  VideoService   │                                 │
│                        │                 │                                 │
│                        │  FFmpeg-based   │                                 │
│                        │  Video Assembly │                                 │
│                        └─────────────────┘                                 │
│                                    │                                        │
│                     ┌──────────────┴──────────────┐                        │
│                     ▼                             ▼                        │
│            ┌──────────────┐              ┌──────────────┐                  │
│            │   YouTube    │              │   TikTok     │                  │
│            │  1920x1080   │              │  1080x1920   │                  │
│            └──────────────┘              └──────────────┘                  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                           INFRASTRUCTURE                                    │
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │ AzureOpenAI     │    │    Settings     │    │    Logging      │        │
│  │    Client       │    │ (pydantic-      │    │  (structlog)    │        │
│  │                 │    │  settings)      │    │                 │        │
│  │  - Images       │    │                 │    │  - JSON output  │        │
│  │  - Chat/GPT     │    │  - .env config  │    │  - Context      │        │
│  │  - TTS          │    │  - Validation   │    │  - Rich console │        │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Package Structure

```
faceless-content/
├── src/faceless/               # Main Python package
│   ├── __init__.py             # Package version and exports
│   ├── __main__.py             # Entry point: python -m faceless
│   │
│   ├── cli/                    # Command-Line Interface
│   │   ├── __init__.py         # Typer app export
│   │   └── commands.py         # generate, validate, init, info
│   │
│   ├── clients/                # External API Clients
│   │   ├── __init__.py
│   │   ├── base.py             # BaseHTTPClient with retry logic
│   │   └── azure_openai.py     # Azure OpenAI (images, chat, TTS)
│   │
│   ├── config/                 # Configuration Management
│   │   ├── __init__.py         # get_settings() export
│   │   └── settings.py         # Settings class (pydantic-settings)
│   │
│   ├── core/                   # Domain Models & Types
│   │   ├── __init__.py
│   │   ├── enums.py            # Niche, Platform, Voice, JobStatus
│   │   ├── exceptions.py       # Exception hierarchy (30+ types)
│   │   └── models.py           # Pydantic models
│   │
│   ├── pipeline/               # Pipeline Orchestration
│   │   ├── __init__.py
│   │   └── orchestrator.py     # Main workflow coordinator
│   │
│   ├── services/               # Business Logic Services
│   │   ├── __init__.py
│   │   ├── enhancer_service.py # Script enhancement with GPT
│   │   ├── image_service.py    # Image generation
│   │   ├── tts_service.py      # Text-to-speech generation
│   │   └── video_service.py    # Video assembly with FFmpeg
│   │
│   └── utils/                  # Utilities
│       ├── __init__.py
│       └── logging.py          # structlog configuration
│
├── tests/                      # Test Suite
│   ├── __init__.py
│   ├── conftest.py             # pytest fixtures
│   └── unit/
│       ├── __init__.py
│       └── test_models.py      # Model unit tests
│
├── documentation/              # Project Documentation
│   ├── ARCHITECTURE.md         # This file
│   ├── SETUP_GUIDE.md
│   └── PIPELINE_README.md
│
├── output/                     # Generated Content (gitignored)
│   └── {niche}/
│       ├── scripts/            # JSON script files
│       ├── images/             # Generated images
│       ├── audio/              # Generated audio
│       ├── videos/             # Video segments
│       └── final/              # Final output videos
│
├── shared/                     # Shared Resources
│   ├── music/                  # Background music
│   ├── prompts/                # Prompt templates
│   └── templates/              # Video templates
│
├── pipeline/                   # Legacy modules (deprecated)
│
├── pyproject.toml              # Project configuration
├── .env.example                # Environment template
├── .pre-commit-config.yaml     # Pre-commit hooks
└── .github/workflows/ci.yml    # CI/CD workflow
```

## Layer Descriptions

### 1. CLI Layer (`cli/`)

Provides the command-line interface using [Typer](https://typer.tiangolo.com/).

| Command | Description |
|---------|-------------|
| `faceless generate <niche>` | Run full pipeline for a niche |
| `faceless validate` | Check configuration and API connections |
| `faceless init <niche>` | Initialize output directories |
| `faceless info` | Display current settings |

**Options for `generate`:**
- `-c, --count` - Number of videos (1-10)
- `-p, --platform` - Target platform(s)
- `-s, --script` - Path to existing script
- `-e, --enhance` - Enhance scripts with GPT
- `-t, --thumbnails` - Generate thumbnails
- `--subtitles` - Generate subtitle files
- `-m, --music` - Background music path

### 2. Pipeline Layer (`pipeline/`)

The `Orchestrator` class coordinates the entire workflow:

```python
orchestrator = Orchestrator()
results = orchestrator.run(
    niche=Niche.SCARY_STORIES,
    platforms=[Platform.YOUTUBE, Platform.TIKTOK],
    count=3,
    enhance=True,
)
```

**Responsibilities:**
- Load/create scripts
- Coordinate service calls
- Manage checkpoints for resume
- Track progress and errors
- Generate final results

### 3. Services Layer (`services/`)

Business logic services that implement specific pipeline stages.

#### EnhancerService
Uses GPT to improve scripts for engagement:
- Improves narration flow
- Enhances image prompts
- Adds visual style consistency

#### ImageService
Generates images for each scene:
- Platform-specific sizing (YouTube vs TikTok)
- Visual style suffix application
- Checkpoint support for resume

#### TTSService
Generates audio narration:
- Niche-specific voice settings
- Speed adjustment
- Duration calculation with ffprobe

#### VideoService
Assembles final videos:
- Ken Burns effect (zoom/pan)
- Scene concatenation
- Background music mixing
- Platform-specific encoding

### 4. Clients Layer (`clients/`)

Handles external API communication with retry logic.

#### BaseHTTPClient
- HTTPX-based async-capable client
- Tenacity retry with exponential backoff
- Configurable timeouts
- Request/response logging

#### AzureOpenAIClient
- Image generation (DALL-E / GPT-Image-1)
- Chat completions (GPT-4o)
- Text-to-speech (gpt-4o-mini-tts)
- JSON response parsing

### 5. Core Layer (`core/`)

Domain models and shared types.

#### Enums
```python
class Niche(str, Enum):
    SCARY_STORIES = "scary-stories"
    FINANCE = "finance"
    LUXURY = "luxury"

class Platform(str, Enum):
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"

class Voice(str, Enum):
    ALLOY = "alloy"
    ECHO = "echo"
    ONYX = "onyx"
    NOVA = "nova"
    # ... etc
```

#### Models
```python
class Scene(BaseModel):
    scene_number: int
    narration: str
    image_prompt: str
    duration_estimate: float = 10.0
    image_path: Path | None = None
    audio_path: Path | None = None

class Script(BaseModel):
    title: str
    niche: Niche
    scenes: list[Scene]
    visual_style: VisualStyle | None = None
    # ... validation, serialization methods

class Checkpoint(BaseModel):
    job_id: UUID
    script_path: Path
    status: JobStatus
    completed_images: set[int] = set()
    completed_audio: set[int] = set()
    # ... save/load methods
```

#### Exceptions
Structured exception hierarchy with 30+ specific types:

```
FacelessError (base)
├── ConfigurationError
│   ├── MissingConfigError
│   ├── InvalidConfigError
│   └── EnvironmentError
├── APIError
│   ├── AzureOpenAIError
│   │   ├── ImageGenerationError
│   │   ├── ChatCompletionError
│   │   └── TTSGenerationError
│   ├── RateLimitError
│   └── AuthenticationError
├── ValidationError
│   ├── ScriptValidationError
│   └── SceneValidationError
├── PipelineError
│   ├── CheckpointError
│   └── StageError
└── FFmpegError
    └── VideoAssemblyError
```

### 6. Config Layer (`config/`)

Uses [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) for configuration management.

```python
class Settings(BaseSettings):
    # Azure OpenAI
    azure_openai_endpoint: str
    azure_openai_api_key: SecretStr
    azure_openai_image_deployment: str = "gpt-image-1"
    azure_openai_chat_deployment: str = "gpt-4o"
    azure_openai_tts_deployment: str = "gpt-4o-mini-tts"
    
    # Pipeline
    output_dir: Path = Path("output")
    max_retries: int = 3
    enable_checkpointing: bool = True
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
```

**Environment Variables:**
```bash
# Azure OpenAI (required)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key

# Optional overrides
AZURE_OPENAI_IMAGE_DEPLOYMENT=gpt-image-1
LOG_LEVEL=INFO
DEBUG=false
```

### 7. Utils Layer (`utils/`)

#### Logging
Uses [structlog](https://www.structlog.org/) for structured logging:

```python
from faceless.utils.logging import get_logger, LoggerMixin

# Direct usage
logger = get_logger(__name__)
logger.info("Processing script", title="My Story", scenes=5)

# Mixin for classes
class MyService(LoggerMixin):
    def process(self):
        self.logger.info("Starting process")
```

**Features:**
- JSON output for production
- Rich console output for development
- Context binding (request ID, script title)
- Automatic exception formatting

## Data Flow

### Script JSON Format

```json
{
  "title": "The House at the End of the Street",
  "niche": "scary-stories",
  "source": "r/nosleep",
  "author": "original_author",
  "url": "https://reddit.com/r/nosleep/...",
  "created_at": "2025-01-29T19:00:00Z",
  "enhanced_at": null,
  "visual_style": {
    "environment": "Dark foggy suburban neighborhood",
    "color_mood": "Deep blues, grays, amber highlights",
    "texture": "Weathered wood, cracked paint",
    "recurring_elements": {
      "house": "Victorian mansion with broken windows"
    }
  },
  "scenes": [
    {
      "scene_number": 1,
      "narration": "The old house stood silent at the end of our street...",
      "image_prompt": "A dark Victorian house at night, foggy street, amber streetlight",
      "duration_estimate": 12.5
    }
  ]
}
```

### File Naming Conventions

| Asset Type | Pattern | Example |
|------------|---------|---------|
| Script | `{safe_title}_script.json` | `the-house-at-the-end_script.json` |
| Image | `scene_{NN}_{platform}.png` | `scene_01_youtube.png` |
| Audio | `scene_{NN}.mp3` | `scene_01.mp3` |
| Video Segment | `scene_{NN}_{platform}.mp4` | `scene_01_youtube.mp4` |
| Final Video | `{niche}_{title}_{platform}.mp4` | `scary-stories_the-house_youtube.mp4` |

## Checkpointing System

Enables resuming failed runs:

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "script_path": "output/scary-stories/scripts/the-house_script.json",
  "status": "generating_audio",
  "started_at": "2025-01-29T19:00:00Z",
  "completed_steps": ["enhance", "images"],
  "completed_images": [1, 2, 3, 4, 5],
  "completed_audio": [1, 2],
  "completed_videos": {}
}
```

**Checkpoint Location:** `output/{niche}/.checkpoints/{script_name}.checkpoint.json`

## API Dependencies

| Service | Purpose | Client |
|---------|---------|--------|
| Azure OpenAI (GPT-Image-1/DALL-E) | Image generation | `AzureOpenAIClient.generate_image()` |
| Azure OpenAI (GPT-4o) | Script enhancement | `AzureOpenAIClient.chat_json()` |
| Azure OpenAI (TTS) | Voice synthesis | `AzureOpenAIClient.generate_audio()` |
| FFmpeg | Video processing | `subprocess.run()` |

## Platform-Specific Settings

| Setting | YouTube | TikTok |
|---------|---------|--------|
| Resolution | 1920×1080 | 1080×1920 |
| Aspect Ratio | 16:9 | 9:16 |
| Image Size | 1536×1024 | 1024×1536 |
| FPS | 30 | 30 |
| Codec | libx264 | libx264 |
| Max Duration | Unlimited | 60s segments |

## Voice Settings by Niche

| Niche | Voice | Speed |
|-------|-------|-------|
| Scary Stories | onyx | 0.9 |
| Finance | onyx | 1.0 |
| Luxury | nova | 0.95 |

## Testing

### Test Structure
```
tests/
├── conftest.py          # Shared fixtures
├── unit/
│   └── test_models.py   # Pydantic model tests
└── integration/         # API integration tests (optional)
```

### Running Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=src/faceless --cov-report=html

# Specific markers
pytest -m unit
pytest -m "not integration"
```

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/ci.yml`):

1. **Lint & Type Check** - Ruff + mypy
2. **Unit Tests** - pytest on Python 3.11 & 3.12
3. **Security Scan** - Bandit
4. **Build Package** - Build wheel/sdist
5. **Integration Tests** - Optional, on main branch

## Extension Points

### Adding a New Niche

1. Add to `Niche` enum in `core/enums.py`
2. Add voice settings in `config/settings.py`
3. Configure image style preferences

### Adding a New Voice Provider

1. Create new client in `clients/` (e.g., `elevenlabs.py`)
2. Add provider setting in `Settings`
3. Update `TTSService` to use new provider

### Adding a New Platform

1. Add to `Platform` enum with resolution property
2. Update `VideoService` encoding settings
3. Add platform-specific options in CLI

## Security Considerations

- API keys stored in `.env` file (gitignored)
- `SecretStr` type for sensitive settings
- Pre-commit hooks detect secrets
- Bandit security scanning in CI
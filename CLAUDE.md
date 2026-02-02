# Faceless Content Pipeline - Claude Instructions

## Quick Reference

```bash
# Install
pip install -e ".[dev]"

# Test
pytest

# Lint & Format
ruff check src/ tests/
ruff format src/ tests/

# Type Check
mypy src/

# Run CLI
faceless generate scary-stories -c 1 -p youtube
faceless validate --test-connections
```

## Project Overview

Python-based content production pipeline for creating "faceless" videos (YouTube/TikTok) with AI-generated images, text-to-speech narration, and automated video assembly. Supports 25 content niches.

## Architecture

```
src/faceless/
├── cli/        # Typer CLI commands (thin layer)
├── clients/    # External API clients (Azure OpenAI)
├── config/     # Pydantic Settings configuration
├── core/       # Domain models, enums, exceptions
├── services/   # Business logic (enhancer, image, tts, video, content_source, etc.)
├── pipeline/   # Orchestrator coordinating services
└── utils/      # Logging utilities
```

## Code Conventions

### Imports
- Use absolute imports: `from faceless.core.models import Script`
- Group: stdlib → third-party → local (enforced by ruff isort)

### Type Hints
- Required on ALL function signatures (enforced by mypy strict mode)
- Use `Path` from pathlib, not strings for file paths
- Use `list[T]` not `List[T]` (Python 3.10+ syntax)

### Models
- All data models use Pydantic v2 (`from pydantic import BaseModel`)
- Validation in models, not in services
- Use `Field()` for defaults and descriptions

### Error Handling
- Use custom exceptions from `faceless.core.exceptions`
- Never catch bare `Exception` - be specific
- Use `structlog` for logging with context: `logger.info("message", key=value)`

### Services Pattern
```python
class MyService:
    def __init__(self, client: AzureOpenAIClient, settings: Settings):
        self.client = client
        self.settings = settings
        self.logger = get_logger(__name__)
    
    async def process(self, data: InputModel) -> OutputModel:
        self.logger.info("Processing", data_id=data.id)
        # Business logic here
```

### Clients Pattern
- Inherit from `BaseHTTPClient` in `clients/base.py`
- Use `tenacity` for retry logic
- Use `httpx` for HTTP requests

## File Naming

| Asset | Pattern | Example |
|-------|---------|---------|
| Script | `{safe-title}_script.json` | `dark-forest_script.json` |
| Image | `scene_{NN}_{platform}.png` | `scene_01_youtube.png` |
| Audio | `scene_{NN}.mp3` | `scene_01.mp3` |
| Video | `{niche}_{title}_{platform}.mp4` | `scary-stories_dark-forest_youtube.mp4` |

## Key Enums

```python
from faceless.core.enums import Niche, Platform, Voice, JobStatus, ContentSourceType

# 25 niches available
Niche.SCARY_STORIES, Niche.FINANCE, Niche.LUXURY, Niche.TRUE_CRIME, ...

# Platforms
Platform.YOUTUBE  # 1920x1080, 16:9
Platform.TIKTOK   # 1080x1920, 9:16

# Content sources (for multi-source fetching)
ContentSourceType.REDDIT, ContentSourceType.WIKIPEDIA, ContentSourceType.YOUTUBE, ...
```

## Don'ts

- **Don't commit `.env` files** - use `.env.example` as template
- **Don't use relative imports** - always absolute from `faceless`
- **Don't skip type hints** - mypy strict mode enforced
- **Don't log sensitive data** - API keys use `SecretStr`

## Testing

- Tests in `tests/` using pytest
- Fixtures in `tests/conftest.py`
- Use markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`
- Mock external APIs with `respx` and `pytest-mock`
- Minimum 70% coverage required

## Environment Variables

Required in `.env`:
```
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_IMAGE_DEPLOYMENT=gpt-image-1
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o
AZURE_OPENAI_TTS_DEPLOYMENT=gpt-4o-mini-tts
```

## Common Tasks

### Add a new service
1. Create `src/faceless/services/my_service.py`
2. Follow the service pattern above
3. Add tests in `tests/unit/test_my_service.py`
4. Export from `services/__init__.py`

### Add a new CLI command
1. Add command function in `cli/commands.py`
2. Use `typer` decorators and `rich` for output
3. Keep CLI thin - delegate to services

### Add a new niche
1. Add to `Niche` enum in `core/enums.py`
2. Configure voice settings in `config/settings.py`
3. Create niche directory with `scripts/` subfolder

# Python Coding Standards

## Type Hints

All functions MUST have complete type annotations:

```python
# ✅ Good
def process_script(script: Script, platform: Platform) -> ProcessedScript:
    ...

async def generate_image(prompt: str, size: tuple[int, int]) -> bytes:
    ...

def get_scenes(script: Script) -> list[Scene]:
    ...

# ❌ Bad - missing type hints
def process_script(script, platform):
    ...
```

## Modern Python Syntax (3.10+)

Use modern type syntax:

```python
# ✅ Good
list[str]           # not List[str]
dict[str, int]      # not Dict[str, int]
tuple[int, str]     # not Tuple[int, str]
str | None          # not Optional[str]
int | str           # not Union[int, str]

# ❌ Bad - legacy typing
from typing import List, Dict, Optional, Union
```

## Imports

Always use absolute imports from the `faceless` package:

```python
# ✅ Good
from faceless.core.models import Script, Scene
from faceless.core.enums import Niche, Platform
from faceless.core.exceptions import ImageGenerationError
from faceless.config import get_settings

# ❌ Bad - relative imports
from ..core.models import Script
from .models import Scene
```

Import order (enforced by ruff isort):
1. Standard library
2. Third-party packages
3. Local imports

## Pydantic Models

```python
from pydantic import BaseModel, Field

class Scene(BaseModel):
    """Represents a single scene in a video script."""
    
    scene_number: int = Field(..., ge=1, description="Scene sequence number")
    narration: str = Field(..., min_length=1, description="Text to be narrated")
    image_prompt: str = Field(..., description="Prompt for image generation")
    duration_estimate: float = Field(default=10.0, ge=1.0, le=60.0)
    
    # Optional fields use None default
    image_path: Path | None = None
    audio_path: Path | None = None
```

## Error Handling

Use custom exceptions from `core/exceptions.py`:

```python
from faceless.core.exceptions import (
    ImageGenerationError,
    TTSGenerationError,
    ConfigurationError,
)

# ✅ Good - specific exception
try:
    image = await client.generate_image(prompt)
except ImageGenerationError as e:
    logger.error("Image generation failed", prompt=prompt, error=str(e))
    raise

# ❌ Bad - bare exception
try:
    image = await client.generate_image(prompt)
except Exception:
    pass
```

## Logging

Use structlog with context:

```python
from faceless.utils.logging import get_logger

logger = get_logger(__name__)

# ✅ Good - structured logging with context
logger.info("Processing script", title=script.title, scenes=len(script.scenes))
logger.error("Generation failed", scene=scene_number, error=str(e))

# ❌ Bad - print or unstructured logging
print(f"Processing {script.title}")
logger.info(f"Processing script: {script.title}")  # Don't use f-strings
```

## Async/Await

Use async for I/O operations:

```python
import httpx

# ✅ Good - async HTTP
async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# Use asyncio.gather for concurrent operations
results = await asyncio.gather(
    generate_image(prompt1),
    generate_image(prompt2),
    generate_image(prompt3),
)
```

## Path Handling

Always use `pathlib.Path`:

```python
from pathlib import Path

# ✅ Good
output_dir = Path("output") / niche / "images"
output_dir.mkdir(parents=True, exist_ok=True)
image_path = output_dir / f"scene_{scene_number:02d}.png"

# ❌ Bad - string paths
output_dir = "output/" + niche + "/images"
os.makedirs(output_dir, exist_ok=True)
```

## Docstrings

Use Google-style docstrings for public functions:

```python
def generate_video(
    script: Script,
    platform: Platform,
    output_dir: Path,
) -> Path:
    """Generate a video from a script for the specified platform.
    
    Args:
        script: The script containing scenes to render.
        platform: Target platform (YouTube or TikTok).
        output_dir: Directory to save the output video.
    
    Returns:
        Path to the generated video file.
    
    Raises:
        VideoAssemblyError: If FFmpeg fails during assembly.
    """
```

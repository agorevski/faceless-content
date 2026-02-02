# Service Layer Standards

## Service Architecture

Services contain business logic and coordinate between clients, models, and the pipeline.

```
┌─────────────────┐
│   CLI/Pipeline  │  ← Orchestration layer
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Services     │  ← Business logic (this layer)
│                 │
│  - Validation   │
│  - Coordination │
│  - Logging      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Clients      │  ← External API communication
└─────────────────┘
```

## Service Template

```python
"""Service for handling [description]."""

from pathlib import Path

from faceless.clients.azure_openai import AzureOpenAIClient
from faceless.config import Settings
from faceless.core.enums import Platform
from faceless.core.exceptions import ServiceError
from faceless.core.models import Scene, Script
from faceless.utils.logging import get_logger


class MyService:
    """Service for [description].
    
    This service handles [specific responsibilities].
    """

    def __init__(
        self,
        client: AzureOpenAIClient,
        settings: Settings,
    ) -> None:
        """Initialize the service.
        
        Args:
            client: Azure OpenAI client for API calls.
            settings: Application settings.
        """
        self.client = client
        self.settings = settings
        self.logger = get_logger(__name__)

    async def process(
        self,
        script: Script,
        platform: Platform,
        output_dir: Path,
    ) -> list[Path]:
        """Process a script and generate outputs.
        
        Args:
            script: The script to process.
            platform: Target platform.
            output_dir: Directory for output files.
        
        Returns:
            List of paths to generated files.
        
        Raises:
            ServiceError: If processing fails.
        """
        self.logger.info(
            "Starting processing",
            title=script.title,
            platform=platform.value,
            scenes=len(script.scenes),
        )
        
        output_dir.mkdir(parents=True, exist_ok=True)
        results: list[Path] = []
        
        for scene in script.scenes:
            try:
                result_path = await self._process_scene(
                    scene=scene,
                    platform=platform,
                    output_dir=output_dir,
                )
                results.append(result_path)
                
            except Exception as e:
                self.logger.error(
                    "Scene processing failed",
                    scene_number=scene.scene_number,
                    error=str(e),
                )
                raise ServiceError(
                    f"Failed to process scene {scene.scene_number}: {e}"
                ) from e
        
        self.logger.info("Processing complete", files=len(results))
        return results

    async def _process_scene(
        self,
        scene: Scene,
        platform: Platform,
        output_dir: Path,
    ) -> Path:
        """Process a single scene.
        
        Args:
            scene: Scene to process.
            platform: Target platform.
            output_dir: Output directory.
        
        Returns:
            Path to the generated file.
        """
        # Implementation here
        ...
```

## Existing Services

### EnhancerService (`enhancer_service.py`)
- Enhances scripts using GPT
- Improves narration flow and engagement
- Refines image prompts for consistency

### ImageService (`image_service.py`)
- Generates images for scenes
- Handles platform-specific sizing
- Applies visual style suffixes
- Supports checkpointing for resume

### TTSService (`tts_service.py`)
- Generates audio narration
- Configures niche-specific voices
- Calculates audio duration with ffprobe

### VideoService (`video_service.py`)
- Assembles final videos with FFmpeg
- Applies Ken Burns effect (zoom/pan)
- Mixes background music
- Generates platform-specific outputs

### DeepResearchService (`research_service.py`)
- Conducts deep research on topics using AI
- Supports 4 depth levels: quick, standard, deep, investigative
- Generates key findings, statistics, expert quotes
- Provides content structure recommendations
- Identifies follow-up topics and multi-video potential
- CLI: `faceless research "topic" -n niche -d depth`

### QualityService (`quality_service.py`)
- Evaluates script quality before production
- Scores hooks (0-10 scale) with 7.0 threshold
- Predicts retention curves and drop-off risks
- Analyzes engagement potential (comments, shares)
- Enforces quality gates before expensive generation
- Generates improved hook alternatives
- CLI: `faceless quality script.json --strict`

### TrendingService (`trending_service.py`)
- Discovers trending topics from Reddit and AI suggestions
- Categorizes topics: hot, rising, evergreen, viral potential
- Analyzes specific topic potential with scoring
- Suggests optimal content timing based on lifecycle
- Generates content calendar recommendations
- CLI: `faceless trending scary-stories --calendar`

## Service Guidelines

### 1. Single Responsibility
Each service handles one aspect of the pipeline:

```python
# ✅ Good - focused service
class ImageService:
    """Generates images for video scenes."""
    ...

# ❌ Bad - too many responsibilities
class ContentService:
    """Handles images, audio, video, and enhancement."""
    ...
```

### 2. Dependency Injection
Accept dependencies through constructor:

```python
# ✅ Good - injectable dependencies
class ImageService:
    def __init__(self, client: AzureOpenAIClient, settings: Settings):
        self.client = client
        self.settings = settings

# ❌ Bad - creates own dependencies
class ImageService:
    def __init__(self):
        self.client = AzureOpenAIClient()  # Hard to test
        self.settings = get_settings()
```

### 3. Structured Logging
Always log with context:

```python
# ✅ Good - structured context
self.logger.info(
    "Image generated",
    scene_number=scene.scene_number,
    platform=platform.value,
    path=str(output_path),
    duration_ms=elapsed_time,
)

# ❌ Bad - unstructured
self.logger.info(f"Generated image for scene {scene.scene_number}")
```

### 4. Error Handling
Use custom exceptions and preserve context:

```python
from faceless.core.exceptions import ImageGenerationError

try:
    image_data = await self.client.generate_image(prompt)
except Exception as e:
    self.logger.error("Image generation failed", prompt=prompt[:50], error=str(e))
    raise ImageGenerationError(f"Failed for scene {scene.scene_number}") from e
```

### 5. Async Operations
Use async for I/O-bound operations:

```python
import asyncio

async def process_all_scenes(self, scenes: list[Scene]) -> list[Path]:
    """Process multiple scenes concurrently."""
    tasks = [self._process_scene(scene) for scene in scenes]
    return await asyncio.gather(*tasks)
```

### 6. Progress Tracking
Support checkpointing for long operations:

```python
async def process_with_checkpoint(
    self,
    scenes: list[Scene],
    checkpoint: Checkpoint,
) -> list[Path]:
    """Process scenes with checkpoint support."""
    results: list[Path] = []
    
    for scene in scenes:
        if scene.scene_number in checkpoint.completed_scenes:
            self.logger.debug("Skipping completed", scene=scene.scene_number)
            continue
        
        result = await self._process_scene(scene)
        results.append(result)
        
        checkpoint.completed_scenes.add(scene.scene_number)
        checkpoint.save()
    
    return results
```

## Testing Services

```python
import pytest
from unittest.mock import AsyncMock, Mock

@pytest.fixture
def mock_client():
    """Create a mock Azure OpenAI client."""
    client = Mock(spec=AzureOpenAIClient)
    client.generate_image = AsyncMock(return_value=b"fake_image")
    return client

@pytest.fixture
def image_service(mock_client, mock_settings):
    """Create ImageService with mocked dependencies."""
    return ImageService(client=mock_client, settings=mock_settings)

@pytest.mark.asyncio
async def test_image_service_generates_for_scene(image_service, sample_scene):
    """Test that ImageService generates an image for a scene."""
    result = await image_service.generate_scene_image(
        scene=sample_scene,
        platform=Platform.YOUTUBE,
        output_dir=Path("/tmp/test"),
    )
    
    assert result.exists()
    image_service.client.generate_image.assert_called_once()
```

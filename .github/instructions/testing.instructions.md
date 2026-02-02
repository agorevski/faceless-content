# Testing Standards

## Test File Structure

```
tests/
├── __init__.py
├── conftest.py           # Shared fixtures
├── unit/
│   ├── __init__.py
│   ├── test_models.py    # Core model tests
│   ├── test_services.py  # Service layer tests
│   └── test_clients.py   # API client tests
└── integration/
    ├── __init__.py
    └── test_pipeline.py  # Full pipeline tests
```

## Test Naming

```python
# Pattern: test_{method}_{scenario}_{expected_result}

def test_script_validation_with_empty_scenes_raises_error():
    ...

def test_image_service_generate_returns_valid_path():
    ...

def test_tts_service_with_long_text_splits_correctly():
    ...
```

## Fixtures (conftest.py)

Common fixtures are defined in `tests/conftest.py`:

```python
import pytest
from faceless.core.models import Script, Scene, VisualStyle
from faceless.core.enums import Niche, Platform
from faceless.config import Settings

@pytest.fixture
def sample_scene() -> Scene:
    """Create a sample scene for testing."""
    return Scene(
        scene_number=1,
        narration="Test narration text.",
        image_prompt="A test image prompt.",
        duration_estimate=10.0,
    )

@pytest.fixture
def sample_script(sample_scene: Scene) -> Script:
    """Create a sample script with one scene."""
    return Script(
        title="Test Script",
        niche=Niche.SCARY_STORIES,
        scenes=[sample_scene],
    )

@pytest.fixture
def mock_settings() -> Settings:
    """Create mock settings for testing."""
    return Settings(
        azure_openai_endpoint="https://test.openai.azure.com/",
        azure_openai_api_key="test-key",
    )
```

## Markers

Use pytest markers to categorize tests:

```python
import pytest

@pytest.mark.unit
def test_model_validation():
    """Unit test - fast, no external dependencies."""
    ...

@pytest.mark.integration
def test_api_connection():
    """Integration test - requires external services."""
    ...

@pytest.mark.slow
def test_full_video_generation():
    """Slow test - takes more than 10 seconds."""
    ...
```

Run specific test categories:
```bash
pytest -m unit              # Only unit tests
pytest -m "not integration" # Skip integration tests
pytest -m "not slow"        # Skip slow tests
```

## Mocking External APIs

Use `respx` for HTTP mocking and `pytest-mock` for general mocking:

```python
import pytest
import respx
from httpx import Response

@pytest.mark.unit
@respx.mock
async def test_azure_client_generate_image():
    """Test image generation with mocked API."""
    # Mock the Azure OpenAI endpoint
    respx.post(
        "https://test.openai.azure.com/openai/deployments/gpt-image-1/images/generations"
    ).mock(
        return_value=Response(
            200,
            json={"data": [{"b64_json": "base64encodedimage"}]},
        )
    )
    
    client = AzureOpenAIClient(settings=mock_settings)
    result = await client.generate_image("test prompt")
    
    assert result is not None
    assert len(respx.calls) == 1


@pytest.mark.unit
def test_service_with_mocked_client(mocker):
    """Test service with mocked client."""
    mock_client = mocker.Mock(spec=AzureOpenAIClient)
    mock_client.generate_image.return_value = b"fake_image_data"
    
    service = ImageService(client=mock_client, settings=mock_settings)
    result = service.generate_scene_image(scene, Platform.YOUTUBE)
    
    mock_client.generate_image.assert_called_once()
```

## Async Testing

Use `pytest-asyncio` for async tests:

```python
import pytest

@pytest.mark.asyncio
async def test_async_image_generation():
    """Test async image generation."""
    service = ImageService(client=mock_client, settings=mock_settings)
    result = await service.generate_async(prompt="test")
    assert result is not None
```

The `asyncio_mode = "auto"` setting in `pyproject.toml` automatically handles async fixtures.

## Coverage Requirements

- Minimum 70% coverage required (enforced in CI)
- Coverage report: `pytest --cov=src/faceless --cov-report=html`
- View report: Open `coverage_html/index.html`

Focus coverage on:
- Business logic in services
- Validation in models
- Error handling paths

## Test Data

For test data files, use:

```python
from pathlib import Path

# Get path to test data
TEST_DATA_DIR = Path(__file__).parent / "data"

@pytest.fixture
def sample_script_json() -> dict:
    """Load sample script from test data."""
    script_path = TEST_DATA_DIR / "sample_script.json"
    return json.loads(script_path.read_text())
```

## Assertions

Use clear, specific assertions:

```python
# ✅ Good - specific assertions
assert result.title == "Expected Title"
assert len(result.scenes) == 3
assert result.scenes[0].scene_number == 1
assert "error" not in result.status.lower()

# ✅ Good - pytest.raises for exceptions
with pytest.raises(ValidationError) as exc_info:
    Script(title="", scenes=[])
assert "title" in str(exc_info.value)

# ❌ Bad - vague assertions
assert result
assert result is not None
```

## Running Tests

```bash
# All tests
pytest

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Run specific file
pytest tests/unit/test_models.py

# Run specific test
pytest tests/unit/test_models.py::test_script_validation

# With coverage
pytest --cov=src/faceless --cov-report=term-missing
```

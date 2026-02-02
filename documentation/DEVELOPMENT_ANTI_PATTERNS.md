# Development Anti-Patterns

This document identifies development anti-patterns found in the faceless-content repository. Each anti-pattern is documented with its location, impact, and recommended resolution.

---

## Table of Contents

1. [AP-005: Overly Broad Exception Handling](#ap-005-overly-broad-exception-handling)
2. [AP-006: Mutable Default Arguments](#ap-006-mutable-default-arguments)
3. [AP-008: Missing Type Hints in Legacy Code](#ap-008-missing-type-hints-in-legacy-code)
4. [AP-009: Inconsistent Configuration Access Patterns](#ap-009-inconsistent-configuration-access-patterns)
5. [AP-012: Missing Input Validation in Pipeline Modules](#ap-012-missing-input-validation-in-pipeline-modules)
6. [AP-013: Subprocess Calls Without Proper Error Handling](#ap-013-subprocess-calls-without-proper-error-handling)
7. [AP-014: Inconsistent File Encoding Handling](#ap-014-inconsistent-file-encoding-handling)
8. [AP-015: Optional Dependencies Not Declared](#ap-015-optional-dependencies-not-declared)

---

## AP-005: Overly Broad Exception Handling

### Description
Many `except Exception as e:` blocks catch all exceptions without distinguishing between different failure modes. This can mask bugs, hide important errors, and make debugging difficult.

### Locations
- `pipeline/image_generator.py:165`
- `pipeline/pipeline.py:193, 218, 231, 312, 325, 329`
- `pipeline/script_enhancer.py:464, 489`
- `pipeline/test_apis.py:61, 124, 150`
- `pipeline/thumbnail_generator.py:281`
- `pipeline/tts_generator.py:223`
- `pipeline/video_assembler.py:389`

### Impact
- **High**: Bugs can be silently swallowed
- **High**: Debugging becomes difficult
- **Medium**: No distinction between recoverable and fatal errors

### Evidence
```python
# pipeline/pipeline.py
try:
    enhanced_path = enhance_script(sp, niche)
    enhanced_paths.append(enhanced_path)
except Exception as e:
    print(f"   ⚠️ Enhancement failed for {sp}: {e}")
    print("   Continuing with original script...")
    enhanced_paths.append(sp)
    results["errors"].append(f"Enhancement: {e}")
```

### Resolution
1. Use the custom exception hierarchy from `src/faceless/core/exceptions.py`
2. Catch specific exceptions and handle them appropriately:
   ```python
   from faceless.core.exceptions import (
       ImageGenerationError,
       TTSGenerationError,
       AzureOpenAIError,
   )
   
   try:
       enhanced_path = enhance_script(sp, niche)
   except AzureOpenAIError as e:
       logger.error("API call failed", error=str(e))
       # Handle API-specific error
   except json.JSONDecodeError as e:
       logger.error("Invalid JSON response", error=str(e))
       # Handle parse error
   except Exception as e:
       logger.exception("Unexpected error")
       raise  # Re-raise unexpected errors
   ```

---

## AP-006: Mutable Default Arguments

### Description
Several functions use mutable default arguments like `list` or `dict`, which is a well-known Python anti-pattern that can cause unexpected behavior.

### Locations
- `pipeline/pipeline.py:85`: `platforms: list = None` (acceptable pattern)
- `pipeline/pipeline.py:356`: `platforms: list = None` (acceptable pattern)

### Impact
- **Low**: The current code assigns `None` as default and checks, which is the correct pattern
- **Note**: This is actually done correctly in this codebase, included for completeness

### Evidence
```python
# pipeline/pipeline.py - This is actually the CORRECT pattern
def full_pipeline(
    niche: str,
    story_count: int = 1,
    platforms: list = None,  # Correct: uses None, not []
    ...
) -> dict:
    if platforms is None:
        platforms = ["youtube", "tiktok"]  # Create new list
```

### Resolution
None needed - the current implementation correctly uses `None` defaults and creates new lists inside the function.

---

## AP-008: Missing Type Hints in Legacy Code

### Description
The `pipeline/` modules lack comprehensive type hints, making the code harder to understand and preventing static analysis tools from catching bugs.

### Locations
- All files in `pipeline/` directory
- Compare to fully typed files in `src/faceless/`

### Impact
- **Medium**: IDE cannot provide accurate autocomplete
- **Medium**: Type-related bugs not caught before runtime
- **Low**: Documentation is less clear

### Evidence
```python
# pipeline/story_scraper.py - No return type hints
def fetch_reddit_stories(
    subreddit: str = "nosleep",
    limit: int = 10,
    time_filter: str = "month",
    min_score: int = 100,
) -> list:  # Should be list[dict[str, Any]]
```

vs.

```python
# src/faceless/services/image_service.py - Fully typed
def generate_for_script(
    self,
    script: Script,
    platform: Platform,
    checkpoint: Checkpoint | None = None,
) -> list[Path]:
```

### Resolution
1. Add comprehensive type hints to all `pipeline/` modules
2. Use `mypy` in strict mode for the pipeline directory
3. Add type hints for return values (not just `-> list` but `-> list[dict[str, Any]]`)

---

## AP-009: Inconsistent Configuration Access Patterns

### Description
Configuration is accessed through multiple different patterns:
1. Direct import of uppercase constants (`from env_config import AZURE_OPENAI_KEY`)
2. Singleton settings object (`get_settings()`)
3. Function calls (`get_legacy_paths()`)

### Locations
- `pipeline/env_config.py`: Exports uppercase constants
- `pipeline/*.py`: Import uppercase constants
- `src/faceless/config/settings.py`: Modern pydantic settings
- `src/faceless/**/*.py`: Use `get_settings()` function

### Impact
- **Medium**: Confusion about which pattern to use
- **Medium**: Harder to test (can't easily mock constants)
- **Low**: Configuration changes may not propagate correctly

### Evidence
```python
# pipeline/image_generator.py - Legacy pattern
from env_config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_IMAGE_DEPLOYMENT,
)

# src/faceless/clients/azure_openai.py - Modern pattern
from faceless.config import get_settings
settings = get_settings()
endpoint = settings.azure_openai.endpoint
```

### Resolution
1. Standardize on `get_settings()` pattern across all code
2. Deprecate uppercase constant exports in `env_config.py`
3. Update all `pipeline/` modules to use settings object
4. Add deprecation warnings to legacy access patterns

---

## AP-012: Missing Input Validation in Pipeline Modules

### Description
Pipeline modules often accept user input without thorough validation, potentially leading to:
- Cryptic error messages later in the pipeline
- Security issues with path traversal
- Unexpected behavior with edge cases

### Locations
- `pipeline/story_scraper.py`: No validation of subreddit names
- `pipeline/image_generator.py`: No validation of prompts
- `pipeline/pipeline.py`: Limited validation of niche values

### Impact
- **Medium**: Poor error messages for invalid input
- **Medium**: Potential security issues
- **Low**: Edge cases may cause crashes

### Evidence
```python
# pipeline/story_scraper.py - No validation
def fetch_reddit_stories(
    subreddit: str = "nosleep",  # What if subreddit has invalid characters?
    limit: int = 10,              # What if limit is negative?
    ...
):
```

### Resolution
1. Use Pydantic models for input validation (as done in `src/faceless/core/models.py`)
2. Add validation at function entry points
3. Provide clear error messages for invalid input
4. Consider using `typing.Literal` for fixed choices

---

## AP-013: Subprocess Calls Without Proper Error Handling

### Description
Several FFmpeg subprocess calls in `pipeline/video_assembler.py` check return codes but don't capture or log stderr content when debugging is needed.

### Locations
- `pipeline/video_assembler.py:27-28`: `get_audio_duration` - no error handling
- `pipeline/video_assembler.py:41-47`: `get_image_dimensions` - no error handling
- `pipeline/video_assembler.py:541`: `create_tiktok_cuts` - silent failure

### Impact
- **Medium**: Silent failures when FFmpeg isn't installed
- **Medium**: No way to diagnose FFmpeg issues
- **Low**: Process may hang on large files

### Evidence
```python
# pipeline/video_assembler.py
def get_audio_duration(audio_path: str) -> float:
    cmd = ["ffprobe", "-v", "error", ...]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())  # What if ffprobe fails?
```

### Resolution
1. Add proper error checking:
   ```python
   def get_audio_duration(audio_path: str) -> float:
       result = subprocess.run(cmd, capture_output=True, text=True)
       if result.returncode != 0:
           raise FFmpegError(
               message="Failed to get audio duration",
               command=cmd,
               return_code=result.returncode,
               stderr=result.stderr,
           )
       try:
           return float(result.stdout.strip())
       except ValueError as e:
           raise FFmpegError(f"Invalid duration output: {result.stdout}") from e
   ```

---

## AP-014: Inconsistent File Encoding Handling

### Description
While many file operations specify `encoding="utf-8"`, some don't, which can cause issues on Windows or with non-ASCII content.

### Locations
Most files are consistent, but verify all `open()` calls include encoding.

### Impact
- **Low**: Potential issues with non-ASCII characters
- **Low**: Platform-dependent behavior

### Evidence
```python
# Good - explicit encoding
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(script, f, indent=2, ensure_ascii=False)

# Potentially problematic - ensure all file operations specify encoding
```

### Resolution
1. Audit all `open()` calls to ensure `encoding="utf-8"` is specified
2. Use `pathlib.Path.read_text(encoding="utf-8")` and `Path.write_text(encoding="utf-8")`
3. Add a pre-commit hook or linter rule to enforce encoding specification

---

## AP-015: Optional Dependencies Not Declared

### Description
Some modules import packages that aren't listed in `pyproject.toml` dependencies, potentially causing runtime failures.

### Potential Issues
- `pipeline/` modules may use packages not in dependencies
- Some features may fail if optional packages aren't installed

### Impact
- **Medium**: Runtime ImportError in production
- **Low**: Confusion about what to install

### Resolution
1. Audit all imports in `pipeline/` against `pyproject.toml`
2. Add missing dependencies to appropriate dependency groups
3. Use optional dependency groups for non-core features:
   ```toml
   [project.optional-dependencies]
   pipeline = ["requests"]  # For legacy pipeline
   ```

---

## Summary Priority Matrix

| Priority | Anti-Pattern | Status |
|----------|-------------|--------|
| 🟡 Medium | AP-005: Broad Exception Handling | Remaining in some services |
| 🟢 Low | AP-006: Mutable Default Arguments | Already correct pattern |
| 🟡 Medium | AP-008: Missing Type Hints | All new code has type hints |
| 🟡 Medium | AP-009: Config Access Patterns | Modern code uses get_settings() |
| 🟡 Medium | AP-012: Missing Validation | Some services need validation |
| 🟡 Medium | AP-013: Subprocess Errors | Some subprocess calls need better handling |
| 🟢 Low | AP-014: File Encoding | Most code specifies encoding |
| 🟢 Low | AP-015: Undeclared Dependencies | Dependencies are properly declared |

---

## Remaining Work

The following anti-patterns still need attention:

1. **AP-005: Broad Exception Handling** - Some services still use overly broad exception catching
2. **AP-008: Missing Type Hints** - Legacy services may need type hint additions
3. **AP-012: Missing Validation** - Some service functions lack input validation
4. **AP-013: Subprocess Errors** - FFmpeg calls could have better error handling

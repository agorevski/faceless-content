# Development Anti-Patterns

This document identifies development anti-patterns found in the faceless-content repository. Each anti-pattern is documented with its location, impact, and recommended resolution.

---

## Table of Contents

1. [AP-001: Duplicated Architecture (Legacy Pipeline vs Modern src/)](#ap-001-duplicated-architecture-legacy-pipeline-vs-modern-src)
2. [AP-002: sys.path Manipulation](#ap-002-syspath-manipulation)
3. [AP-003: Mixed HTTP Client Libraries](#ap-003-mixed-http-client-libraries)
4. [AP-004: Print Statements Instead of Structured Logging](#ap-004-print-statements-instead-of-structured-logging)
5. [AP-005: Overly Broad Exception Handling](#ap-005-overly-broad-exception-handling)
6. [AP-006: Mutable Default Arguments](#ap-006-mutable-default-arguments)
7. [AP-007: Hardcoded Magic Numbers and Strings](#ap-007-hardcoded-magic-numbers-and-strings)
8. [AP-008: Missing Type Hints in Legacy Code](#ap-008-missing-type-hints-in-legacy-code)
9. [AP-009: Inconsistent Configuration Access Patterns](#ap-009-inconsistent-configuration-access-patterns)
10. [AP-010: Global Module-Level Imports with Try/Except Fallbacks](#ap-010-global-module-level-imports-with-tryexcept-fallbacks)
11. [AP-011: Code Duplication Between Pipeline and src/faceless](#ap-011-code-duplication-between-pipeline-and-srcfaceless)
12. [AP-012: Missing Input Validation in Pipeline Modules](#ap-012-missing-input-validation-in-pipeline-modules)
13. [AP-013: Subprocess Calls Without Proper Error Handling](#ap-013-subprocess-calls-without-proper-error-handling)
14. [AP-014: Inconsistent File Encoding Handling](#ap-014-inconsistent-file-encoding-handling)
15. [AP-015: Optional Dependencies Not Declared](#ap-015-optional-dependencies-not-declared)

---

## AP-001: Duplicated Architecture (Legacy Pipeline vs Modern src/)

### Description
The repository contains two parallel implementations:
- **Legacy**: `pipeline/` directory with standalone modules
- **Modern**: `src/faceless/` directory with properly structured package

This creates maintenance burden, confusion about which code to use, and potential inconsistencies between implementations.

### Locations
- `pipeline/*.py` (17 files)
- `src/faceless/` (structured package)

### Impact
- **High**: Bugs may be fixed in one location but not the other
- **High**: New developers may not know which codebase to extend
- **Medium**: Double testing burden

### Evidence
```
pipeline/
├── image_generator.py      ← Legacy implementation
├── tts_generator.py        ← Legacy implementation
├── video_assembler.py      ← Legacy implementation
└── ...

src/faceless/
├── services/
│   ├── image_service.py    ← Modern implementation
│   ├── tts_service.py      ← Modern implementation
│   └── video_service.py    ← Modern implementation
└── ...
```

### Resolution
1. Migrate all functionality from `pipeline/` to `src/faceless/`
2. Create thin wrappers in `pipeline/` that delegate to `src/faceless/` for backward compatibility
3. Deprecate and eventually remove the `pipeline/` directory
4. Update documentation to reference only `src/faceless/`

---

## AP-002: sys.path Manipulation

### Description
Multiple files manipulate `sys.path` at import time to enable cross-directory imports. This is a fragile pattern that:
- Breaks when files are moved
- Creates import order dependencies
- Makes the codebase harder to package properly

### Locations
```
pipeline/env_config.py:18:    sys.path.insert(0, str(_src_path))
pipeline/env_config.py:23:    sys.path.insert(0, str(_shared_path))
pipeline/pipeline.py:20:      sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
pipeline/subtitle_generator.py:15
pipeline/test_apis.py:9
pipeline/thumbnail_generator.py:16
tests/unit/test_content_metadata.py:12
tests/unit/test_hashtags.py:12
tests/unit/test_hooks.py:12
tests/unit/test_posting_schedule.py:13
tests/unit/test_text_overlay.py:12
tests/unit/test_tiktok_formats.py:12
```

### Impact
- **High**: Brittle imports that break on refactoring
- **Medium**: Cannot be properly packaged/distributed
- **Medium**: IDE tools may not resolve imports correctly

### Evidence
```python
# pipeline/env_config.py
import sys
from pathlib import Path

_src_path = Path(__file__).parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))
```

### Resolution
1. Use proper Python packaging with `pyproject.toml` (already partially done)
2. Install the package in development mode: `pip install -e .`
3. Remove all `sys.path` manipulations
4. Use proper relative or absolute imports based on package structure
5. Configure pytest to discover packages correctly via `pythonpath` in `pyproject.toml`

---

## AP-003: Mixed HTTP Client Libraries

### Description
The codebase uses two different HTTP client libraries:
- **Modern code**: Uses `httpx` (in `src/faceless/clients/`)
- **Legacy code**: Uses `requests` (in `pipeline/`)

This inconsistency means:
- Two sets of error handling patterns
- No shared retry/timeout configuration
- Async support limitations

### Locations
Using `requests`:
- `pipeline/image_generator.py`
- `pipeline/script_enhancer.py`
- `pipeline/story_scraper.py`
- `pipeline/test_apis.py`
- `pipeline/thumbnail_generator.py`
- `pipeline/tts_generator.py`

Using `httpx`:
- `src/faceless/clients/base.py`
- `src/faceless/clients/azure_openai.py`

### Impact
- **Medium**: Inconsistent error handling
- **Medium**: Different timeout/retry behavior
- **Low**: Increased dependency footprint

### Evidence
```python
# pipeline/image_generator.py (legacy - uses requests)
import requests
response = requests.post(url, headers=headers, json=payload, timeout=120)

# src/faceless/clients/base.py (modern - uses httpx)
import httpx
response = self._client.request(method, path, **kwargs)
```

### Resolution
1. Standardize on `httpx` across the entire codebase
2. Migrate all `pipeline/` modules to use the `BaseHTTPClient` from `src/faceless/clients/base.py`
3. Remove `requests` from dependencies if no longer needed

---

## AP-004: Print Statements Instead of Structured Logging

### Description
The `pipeline/` directory uses `print()` statements extensively for output instead of using the structured logging system available in `src/faceless/utils/logging.py`.

### Locations
The `pipeline/` directory has **~230+ print statements** spread across 17 files:
- `pipeline/pipeline.py`: 54 print statements
- `pipeline/env_config.py`: 24 print statements
- `pipeline/script_enhancer.py`: 22 print statements
- `pipeline/video_assembler.py`: 20 print statements
- (and many more)

### Impact
- **High**: No log levels (can't filter warnings from info)
- **High**: No structured metadata for log aggregation
- **Medium**: No file logging support
- **Medium**: Inconsistent output formatting

### Evidence
```python
# pipeline/pipeline.py
print(f"\n{'='*60}")
print("🎬 FACELESS CONTENT PIPELINE")
print(f"   Niche: {niche}")
# ... many more print statements

# Compare to src/faceless/services/video_service.py (proper logging)
self.logger.info(
    "Created scene video",
    scene_number=scene.scene_number,
    output=str(output_path),
)
```

### Resolution
1. Import and use `LoggerMixin` from `faceless.utils.logging` in all pipeline modules
2. Replace all `print()` calls with appropriate `self.logger.info()`, `self.logger.error()`, etc.
3. Use structured logging with key-value pairs for machine-parseable output
4. Consider using `rich` console for CLI output that needs formatting

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

## AP-007: Hardcoded Magic Numbers and Strings

### Description
Various magic numbers and strings are hardcoded throughout the codebase instead of being defined as named constants or configuration values.

### Locations
- `pipeline/image_generator.py:84`: `timeout=120`
- `pipeline/tts_generator.py:74`: `timeout=180`
- `pipeline/tts_generator.py:149`: `timeout=120`
- `pipeline/story_scraper.py:69`: `timeout=30`
- `pipeline/story_scraper.py:161`: `words_per_scene: int = 150`
- `pipeline/video_assembler.py:106`: `scale_factor = 1.15`
- `pipeline/video_assembler.py:157`: Various FFmpeg parameters

### Impact
- **Medium**: Difficult to tune behavior without code changes
- **Medium**: Same values repeated in multiple places
- **Low**: No documentation of what values mean

### Evidence
```python
# pipeline/image_generator.py
response = requests.post(url, headers=headers, json=payload, timeout=120)

# pipeline/tts_generator.py
response = requests.post(url, headers=headers, json=payload, timeout=180)
```

### Resolution
1. Define timeout constants in settings:
   ```python
   # In Settings class
   image_generation_timeout: int = Field(default=120)
   tts_generation_timeout: int = Field(default=180)
   ```
2. Create a constants module for algorithm-specific values:
   ```python
   # constants.py
   TTS_WORDS_PER_MINUTE = 150
   KEN_BURNS_SCALE_FACTOR = 1.15
   ```

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

## AP-010: Global Module-Level Imports with Try/Except Fallbacks

### Description
Several modules use try/except at module level to handle optional imports, setting flags to indicate availability. This pattern is fragile and makes dependency management unclear.

### Locations
- `pipeline/pipeline.py:30-35`: Optional `content_metadata` import
- `pipeline/script_enhancer.py:27-36`: Optional `hooks` import

### Impact
- **Medium**: Features silently degrade without warning
- **Medium**: Unclear which dependencies are truly optional
- **Low**: Testing all code paths is difficult

### Evidence
```python
# pipeline/pipeline.py
try:
    from content_metadata import generate_content_metadata, save_metadata
    ENGAGEMENT_MODULES_AVAILABLE = True
except ImportError:
    ENGAGEMENT_MODULES_AVAILABLE = False
```

### Resolution
1. Declare all dependencies in `pyproject.toml` (required vs optional)
2. Use explicit optional dependency groups:
   ```toml
   [project.optional-dependencies]
   engagement = ["some-package"]
   ```
3. Provide clear error messages when optional features are used without dependencies
4. Document which features require which optional dependencies

---

## AP-011: Code Duplication Between Pipeline and src/faceless

### Description
Similar functionality is implemented twice with slight differences, leading to:
- Different behavior for the same operations
- Bugs fixed in one place but not the other
- Wasted development effort

### Examples
| Feature | Pipeline Location | src/faceless Location |
|---------|------------------|----------------------|
| Image generation | `pipeline/image_generator.py` | `src/faceless/services/image_service.py` |
| TTS generation | `pipeline/tts_generator.py` | `src/faceless/services/tts_service.py` |
| Video assembly | `pipeline/video_assembler.py` | `src/faceless/services/video_service.py` |
| Checkpointing | `pipeline/pipeline.py` | `src/faceless/core/models.py` (Checkpoint class) |

### Impact
- **High**: Maintenance burden is doubled
- **High**: Inconsistent behavior between entry points
- **Medium**: Harder to understand the system

### Resolution
1. Identify the "canonical" implementation for each feature
2. Create adapters in `pipeline/` that delegate to `src/faceless/`
3. Gradually migrate all logic to `src/faceless/`
4. Consider removing `pipeline/` entirely once migration is complete

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

| Priority | Anti-Pattern | Effort | Impact |
|----------|-------------|--------|--------|
| 🔴 Critical | AP-001: Duplicated Architecture | High | High |
| 🔴 Critical | AP-004: Print Statements | Medium | High |
| 🔴 Critical | AP-005: Broad Exception Handling | Medium | High |
| 🟠 High | AP-002: sys.path Manipulation | Medium | Medium |
| 🟠 High | AP-003: Mixed HTTP Libraries | Medium | Medium |
| 🟠 High | AP-011: Code Duplication | High | High |
| 🟡 Medium | AP-007: Magic Numbers | Low | Medium |
| 🟡 Medium | AP-008: Missing Type Hints | Medium | Medium |
| 🟡 Medium | AP-009: Config Access Patterns | Medium | Medium |
| 🟡 Medium | AP-012: Missing Validation | Medium | Medium |
| 🟡 Medium | AP-013: Subprocess Errors | Low | Medium |
| 🟢 Low | AP-010: Optional Import Fallbacks | Low | Medium |
| 🟢 Low | AP-014: File Encoding | Low | Low |
| 🟢 Low | AP-015: Undeclared Dependencies | Low | Medium |

---

## Recommended Resolution Order

1. **Phase 1 - Quick Wins** (1-2 days)
   - AP-005: Fix overly broad exception handling
   - AP-007: Extract magic numbers to constants
   - AP-014: Ensure consistent encoding

2. **Phase 2 - Logging & Error Handling** (1 week)
   - AP-004: Replace print statements with structured logging
   - AP-013: Add proper subprocess error handling

3. **Phase 3 - Architecture Consolidation** (2-4 weeks)
   - AP-001/AP-011: Consolidate pipeline/ into src/faceless/
   - AP-002: Remove sys.path manipulation
   - AP-003: Standardize on httpx

4. **Phase 4 - Type Safety & Validation** (1-2 weeks)
   - AP-008: Add type hints to all modules
   - AP-012: Add input validation
   - AP-009: Standardize configuration access

5. **Phase 5 - Cleanup** (1 week)
   - AP-010: Clean up optional import handling
   - AP-015: Audit and declare all dependencies

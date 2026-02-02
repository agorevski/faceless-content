# Development Anti-Patterns

This document identifies development anti-patterns found in the faceless-content repository. Each anti-pattern is documented with its location, impact, and recommended resolution.

> **Last Review Date:** 2026-02-02

---

## Table of Contents

1. [AP-016: Unimplemented TODO Stubs](#ap-016-unimplemented-todo-stubs)
2. [AP-017: Silent Exception Swallowing](#ap-017-silent-exception-swallowing)
3. [AP-018: Synchronous asyncio.run in CLI](#ap-018-synchronous-asynciorun-in-cli)
4. [AP-019: Magic Numbers in Services](#ap-019-magic-numbers-in-services)
5. [AP-005: Overly Broad Exception Handling](#ap-005-overly-broad-exception-handling)
6. [AP-006: Mutable Default Arguments](#ap-006-mutable-default-arguments)

---

## AP-016: Unimplemented TODO Stubs ⚠️ ACTIVE

### Status: NEEDS ATTENTION
**Severity:** Medium
**Location:** `src/faceless/pipeline/orchestrator.py:311, 323`

### Description
The orchestrator contains TODO comments for unimplemented thumbnail and subtitle generation. These stubs mark steps as completed without performing any actual work:

```python
# Step 5: Generate thumbnails (optional)
if thumbnails and not errors and "thumbnails" not in checkpoint.completed_steps:
    self.logger.info("Starting thumbnail generation...")
    checkpoint.status = JobStatus.GENERATING_THUMBNAILS
    # TODO: Implement thumbnail generation
    checkpoint.completed_steps.append("thumbnails")  # ← Marked done with no work
    self.logger.info("Thumbnail generation completed")

# Step 6: Generate subtitles (optional)
if subtitles and not errors and "subtitles" not in checkpoint.completed_steps:
    self.logger.info("Starting subtitle generation...")
    checkpoint.status = JobStatus.GENERATING_SUBTITLES
    # TODO: Implement subtitle generation
    checkpoint.completed_steps.append("subtitles")  # ← Marked done with no work
    self.logger.info("Subtitle generation completed")
```

### Impact
- Users may expect thumbnail/subtitle generation when passing `--thumbnails` or `--subtitles` flags
- Checkpoint incorrectly records successful completion of these steps
- Misleading log messages ("Thumbnail generation completed") when nothing was generated

### Recommended Resolution
1. Either implement the pending features, OR
2. Remove the flags and code blocks if not planned, OR
3. Log a warning indicating these features are not yet implemented

```python
# Better temporary pattern
if thumbnails:
    self.logger.warning(
        "Thumbnail generation not yet implemented",
        feature="thumbnails",
    )
```

---

## AP-017: Silent Exception Swallowing ⚠️ ACTIVE

### Status: NEEDS ATTENTION
**Severity:** Low
**Location:** `src/faceless/services/sources/wikipedia_source.py:240-241`

### Description
Some exception handlers use `pass` which silently swallows errors without logging:

```python
try:
    featured = await self._get_featured_article()
    if featured:
        content.append(featured)
except ContentFetchError:
    pass  # ← Silent failure with no logging
```

### Impact
- Debugging becomes difficult when featured article fetch fails
- No visibility into failure rates or patterns
- Cannot distinguish between "no featured article" and "fetch error"

### Recommended Resolution
Log at debug or warning level before continuing:

```python
except ContentFetchError as e:
    self.logger.debug("Featured article fetch failed, continuing", error=str(e))
```

---

## AP-018: Synchronous asyncio.run in CLI ⚠️ ACTIVE

### Status: ACCEPTABLE (with caveats)
**Severity:** Low
**Location:** `src/faceless/cli/commands.py:1143, 1147, 1153, 1208`

### Description
The CLI commands use `asyncio.run()` to call async functions synchronously:

```python
content = asyncio.run(
    service.fetch_trending(niche, limit=count, sources=source_types)
)
```

### Impact
- Each `asyncio.run()` creates a new event loop, adding overhead
- Cannot benefit from concurrent I/O across multiple CLI operations
- Pattern works but is not optimal for async-heavy code

### Acceptable Because
- CLI commands are typically single operations
- Typer does not natively support async command handlers
- Overhead is minimal for typical use cases

### Future Improvement
Consider using `asyncer` or a custom async runner if more async operations are added:

```python
# Alternative: Use asyncer for cleaner async CLI
from asyncer import runnify

@app.command()
def scrape(niche: Niche):
    content = runnify(service.fetch_trending)(niche, limit=count)
```

---

## AP-019: Magic Numbers in Services ⚠️ ACTIVE

### Status: MINOR CONCERN
**Severity:** Low
**Location:** Multiple service files

### Description
Some hardcoded values exist in service code that could be configuration:

```python
# research_service.py:239-242
ResearchDepth.QUICK: 1500,
ResearchDepth.STANDARD: 3000,
ResearchDepth.DEEP: 5000,
ResearchDepth.INVESTIGATIVE: 8000,

# trending_service.py:366-369
volume_map = {"high": 80000, "medium": 30000, "low": 10000}

# video_service.py:196
f"zoompan=z='min(zoom+0.0005,1.05)':d={int(duration * 25)}:s={width}x{height}:fps=25"
#                 ↑ 0.0005 zoom increment, 1.05 max zoom
```

### Impact
- Values cannot be customized without code changes
- Magic numbers are unclear without comments
- Testing different values requires code modification

### Acceptable Because
- Most magic numbers are domain-specific defaults
- Primary configuration (resolution, API settings) is properly in Settings
- Adding every value to config would create config bloat

### Recommendation
Add inline comments explaining non-obvious values:

```python
# Zoom 0.05% per frame for subtle Ken Burns effect
zoom_increment = 0.0005
max_zoom = 1.05  # Max 5% zoom to avoid quality loss
```

---

## AP-005: Overly Broad Exception Handling ✅ ACCEPTABLE

### Status: ACCEPTABLE PATTERN
**Review Date:** 2026-02-02

### Description
The codebase uses `except Exception as e:` blocks at appropriate boundaries:

1. **CLI command handlers** (`cli/commands.py`) - Top-level exception handling for user-friendly error display
2. **Pipeline orchestrator** (`pipeline/orchestrator.py`) - Orchestration boundaries catch and report all errors
3. **API clients** (`clients/azure_openai.py`) - Network operations need broad handling with proper logging
4. **Service methods** - Individual operations log and re-raise or handle gracefully

### Acceptable Patterns
```python
# CLI boundary - acceptable (must show user-friendly errors)
@app.command()
def generate(...):
    try:
        # ... command logic
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

# Service re-raising with custom exception - preferred
except (ImageGenerationError, ContentFilterError):
    raise
except Exception as e:
    self.logger.error("Image generation failed", error=str(e))
    raise ImageGenerationError(f"Unexpected error: {e}") from e
```

### Resolution
No changes needed. Current usage follows best practices.

---

## AP-006: Mutable Default Arguments ✅ RESOLVED

### Status: RESOLVED (No Action Needed)

### Description
The codebase correctly uses `None` defaults instead of mutable defaults:

```python
# Correct pattern used throughout codebase
def process_scenes(
    scenes: list[Scene],
    options: dict[str, Any] | None = None,
) -> list[Path]:
    if options is None:
        options = {}
```

### Resolution
None needed - the current implementation is correct.

---

## Summary

| Anti-Pattern | Status | Priority | Notes |
|-------------|--------|----------|-------|
| AP-016: Unimplemented TODO Stubs | ⚠️ Active | Medium | Orchestrator has fake completion |
| AP-017: Silent Exception Swallowing | ⚠️ Active | Low | Wikipedia source lacks logging |
| AP-018: Synchronous asyncio.run | ✅ Acceptable | Low | CLI pattern is fine |
| AP-019: Magic Numbers in Services | ⚠️ Minor | Low | Add comments to clarify |
| AP-005: Broad Exception Handling | ✅ Acceptable | - | Appropriate at boundaries |
| AP-006: Mutable Default Arguments | ✅ Resolved | - | Correctly uses None |

---

## Previously Resolved Anti-Patterns

These anti-patterns were identified and resolved in previous reviews:

| Anti-Pattern | Status | Resolution |
|-------------|--------|------------|
| AP-001: Duplicated Architecture | ✅ Resolved | Legacy `pipeline/` removed |
| AP-002: sys.path Manipulation | ✅ Resolved | No more sys.path hacks |
| AP-003: Mixed HTTP Libraries | ✅ Resolved | All code uses httpx |
| AP-004: Print Statements | ✅ Resolved | Uses structured logging via Rich console |
| AP-007: Magic Numbers | ✅ Mostly Resolved | Primary config in Settings |
| AP-008: Missing Type Hints | ✅ Resolved | All code fully typed |
| AP-009: Config Access Patterns | ✅ Resolved | Uses `get_settings()` |
| AP-010: Optional Import Fallbacks | ✅ Resolved | No try/except imports |
| AP-011: Code Duplication | ✅ Resolved | Single source of truth |
| AP-012: Missing Validation | ✅ Resolved | Uses Pydantic models |
| AP-013: Subprocess Errors | ✅ Resolved | Proper error handling |
| AP-014: File Encoding | ✅ Resolved | All files specify UTF-8 |
| AP-015: Undeclared Dependencies | ✅ Resolved | Dependencies declared |

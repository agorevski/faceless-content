# Development Anti-Patterns

This document identifies development anti-patterns found in the faceless-content repository. Each anti-pattern is documented with its location, impact, and recommended resolution.

> **Note:** The legacy `pipeline/` directory has been completely removed. All code now lives in `src/faceless/` with proper structure and patterns. This document is retained for historical reference and to document ongoing considerations.

---

## Table of Contents

1. [AP-005: Overly Broad Exception Handling](#ap-005-overly-broad-exception-handling)
2. [AP-006: Mutable Default Arguments](#ap-006-mutable-default-arguments)

---

## AP-005: Overly Broad Exception Handling ✅ ACCEPTABLE

### Status: ACCEPTABLE PATTERN
**Review Date:** 2026-02-02

### Description
The codebase uses `except Exception as e:` blocks in certain locations. While this was flagged as an anti-pattern, analysis shows the usage is appropriate:

1. **CLI command handlers** (`cli/commands.py`) - Top-level exception handling for user-friendly error display is necessary
2. **Pipeline orchestrator** (`pipeline/orchestrator.py`) - Orchestration boundaries need to catch and report all errors
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

# Service method with specific handling - preferred
try:
    result = await client.generate_image(prompt)
except httpx.TimeoutException:
    logger.error("API timeout", prompt=prompt[:50])
    raise ImageGenerationError("Request timed out")
except httpx.HTTPStatusError as e:
    logger.error("API error", status=e.response.status_code)
    raise ImageGenerationError(f"API returned {e.response.status_code}")
```

### Resolution
No changes needed. The current usage follows best practices:
- CLI/orchestrator boundaries use broad exception handling appropriately
- Service methods catch specific exceptions where possible
- All exceptions are logged with context using structlog

---

## AP-006: Mutable Default Arguments ✅ RESOLVED

### Status: RESOLVED (No Action Needed)

### Description
This was flagged for completeness, but the codebase already uses the correct pattern.

### Evidence
```python
# Correct pattern used throughout codebase
def process_scenes(
    scenes: list[Scene],
    options: dict[str, Any] | None = None,  # Uses None, not {} or []
) -> list[Path]:
    if options is None:
        options = {}  # Create new dict inside function
```

### Resolution
None needed - the current implementation correctly uses `None` defaults.

---

## Summary

All anti-patterns have been resolved or determined to be acceptable:

| Anti-Pattern | Status | Notes |
|-------------|--------|-------|
| AP-001: Duplicated Architecture | ✅ Resolved | `pipeline/` removed |
| AP-002: sys.path Manipulation | ✅ Resolved | No more sys.path hacks |
| AP-003: Mixed HTTP Libraries | ✅ Resolved | All code uses httpx |
| AP-004: Print Statements | ✅ Resolved | Uses structured logging |
| AP-005: Broad Exception Handling | ✅ Acceptable | Appropriate at boundaries |
| AP-006: Mutable Default Arguments | ✅ Resolved | Already correct pattern |
| AP-007: Magic Numbers | ✅ Resolved | Extracted to settings |
| AP-008: Missing Type Hints | ✅ Resolved | All code fully typed |
| AP-009: Config Access Patterns | ✅ Resolved | Uses `get_settings()` |
| AP-010: Optional Import Fallbacks | ✅ Resolved | No try/except imports |
| AP-011: Code Duplication | ✅ Resolved | Single source of truth |
| AP-012: Missing Validation | ✅ Resolved | Uses Pydantic models |
| AP-013: Subprocess Errors | ✅ Resolved | Proper error handling |
| AP-014: File Encoding | ✅ Resolved | All files specify UTF-8 |
| AP-015: Undeclared Dependencies | ✅ Resolved | Dependencies declared |

---

## Archive

This document is now complete. All identified anti-patterns have been addressed through:

1. **Architecture consolidation** - Removal of legacy `pipeline/` directory
2. **Code improvements** - Proper error handling, type hints, encoding
3. **Pattern standardization** - Consistent use of settings, logging, HTTP clients
4. **Documentation** - Clarification of acceptable patterns vs anti-patterns

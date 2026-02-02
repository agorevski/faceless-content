# GitHub Copilot Instructions - Faceless Content

## Repository Context

This is the `faceless-content` repository - an AI-powered video production pipeline for creating faceless YouTube/TikTok content. The pipeline uses Azure OpenAI for image generation, script enhancement, and text-to-speech.

## Pull Request Guidelines

### PR Title Format
- `feat: Add new feature description`
- `fix: Fix bug description`
- `refactor: Refactor description`
- `docs: Documentation update`
- `test: Add/update tests`

### PR Checklist
- [ ] Tests pass (`pytest`)
- [ ] Linting passes (`ruff check src/ tests/`)
- [ ] Type checking passes (`mypy src/`)
- [ ] Coverage maintained at 70%+
- [ ] Documentation updated if needed

## Issue Guidelines

### Bug Reports Should Include
- Python version
- OS information
- Steps to reproduce
- Expected vs actual behavior
- Relevant error messages/logs

### Feature Requests Should Include
- Use case description
- Proposed solution
- Alternatives considered

## Code Review Focus Areas

When reviewing PRs, pay attention to:

1. **Type Safety** - All functions must have type hints
2. **Error Handling** - Use custom exceptions from `core/exceptions.py`
3. **Logging** - Use structlog with context, not print statements
4. **Tests** - New code needs tests, existing tests shouldn't break
5. **Security** - No hardcoded secrets, use `SecretStr` for sensitive config

## Branch Strategy

- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - New features
- `fix/*` - Bug fixes
- `refactor/*` - Code improvements

## CI/CD

GitHub Actions runs on every PR:
1. Type check (mypy)
2. Tests (pytest) on Python 3.11 & 3.12
3. Security scan (bandit)
4. Build package
5. Coverage check (70% minimum)

## Labels

| Label | Description |
|-------|-------------|
| `bug` | Something isn't working |
| `enhancement` | New feature or request |
| `documentation` | Documentation improvements |
| `good first issue` | Good for newcomers |
| `help wanted` | Extra attention needed |
| `niche:*` | Related to specific content niche |
| `service:*` | Related to specific service (image, tts, video) |

## Related Documentation

- [Architecture](documentation/ARCHITECTURE.md)
- [Setup Guide](documentation/SETUP_GUIDE.md)
- [Future Improvements](documentation/FUTURE_IMPROVEMENTS.md)

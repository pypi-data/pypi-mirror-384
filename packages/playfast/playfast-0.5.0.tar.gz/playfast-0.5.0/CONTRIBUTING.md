# Contributing to Playfast

Thank you for your interest in contributing to Playfast! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Guidelines](#testing-guidelines)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Community](#community)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone. Be kind, professional, and constructive in all interactions.

## Getting Started

### Prerequisites

- Python 3.11+ (Python 3.14 with free-threading recommended)
- Rust 1.70+
- UV (package manager)
- Git

### Development Setup

1. **Fork and clone the repository:**

```bash
git clone https://github.com/yourusername/playfast.git
cd playfast
```

2. **Set up Python environment:**

```bash
# Use Python 3.14 with free-threading for optimal performance
uv python pin 3.14t

# Install dependencies
uv sync --all-extras
```

3. **Build Rust extension:**

```bash
# Development build (faster compilation)
uv run maturin develop

# Release build (optimized, for benchmarking)
uv run maturin develop --release
```

4. **Verify installation:**

```bash
# Run tests
uv run pytest

# Run type checking
uv run mypy python/

# Run linting
uv run ruff check python/
```

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue using the bug report template. Include:

- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, Rust version)
- Error messages and stack traces

### Suggesting Features

Feature requests are welcome! Please create an issue using the feature request template and include:

- Clear description of the feature
- Use case and benefits
- Possible implementation approach
- Any alternatives considered

### Code Contributions

1. **Find or create an issue** describing what you want to work on

1. **Comment on the issue** to let others know you're working on it

1. **Create a feature branch** from `main`:

   ```bash
   git checkout -b feature/your-feature-name
   ```

1. **Make your changes** following our code style guidelines

1. **Add tests** for new functionality

1. **Update documentation** if needed

1. **Submit a pull request**

## Code Style Guidelines

### Python

- **Formatter**: Use Ruff for formatting

  ```bash
  uv run ruff format python/
  ```

- **Linter**: Ensure no Ruff errors

  ```bash
  uv run ruff check python/
  ```

- **Type Hints**: Required for all public APIs

  ```bash
  uv run mypy python/
  ```

- **Docstrings**: Use Google style

  ```python
  def get_app(app_id: str, lang: str = "en") -> AppInfoModel:
      """Get application information from Google Play Store.

      Args:
          app_id: The package name of the app (e.g., 'com.spotify.music')
          lang: Language code (default: 'en')

      Returns:
          AppInfoModel containing app details

      Raises:
          AppNotFoundError: If the app doesn't exist
          ParseError: If parsing fails
      """
  ```

- **Naming Conventions**:

  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
  - Private members: `_leading_underscore`

### Rust

- **Formatter**: Use `cargo fmt`

  ```bash
  cargo fmt
  ```

- **Linter**: Ensure no Clippy warnings

  ```bash
  cargo clippy -- -D warnings
  ```

- **Documentation**: Add doc comments for public APIs

  ```rust
  /// Parses an app page HTML and extracts app information.
  ///
  /// # Arguments
  ///
  /// * `html` - The HTML content of the app page
  /// * `app_id` - The package name of the app
  ///
  /// # Returns
  ///
  /// Returns `AppInfo` struct containing parsed data
  ///
  /// # Errors
  ///
  /// Returns `ParseError` if HTML structure is unexpected
  pub fn parse_app_page(html: &str, app_id: &str) -> Result<AppInfo, ParseError> {
      // Implementation
  }
  ```

- **Error Handling**: Use `Result` types, avoid panics in library code

- **Performance**: Use `clippy::perf` lints, benchmark critical paths

## Testing Guidelines

### Python Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_client.py

# Run with coverage
uv run pytest --cov=playfast --cov-report=html

# Run only fast tests (skip slow integration tests)
uv run pytest -m "not slow"

# Run tests in parallel
uv run pytest -n auto
```

### Rust Tests

```bash
# Run unit tests
cargo test

# Run specific test
cargo test test_parser

# Run with output
cargo test -- --nocapture
```

### Test Requirements

- **Unit tests** for all new functions
- **Integration tests** for public APIs
- **Edge cases** and error conditions
- **Performance tests** for critical paths (if applicable)
- Maintain or improve code coverage

### Test Structure

```python
# tests/test_client.py
import pytest
from playfast import AsyncClient


class TestAsyncClient:
    @pytest.mark.asyncio
    async def test_get_app_success(self):
        """Test successful app retrieval."""
        async with AsyncClient() as client:
            app = await client.get_app("com.spotify.music")
            assert app.title
            assert app.score >= 0

    @pytest.mark.asyncio
    async def test_get_app_not_found(self):
        """Test handling of non-existent app."""
        async with AsyncClient() as client:
            with pytest.raises(AppNotFoundError):
                await client.get_app("invalid.app.id")
```

## Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `ci`: CI/CD changes

### Examples

```
feat(client): add multi-country parallel scraping

Implement parallel fetching of app information across multiple countries
using asyncio.gather for concurrent requests.

Closes #42
```

```
fix(parser): handle missing developer info gracefully

Some apps don't have developer information in the HTML.
Added fallback logic to prevent ParseError.

Fixes #38
```

```
perf(rust): optimize HTML parsing with SIMD

Use SIMD operations for faster string processing in parser.
Benchmark shows 2x improvement for large HTML documents.
```

### Commit Guidelines

- Use present tense ("add feature" not "added feature")
- Use imperative mood ("move cursor" not "moves cursor")
- Keep subject line under 72 characters
- Reference issues and PRs in the footer
- Include "BREAKING CHANGE:" in footer for breaking changes

## Pull Request Process

### Before Submitting

1. **Update your branch** with latest `main`:

   ```bash
   git fetch origin
   git rebase origin/main
   ```

1. **Run all checks**:

   ```bash
   # Python checks
   uv run ruff check python/
   uv run mypy python/
   uv run pytest

   # Rust checks
   cargo fmt --check
   cargo clippy -- -D warnings
   cargo test
   ```

1. **Update documentation** if needed:

   - Update [README.md](README.md) for user-facing changes
   - Update [CLAUDE.md](CLAUDE.md) for development changes
   - Add docstrings for new public APIs

1. **Add changelog entry** (if applicable):

   - Add entry to `CHANGELOG.md` under "Unreleased" section

### Submitting PR

1. **Push your branch**:

   ```bash
   git push origin feature/your-feature-name
   ```

1. **Create pull request** on GitHub using the PR template

1. **Fill out the PR template** completely:

   - Clear description of changes
   - Motivation and context
   - Type of change (bug fix, feature, etc.)
   - Testing done
   - Checklist completion

1. **Request review** from maintainers

### PR Review Process

- Maintainers will review your PR within a few days
- Address review comments by pushing new commits
- Once approved, a maintainer will merge your PR
- Your contribution will be included in the next release

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] No new warnings
- [ ] Dependent changes merged

## Development Tips

### Quick Development Cycle

```bash
# Fast rebuild after Rust changes (debug mode)
uv run maturin develop

# Run specific test quickly
uv run pytest tests/test_client.py::TestAsyncClient::test_get_app -v

# Auto-format on save (VS Code)
# Add to .vscode/settings.json:
{
    "editor.formatOnSave": true,
    "python.formatting.provider": "none",
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff"
    }
}
```

### Debugging

**Python:**

```python
import logging

logging.basicConfig(level=logging.DEBUG)


# Use breakpoint()
async def debug_example():
    app = await client.get_app("com.spotify.music")
    breakpoint()  # Debugger will stop here
    print(app)
```

**Rust:**

```bash
# Build with debug symbols
uv run maturin develop --debug

# Set backtrace
RUST_BACKTRACE=1 python your_script.py
```

### Profiling

**Python:**

```bash
uv run python -m cProfile -o profile.stats examples/basic.py
uv run python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"
```

**Rust:**

```bash
cargo build --release
perf record -g ./target/release/playfast
perf report
```

## Community

### Getting Help

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check [README.md](README.md) and [CLAUDE.md](CLAUDE.md)

### Recognition

Contributors will be recognized in:

- `CONTRIBUTORS.md` file
- Release notes
- Project README

Thank you for contributing to Playfast!

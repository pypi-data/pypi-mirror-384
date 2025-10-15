# Contributing Guide

We welcome contributions to Playfast! This guide will help you get started.

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/playfast.git
cd playfast
```

### 2. Set Up Development Environment

```bash
# Set Python version (3.14t recommended for free-threading)
uv python pin 3.14t

# Install dependencies
uv sync

# Build Rust extension
uv run maturin develop --release

# Verify installation
uv run pytest
```

## Development Workflow

### Making Changes

1. **Create a feature branch**:

```bash
git checkout -b feature/amazing-feature
```

2. **Make your changes** in either:

   - `python/playfast/` - Python code
   - `src/` - Rust code
   - `docs/` - Documentation
   - `tests/` - Tests

1. **Rebuild after Rust changes**:

```bash
uv run maturin develop
```

4. **Run tests**:

```bash
uv run pytest
```

5. **Format and lint**:

```bash
# Python
uv run ruff format
uv run ruff check python/

# Rust
cargo fmt
cargo clippy
```

### Code Quality Standards

#### Python Code

- **Formatting**: Use Ruff (replaces Black)

```bash
uv run ruff format
```

- **Linting**: Pass all Ruff checks

```bash
uv run ruff check python/
uv run ruff check --fix python/  # Auto-fix
```

- **Type Checking**: Pass Mypy and Pyright

```bash
uv run mypy python/
uv run pyright
```

- **Style**:
  - Line length: 88 characters
  - Use type hints everywhere
  - Write docstrings (Google style)
  - Follow PEP 8

#### Rust Code

- **Formatting**: Use rustfmt

```bash
cargo fmt
```

- **Linting**: Pass Clippy with no warnings

```bash
cargo clippy
cargo clippy -- -D warnings  # Treat warnings as errors
```

- **Style**:
  - Follow Rust naming conventions
  - Write documentation comments (`///`)
  - Use `Result<T, E>` for error handling
  - Avoid `.unwrap()` in library code

### Testing

#### Python Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/python/test_client.py -v

# Run with coverage
uv run pytest --cov=playfast --cov-report=html

# Skip slow tests
uv run pytest -m "not slow"

# Run tests in parallel
uv run pytest -n auto
```

#### Rust Tests

```bash
# Run all Rust tests
cargo test

# Run specific test
cargo test test_parser

# Run with output
cargo test -- --nocapture
```

#### Writing Tests

- Add tests for all new features
- Maintain >85% code coverage
- Use pytest fixtures from `conftest.py`
- Mock network calls in unit tests
- Add integration tests for end-to-end flows

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `build`: Build system changes
- `ci`: CI/CD changes
- `chore`: Other changes

**Examples:**

```
feat(client): add multi-country parallel fetching

Add get_apps_parallel method that fetches app data from multiple
countries concurrently using aiohttp.

Closes #123
```

```
fix(parser): handle missing app descriptions

Some apps don't have descriptions in their HTML. Return empty string
instead of raising ParseError.

Fixes #456
```

```
perf(rust): optimize HTML parsing with SIMD

Use scraper's SIMD features to speed up HTML parsing by 2x.

Benchmark results:
- Before: 4.8s for 1000 pages
- After: 2.3s for 1000 pages
```

### Pull Request Process

1. **Update documentation** if adding features
1. **Add tests** for new functionality
1. **Run all checks**:

```bash
# Python
uv run ruff check python/
uv run mypy python/
uv run pyright
uv run pytest

# Rust
cargo fmt --check
cargo clippy
cargo test

# Documentation
uv run mkdocs build
```

4. **Push to your fork**:

```bash
git push origin feature/amazing-feature
```

5. **Create Pull Request** on GitHub with:

   - Clear title and description
   - Reference related issues
   - List of changes
   - Testing performed
   - Screenshots (if UI changes)

1. **Respond to review feedback**

1. **Squash commits** if requested

1. **Wait for approval** and merge

## Code Style Guidelines

### Python

**Good:**

```python
async def get_app(
    self,
    app_id: str,
    lang: str = "en",
    country: str = "us",
) -> AppInfo:
    """Get app information from Google Play Store.

    Args:
        app_id: Package ID (e.g., "com.spotify.music")
        lang: Language code (default: "en")
        country: Country code (default: "us")

    Returns:
        AppInfo object with app metadata

    Raises:
        AppNotFoundError: If app doesn't exist
        NetworkError: If request fails
    """
    html = await self._fetch_html(app_id, lang, country)
    return parse_app_page(html, app_id)
```

**Bad:**

```python
# No type hints, no docstring, inconsistent formatting
async def get_app(self, app_id, lang="en", country="us"):
    html = await self._fetch_html(app_id, lang, country)
    return parse_app_page(html, app_id)
```

### Rust

**Good:**

```rust
/// Parse app information from HTML page.
///
/// # Arguments
///
/// * `html` - HTML content from Play Store
/// * `app_id` - Package ID
///
/// # Returns
///
/// Parsed `RustAppInfo` object
///
/// # Errors
///
/// Returns `PlayfastError::ParseError` if HTML is invalid
pub fn parse_app_page(html: &str, app_id: &str) -> Result<RustAppInfo, PlayfastError> {
    let document = Html::parse_document(html);
    // ...
}
```

**Bad:**

```rust
// No docs, uses unwrap
pub fn parse_app_page(html: &str, app_id: &str) -> RustAppInfo {
    let document = Html::parse_document(html);
    document.select(&selector).next().unwrap()
}
```

## Project Structure

Understanding the codebase:

```
playfast/
├── python/playfast/       # Python layer (high-level API)
│   ├── client.py         # AsyncClient (aiohttp-based)
│   ├── rust_client.py    # RustClient (wrapper)
│   ├── models.py         # Pydantic models
│   ├── constants.py      # Enums (Category, Collection, etc.)
│   └── exceptions.py     # Custom exceptions
│
├── src/                  # Rust core (low-level)
│   ├── lib.rs           # PyO3 bindings (Python interface)
│   ├── http.rs          # HTTP client (reqwest)
│   ├── parser.rs        # HTML/JSON parsing
│   ├── models.rs        # Rust data structures
│   └── error.rs         # Error types
│
├── tests/
│   ├── python/          # Python tests
│   │   ├── conftest.py  # Pytest fixtures
│   │   ├── test_async_client.py
│   │   ├── test_rust_client.py
│   │   └── test_models.py
│   └── rust/            # Rust tests (in src/*.rs)
│
├── benchmarks/          # Performance benchmarks
│   ├── compare_clients.py
│   └── memory_profiling.py
│
├── examples/            # Usage examples
│   ├── basic.py
│   ├── parallel.py
│   └── reviews.py
│
└── docs/               # MkDocs documentation
    ├── index.md
    ├── api/
    ├── guides/
    └── examples/
```

## Areas to Contribute

### Easy Issues (Good First Issues)

- Documentation improvements
- Add more examples
- Fix typos
- Add tests
- Improve error messages

### Medium Issues

- Add new features (e.g., developer page scraping)
- Optimize existing code
- Improve error handling
- Add caching layer

### Advanced Issues

- Rust performance optimizations
- Python 3.14t free-threading support
- Distributed crawling
- Real-time monitoring

## Getting Help

- **GitHub Issues**: Report bugs or request features
- **GitHub Discussions**: Ask questions
- **Code Review**: Request reviews on your PRs

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Help newcomers
- Focus on the code, not the person

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

______________________________________________________________________

Thank you for contributing to Playfast! 🚀

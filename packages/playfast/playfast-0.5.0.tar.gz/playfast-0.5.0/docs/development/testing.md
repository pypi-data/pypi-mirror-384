# Testing

Guide to testing in Playfast.

## Running Tests

### All Tests

```bash
# Run all tests
uv run pytest

# With coverage
uv run pytest --cov=playfast --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```

### Specific Tests

```bash
# Single file
uv run pytest tests/python/test_client.py

# Single test
uv run pytest tests/python/test_client.py::test_get_app

# Pattern matching
uv run pytest -k "test_app"

# Verbose output
uv run pytest -v
```

### Test Markers

```bash
# Skip slow/integration tests (default)
uv run pytest -m "not slow and not integration"

# Run only integration tests
uv run pytest -m integration

# Run only async tests
uv run pytest -m asyncio
```

## Test Structure

### Python Tests (`tests/python/`)

**`conftest.py`** - Pytest fixtures

```python
@pytest.fixture
def mock_app_info() -> AppInfo:
    """Mock AppInfo for testing."""
    return AppInfo(
        app_id="com.test.app",
        title="Test App",
        # ...
    )
```

**`test_async_client.py`** - AsyncClient tests

- Context manager tests
- get_app() tests
- get_apps_parallel() tests
- stream_reviews() tests
- Error handling tests

**`test_rust_client.py`** - RustClient tests

- Similar to AsyncClient tests
- Synchronous versions

**`test_models.py`** - Pydantic model tests

- Validation tests
- from_rust() conversion tests
- Helper method tests

### Rust Tests (`src/*.rs`)

Embedded in source files:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_app_page() {
        let html = r#"<html>...</html>"#;
        let result = parse_app_page(html, "com.test.app");
        assert!(result.is_ok());
    }
}
```

## Writing Tests

### Python Tests

**Good test structure:**

```python
def test_get_app_success(mock_response):
    """Test successful app fetch."""
    # Arrange
    client = AsyncClient()
    app_id = "com.spotify.music"

    # Act
    app = await client.get_app(app_id)

    # Assert
    assert app.app_id == app_id
    assert app.title is not None
    assert app.score >= 0
```

**Use fixtures:**

```python
def test_app_is_free(mock_app_info):
    """Test is_free property."""
    assert mock_app_info.is_free is True
```

**Test errors:**

```python
def test_app_not_found():
    """Test AppNotFoundError is raised."""
    with pytest.raises(AppNotFoundError):
        await client.get_app("invalid.app.id")
```

### Rust Tests

```rust
#[test]
fn test_parser_valid_html() {
    let html = include_str!("../tests/fixtures/app_page.html");
    let result = parse_app_page(html, "com.spotify.music");
    assert!(result.is_ok());

    let app = result.unwrap();
    assert_eq!(app.app_id, "com.spotify.music");
}

#[test]
fn test_parser_invalid_html() {
    let html = "<html></html>";
    let result = parse_app_page(html, "com.test");
    assert!(result.is_err());
}
```

## Mocking

### Mock Network Calls

```python
from unittest.mock import AsyncMock, patch


async def test_get_app_mocked():
    with patch.object(AsyncClient, "_fetch_html") as mock_fetch:
        mock_fetch.return_value = "<html>...</html>"

        client = AsyncClient()
        app = await client.get_app("com.test")

        mock_fetch.assert_called_once()
```

### Use Fixtures

```python
@pytest.fixture
def mock_html():
    """Mock HTML response."""
    return """
    <html>
        <div class="app-title">Test App</div>
        <div class="rating">4.5</div>
    </html>
    """


def test_with_fixture(mock_html):
    app = parse_app_page(mock_html, "com.test")
    assert app.title == "Test App"
```

## Coverage

### Check Coverage

```bash
# Run with coverage
uv run pytest --cov=playfast

# Generate HTML report
uv run pytest --cov=playfast --cov-report=html

# Check minimum coverage (85%)
uv run pytest --cov=playfast --cov-fail-under=85
```

### Coverage Configuration

In `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["python/playfast"]
omit = []

[tool.coverage.report]
fail_under = 85
skip_covered = true
show_missing = true
exclude_lines = [
  "pragma: no cover",
  "@overload",
  "if TYPE_CHECKING:",
]
```

## Continuous Integration

Tests run automatically on:

- Every push
- Every pull request
- Before merge

Required checks:

- ✅ All tests pass
- ✅ Coverage >= 85%
- ✅ Linting passes (ruff, clippy)
- ✅ Type checking passes (mypy, pyright)

## Best Practices

1. **Test one thing per test**
1. **Use descriptive test names**
1. **Follow Arrange-Act-Assert pattern**
1. **Mock external dependencies**
1. **Test both success and error cases**
1. **Keep tests fast** (mock network calls)
1. **Maintain high coverage** (>85%)
1. **Write tests before fixing bugs** (TDD)

## Debugging Tests

```bash
# Print output
uv run pytest -s

# Enter debugger on failure
uv run pytest --pdb

# Stop at first failure
uv run pytest -x

# Show local variables on failure
uv run pytest -l
```

## Performance Testing

See [Benchmarking](benchmarking.md) for performance tests.

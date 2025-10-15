# Tests

This directory contains tests for both Python and Rust components.

## Structure

```
tests/
├── python/              # Python tests (pytest)
│   ├── conftest.py     # pytest fixtures and configuration
│   └── test_*.py       # Python test modules
└── rust/               # Rust tests (cargo test)
    └── integration_tests.rs
```

## Running Tests

### Python Tests

```bash
# Run all Python tests
pytest tests/python/

# Run with coverage
pytest tests/python/ --cov=python/playfast --cov-report=html

# Run specific test file
pytest tests/python/test_async_client.py -v
```

### Rust Tests

```bash
# Run all Rust tests
cargo test

# Run specific integration test
cargo test --test integration_tests

# Run with output
cargo test -- --nocapture
```

### Run All Tests

```bash
# Python + Rust
pytest tests/python/ && cargo test
```

## Test Types

### Python Tests (`tests/python/`)

- **Unit tests**: Test individual Python modules
- **Integration tests**: Test Python-Rust interaction
- **Coverage target**: 85%+

### Rust Tests (`tests/rust/`)

- **Integration tests**: Test Rust core functionality
- **Pattern validation**: Test parsing logic
- **Data structure tests**: Test JSON/HTML parsing

## CI/CD

Both test suites are run in CI:

```yaml
- name: Test Python
  run: pytest tests/python/ --cov=python/playfast

- name: Test Rust
  run: cargo test
```

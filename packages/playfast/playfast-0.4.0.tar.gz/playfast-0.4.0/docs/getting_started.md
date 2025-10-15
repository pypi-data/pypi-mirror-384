# Getting Started

This guide will help you get started with Playfast.

## Prerequisites

- Python 3.11+ (Python 3.14 free-threading recommended)
- Basic understanding of async/await in Python
- (Optional) Rust 1.70+ for building from source

## Installation

### Using UV (Recommended)

UV is the modern Python package manager with superior performance:

```bash
uv pip install playfast
```

### Using pip

```bash
pip install playfast
```

### From Source

If you want to build from source or contribute to development:

```bash
# Clone the repository
git clone https://github.com/mixL1nk/playfast.git
cd playfast

# Set Python version
uv python pin 3.14t  # free-threading build

# Install dependencies
uv sync --all-extras

# Build Rust extension
uv run maturin develop --release

# Run tests
uv run pytest
```

## Verify Installation

```python
import playfast

print(playfast.__version__)
```

## Your First Script

Create a file named `first_playfast.py`:

```python
import asyncio
from playfast import AsyncClient


async def main():
    """Fetch information about Spotify app."""
    async with AsyncClient() as client:
        app = await client.get_app("com.spotify.music")

        print(f"App: {app.title}")
        print(f"Developer: {app.developer}")
        print(f"Score: {app.score}⭐")
        print(f"Ratings: {app.ratings:,}")
        print(f"Price: ${app.price}")
        print(f"Free: {app.is_free}")


if __name__ == "__main__":
    asyncio.run(main())
```

Run it:

```bash
python first_playfast.py
```

Expected output:

```
App: Spotify: Music and Podcasts
Developer: Spotify AB
Score: 4.4⭐
Ratings: 15,234,567
Price: $0.0
Free: True
```

## Core Concepts

### AsyncClient

The main entry point for all operations. Always use it as an async context manager:

```python
async with AsyncClient() as client:
    # Your code here
    pass
```

### Models

All data is returned as Pydantic models with full type safety:

- `AppInfo`: Complete app information
- `Review`: User reviews
- `SearchResult`: Search results

### Async Operations

All methods are async and should be awaited:

```python
# Single app
app = await client.get_app("com.example.app")

# Multiple apps in parallel
apps = await client.get_apps_parallel(["app1", "app2", "app3"])

# Stream reviews
async for review in client.stream_reviews("com.example.app"):
    print(review.content)
```

## Next Steps

- [Quick Start](quick_start.md) - More examples
- [Basic Usage](guides/basic_usage.md) - Learn common patterns
- [API Reference](api/client.md) - Full API documentation
- [Examples](examples/basic.md) - Real-world examples

## Troubleshooting

### Import Error

If you get `ModuleNotFoundError: No module named 'playfast'`:

```bash
# Make sure you're in the correct environment
which python
python -m pip list | grep playfast
```

### Async Context Manager Error

If you get `RuntimeError: Event loop is closed`:

```python
# Make sure you're using asyncio.run()
asyncio.run(main())

# NOT this:
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
```

### Performance Issues

If scraping is slow:

1. Increase `max_concurrent` parameter:

```python
async with AsyncClient(max_concurrent=50) as client:
    ...
```

2. Use parallel methods:

```python
# Good: parallel
apps = await client.get_apps_parallel(["app1", "app2"])

# Bad: sequential
app1 = await client.get_app("app1")
app2 = await client.get_app("app2")
```

## Getting Help

- [FAQ](faq.md) - Frequently asked questions
- [GitHub Issues](https://github.com/mixL1nk/playfast/issues) - Report bugs
- [API Reference](api/client.md) - Detailed documentation

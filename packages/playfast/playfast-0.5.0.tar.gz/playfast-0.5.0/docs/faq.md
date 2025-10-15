# Frequently Asked Questions

## General

### What is Playfast?

Playfast is a high-performance Google Play Store scraper built with Rust and Python, designed to be 3-10x faster than existing solutions by leveraging Python 3.14's free-threading and Rust's performance.

### Is Playfast free?

Yes, Playfast is open source and released under the MIT License. You can use it freely for personal and commercial projects.

### What makes Playfast faster than other scrapers?

Playfast uses a hybrid architecture:

1. **Rust Core**: CPU-intensive HTML parsing is done in Rust without the GIL
1. **Async I/O**: Network requests use Python's asyncio for concurrency
1. **Free-Threading**: Python 3.14's PEP 703 allows true parallel execution
1. **Zero-Copy**: Data passes between Rust and Python without copying

## Installation & Setup

### What Python version do I need?

- **Minimum**: Python 3.11
- **Recommended**: Python 3.14 with free-threading enabled

### How do I enable free-threading?

```bash
# Install Python 3.14t (free-threading build)
uv python install 3.14t

# Use it in your project
uv python pin 3.14t
```

### Do I need to install Rust?

No, pre-built wheels are available for:

- Linux (x86_64, aarch64)
- macOS (Intel, Apple Silicon)
- Windows (x86_64)

You only need Rust if building from source.

### Why am I getting build errors?

Common causes:

1. **Missing C compiler**: Install build tools for your platform
1. **Outdated Rust**: Run `rustup update`
1. **Network issues**: Check your internet connection

See [Installation Troubleshooting](installation.md#troubleshooting).

## Usage

### Can I use Playfast synchronously?

No, Playfast is async-only. You must use `asyncio`:

```python
import asyncio
from playfast import AsyncClient


async def main():
    async with AsyncClient() as client:
        app = await client.get_app("com.example.app")


asyncio.run(main())
```

### How many concurrent requests can I make?

Default is 10 concurrent requests. You can increase it:

```python
async with AsyncClient(max_concurrent=50) as client:
    # Up to 50 concurrent requests
    pass
```

**Warning**: Too many concurrent requests may trigger rate limiting.

### How do I handle rate limiting?

Use exponential backoff:

```python
from playfast.exceptions import RateLimitError
import asyncio


async def fetch_with_retry(client, app_id, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await client.get_app(app_id)
        except RateLimitError as e:
            if attempt < max_retries - 1:
                wait_time = 2**attempt  # Exponential backoff
                await asyncio.sleep(wait_time)
            else:
                raise
```

### Can I scrape apps from different countries?

Yes, use the `country` parameter:

```python
# Single country
app_us = await client.get_app("com.spotify.music", country="us")

# Multiple countries
results = await client.get_apps_parallel(
    app_ids=["com.spotify.music"], countries=["us", "kr", "jp", "de"]
)
```

### How do I get all reviews for an app?

Use `stream_reviews()`:

```python
reviews = []
async for review in client.stream_reviews("com.spotify.music"):
    reviews.append(review)
    # Process incrementally to avoid memory issues
```

### What's the difference between `get_apps_parallel` and multiple `get_app` calls?

`get_apps_parallel` is much faster:

```python
# ❌ Slow: Sequential
apps = []
for app_id in app_ids:
    app = await client.get_app(app_id)
    apps.append(app)

# ✅ Fast: Parallel
results = await client.get_apps_parallel(app_ids)
```

## Performance

### How fast is Playfast?

Benchmark (100 apps):

- **Playfast**: 3.2 seconds
- **google-play-scraper (async)**: 12.1 seconds
- **google-play-scraper (sync)**: 28.5 seconds

**Result**: 3.8-8.9x faster

### How can I improve performance?

1. **Increase concurrency**:

```python
async with AsyncClient(max_concurrent=50) as client:
    ...
```

2. **Use parallel methods**:

```python
# Use get_apps_parallel, not multiple get_app calls
```

3. **Enable free-threading**:

```bash
uv python install 3.14t
```

4. **Batch processing**:

```python
# Process in batches instead of all at once
for batch in chunks(app_ids, 100):
    await client.get_apps_parallel(batch)
```

### How much memory does Playfast use?

Memory usage is minimal due to:

- Streaming approach for reviews
- Efficient Rust data structures
- No unnecessary data copying

For 1000 apps: ~50-100 MB peak memory usage.

### Can I profile Playfast's performance?

Yes:

```python
import cProfile

cProfile.run("asyncio.run(main())")
```

Or use `py-spy`:

```bash
py-spy record -o profile.svg -- python your_script.py
```

## Errors & Troubleshooting

### What does "App not found" mean?

The app ID doesn't exist on the Play Store or was removed. Verify the app ID at:
`https://play.google.com/store/apps/details?id=YOUR_APP_ID`

### Why do I get "Parse error"?

Possible causes:

1. **Google changed HTML structure**: Please report an issue
1. **Network error**: Check your connection
1. **Rate limiting**: Wait and retry

### How do I debug issues?

Enable logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)

from playfast import AsyncClient
```

### My script hangs indefinitely

Common causes:

1. **Missing `await`**: Ensure all async calls use `await`
1. **Event loop closed**: Use `asyncio.run(main())`
1. **Network timeout**: Increase timeout:

```python
async with AsyncClient(timeout=60) as client:
    ...
```

## Data & Privacy

### Is web scraping legal?

Web scraping public data is generally legal, but:

1. Follow Google's Terms of Service
1. Respect robots.txt
1. Don't overload servers (rate limiting)
1. Check local laws

**Disclaimer**: Playfast is provided as-is. Users are responsible for compliance with applicable laws.

### Does Playfast store scraped data?

No, Playfast only returns data to your application. You control what to do with it.

### How do I anonymize my requests?

Use a proxy:

```python
async with AsyncClient(proxy="http://proxy.example.com:8080") as client:
    ...
```

Or rotate user agents:

```python
import random

user_agents = [
    "Mozilla/5.0 ...",
    "Mozilla/5.0 ...",
]

async with AsyncClient(headers={"User-Agent": random.choice(user_agents)}) as client:
    ...
```

## Development

### How do I contribute?

See [Contributing Guide](development/contributing.md).

### How do I report bugs?

[Open an issue on GitHub](https://github.com/mixL1nk/playfast/issues) with:

1. Python version
1. Playfast version
1. Minimal reproduction code
1. Error message/traceback

### Can I add new features?

Yes! We welcome:

- New scraping endpoints
- Performance improvements
- Bug fixes
- Documentation improvements

See [Contributing Guide](development/contributing.md).

### How do I run tests?

```bash
# All tests
uv run pytest

# Specific test
uv run pytest tests/test_client.py

# With coverage
uv run pytest --cov=playfast
```

## Still Have Questions?

- [GitHub Discussions](https://github.com/mixL1nk/playfast/discussions)
- [GitHub Issues](https://github.com/mixL1nk/playfast/issues)
- [API Reference](api/client.md)

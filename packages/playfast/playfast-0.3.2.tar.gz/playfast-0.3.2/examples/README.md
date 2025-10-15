# Playfast Examples

This directory contains practical examples demonstrating Playfast's features.

## Examples Overview

### 1. `01_async_client.py` - AsyncClient Basics

Learn how to use AsyncClient for async/await operations:

- Single app fetching
- Multiple apps (concurrent)
- Multi-country data collection
- Reviews and search

**When to use:**

- Easy async/await syntax needed
- I/O-bound workloads
- Integration with existing async code

```bash
uv run python examples/01_async_client.py
```

### 2. `02_rust_client.py` - RustClient for Maximum Performance

Learn how to use RustClient for high-performance scenarios:

- Single app fetching
- Parallel batch processing (ThreadPoolExecutor)
- Multi-country parallel execution
- Reviews and search

**When to use:**

- Batch processing (1000s of apps)
- High-throughput scenarios
- Maximum performance needed (30-40% faster)

```bash
uv run python examples/02_rust_client.py
```

### 3. `03_batch_api.py` - High-Level Batch API

Learn how to use high-level batch functions:

- `fetch_apps()` - Multiple apps across countries
- `fetch_category_lists()` - Top apps by category
- `search_apps()` - Search queries
- `fetch_reviews()` - Reviews for multiple apps
- `fetch_multi_country_apps()` - Same app, multiple countries

**When to use:**

- Simplest API for multiple items
- 5-10x faster than sequential
- Automatic parallelization

```bash
uv run python examples/03_batch_api.py
```

### 4. `04_countries_and_categories.py` - Countries and Categories

Learn about country/region optimization:

- All available countries (162)
- Unique Play Store regions (36)
- Representative countries
- Region mapping
- Categories and collections

**When to use:**

- Global data collection
- Region optimization
- Understanding Play Store structure

```bash
uv run python examples/04_countries_and_categories.py
```

### 5. `basic.py` - Quickstart

Minimal example for getting started:

- Fetch single app
- Display basic information

```bash
uv run python examples/basic.py
```

### 6. `rust_client_example.py` - Advanced RustClient

Comprehensive RustClient examples:

- All features in detail
- Massive batch processing (100+ apps)
- Performance tips

```bash
uv run python examples/rust_client_example.py
```

## Running Examples

### Run all examples

```bash
uv run python examples/01_async_client.py
uv run python examples/02_rust_client.py
uv run python examples/03_batch_api.py
uv run python examples/04_countries_and_categories.py
```

### Quick start

```bash
uv run python examples/basic.py
```

## Performance Comparison

| Method          | Use Case              | Speed            | Complexity |
| --------------- | --------------------- | ---------------- | ---------- |
| **AsyncClient** | I/O-bound, async code | Fast             | Easy       |
| **RustClient**  | CPU-bound, batch      | Fastest (30-40%) | Easy       |
| **Batch API**   | Multiple items        | 5-10x sequential | Easiest    |

## Common Patterns

### Pattern 1: Single App (AsyncClient)

```python
import asyncio
from playfast import AsyncClient


async def main():
    async with AsyncClient() as client:
        app = await client.get_app("com.spotify.music")
        print(f"{app.title}: {app.score}⭐")


asyncio.run(main())
```

### Pattern 2: Batch Processing (RustClient)

```python
from concurrent.futures import ThreadPoolExecutor
from playfast import RustClient

client = RustClient()
app_ids = ["com.spotify.music", "com.netflix.mediaclient"]

with ThreadPoolExecutor(max_workers=10) as executor:
    apps = list(executor.map(client.get_app, app_ids))
```

### Pattern 3: High-Level Batch (Batch API)

```python
from playfast import fetch_apps

apps = fetch_apps(
    app_ids=["com.spotify.music", "com.netflix.mediaclient"],
    countries=["us", "kr", "jp"],
    lang="en",
)
```

## Tips

1. **Use batch APIs for multiple requests**: They're optimized for parallel execution
1. **RustClient for CPU-bound**: True parallel execution with GIL release
1. **AsyncClient for I/O-bound**: Natural async/await syntax
1. **Adjust concurrency**: Balance between speed and rate limiting
1. **Use unique regions**: 247 countries → 93 unique stores (2.7x faster)

## Need Help?

- Check the [documentation](../docs/index.md)
- See [API reference](../docs/api/)
- Read [Getting Started guide](../docs/getting_started.md)

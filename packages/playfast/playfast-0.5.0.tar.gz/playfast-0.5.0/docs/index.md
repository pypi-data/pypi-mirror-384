# Playfast ⚡

**Lightning-Fast Google Play Store Scraper**

Playfast is a high-performance Google Play Store scraper built with Rust + PyO3, delivering **5-10x faster performance** with true parallel batch processing.

## ✨ Features

- **🚀 Blazingly Fast**: Batch API is 5-10x faster than sequential processing
- **⚡ True Parallel**: Rust core completely releases GIL for real parallelism
- **🦀 Pure Rust Performance**: HTTP + parsing all in Rust
- **🔒 Type Safe**: Full Pydantic validation and type hints
- **💾 Memory Efficient**: Only 1.5 KB per app, linear scaling
- **🌍 Multi-Country**: 247 countries, 93 unique Play Stores
- **📦 Batch API**: High-level functions for easy parallel processing
- **🎯 Python 3.11+**: Full support for modern Python

## 📊 Performance

**Batch Processing** makes bulk operations 5-10x faster through true Rust parallelism!

### Benchmark Results

**Batch Apps (3 apps × 3 countries = 9 requests):**

| Method                   | Time    | Speedup       |
| ------------------------ | ------- | ------------- |
| **Batch API**            | **~3s** | **6-8x** 🚀   |
| RustClient + ThreadPool  | ~3-4s   | 6-7x          |
| AsyncClient (concurrent) | ~3-5s   | 5-7x          |
| Sequential               | ~20-30s | 1x (baseline) |

**Key Findings:**

- ⚡ **Batch API is simplest and fastest**
- 🎯 **5-10x faster than sequential**
- 💡 **True parallel execution** (Rust releases GIL)
- 🔮 **Linear scaling** up to 1000s of requests

## 🚀 Quick Start

### Installation

```bash
# Using uv (recommended)
uv pip install playfast

# Using pip
pip install playfast
```

### Option 1: Batch API (Recommended - Easiest & Fastest)

```python
from playfast import fetch_apps, fetch_category_lists

# Fetch multiple apps across countries (parallel!)
apps = fetch_apps(
    app_ids=["com.spotify.music", "com.netflix.mediaclient"],
    countries=["us", "kr", "jp"],
    lang="en",
)
print(f"Fetched {len(apps)} apps in ~3 seconds!")

# Fetch top apps by category (parallel!)
results = fetch_category_lists(
    countries=["us", "kr"],
    categories=["GAME_ACTION", "SOCIAL"],
    collection="topselling_free",
    num_results=50,
)
print(f"Fetched {sum(len(r) for r in results)} apps!")
```

### Option 2: RustClient (Maximum Performance)

```python
from playfast import RustClient

# Synchronous API - simple and fast
client = RustClient(timeout=30)

# Get app information
app = client.get_app("com.spotify.music")
print(f"{app.title}: {app.score}⭐ ({app.ratings:,} ratings)")

# Get reviews (paginated)
reviews, next_token = client.get_reviews("com.spotify.music")
for review in reviews:
    print(f"{review.user_name}: {review.content[:100]}")

# Search for apps
results = client.search("music streaming", n_hits=10)
for result in results:
    print(f"{result.title} - {result.score}⭐")
```

### Option 3: AsyncClient (Easy Async Interface)

```python
import asyncio
from playfast import AsyncClient


async def main():
    async with AsyncClient() as client:
        # Get app information
        app = await client.get_app("com.spotify.music")
        print(f"{app.title}: {app.score}⭐")

        # Get reviews
        reviews, next_token = await client.get_reviews("com.spotify.music")
        for review in reviews:
            print(f"{review.user_name}: {review.content[:100]}")


asyncio.run(main())
```

## 🏗️ Architecture

Playfast uses **pure Rust** for maximum performance:

```
┌─────────────────────────────────────┐
│   Python Layer (High-Level API)     │
│   - RustClient (wrapper)            │
│   - AsyncClient (async wrapper)     │
│   - Batch API (high-level)          │
│   - Pydantic Models                 │
└──────────────┬──────────────────────┘
               │ PyO3 Bindings
               ▼
┌─────────────────────────────────────┐
│   Rust Core (Maximum Performance)   │
│   - HTTP Client (reqwest)           │
│   - HTML Parser (scraper)           │
│   - Parallel Processing (rayon)     │
│   - Complete GIL Release            │
└─────────────────────────────────────┘
```

### Three Client Options

1. **Batch API** (Easiest & Fastest)

   - High-level functions: `fetch_apps()`, `fetch_category_lists()`, etc.
   - Automatic parallelization
   - Simplest API
   - **Best for:** Multiple items, bulk data collection

1. **RustClient** (Maximum Performance)

   - Rust HTTP + Rust parsing
   - Complete GIL-free execution
   - Synchronous API
   - **Best for:** Single requests, simple scripts, batch with ThreadPoolExecutor

1. **AsyncClient** (Async Interface)

   - Python async HTTP + Rust parsing
   - Natural async/await syntax
   - Easy integration with async code
   - **Best for:** Async codebases, I/O-bound tasks

**Performance Comparison:**

| Method          | Speed          | Ease of Use    | Best For       |
| --------------- | -------------- | -------------- | -------------- |
| **Batch API**   | ⚡⚡⚡ Fastest | ⭐⭐⭐ Easiest | Multiple items |
| **RustClient**  | ⚡⚡⚡ Fastest | ⭐⭐ Easy      | Single items   |
| **AsyncClient** | ⚡⚡ Fast      | ⭐⭐ Easy      | Async code     |

## 📚 Examples

### Batch API - Multi-Country Collection

```python
from playfast import fetch_multi_country_apps

# Fetch Spotify from 8 countries (parallel!)
apps_by_country = fetch_multi_country_apps(
    app_id="com.spotify.music",
    countries=["us", "kr", "jp", "de", "fr", "gb", "br", "in"],
    lang="en",
)

for country, app in apps_by_country.items():
    print(f"{country.upper()}: {app.score}⭐ ({app.ratings:,} ratings)")
```

### RustClient - Parallel Batch Processing

```python
from concurrent.futures import ThreadPoolExecutor
from playfast import RustClient

client = RustClient()

app_ids = [
    "com.spotify.music",
    "com.netflix.mediaclient",
    "com.instagram.android",
]

# True parallel execution (GIL-free!)
with ThreadPoolExecutor(max_workers=10) as executor:
    apps = list(executor.map(client.get_app, app_ids))

for app in apps:
    print(f"{app.title}: {app.score}⭐")
```

### Country Optimization

```python
from playfast import get_unique_countries, get_representative_country

# Instead of 247 countries, use 93 unique stores
unique = get_unique_countries()
print(f"Unique stores: {len(unique)}")  # 93

# Get representative for a region
rep = get_representative_country("fi")  # Finland → Vanuatu store
print(f"Finland uses {rep} store")  # 'vu'
```

## 📖 API Documentation

### Batch API (High-Level)

```python
# Fetch multiple apps
fetch_apps(app_ids: list[str], countries: list[str], lang: str = "en") -> list[AppInfo]

# Fetch category lists
fetch_category_lists(
    countries: list[str],
    categories: list[str],
    collection: str = "topselling_free",
    num_results: int = 100,
) -> list[list[SearchResult]]

# Search apps
search_apps(queries: list[str], countries: list[str], lang: str = "en") -> list[list[SearchResult]]

# Fetch reviews
fetch_reviews(app_ids: list[str], countries: list[str], sort: int = 1) -> list[tuple[list[Review], str | None]]

# Convenience: Multi-country for single app
fetch_multi_country_apps(app_id: str, countries: list[str], lang: str = "en") -> dict[str, AppInfo]
```

### RustClient

```python
class RustClient:
    def __init__(self, timeout: int = 30, lang: str = "en")

    # Core methods (all GIL-free!)
    def get_app(self, app_id: str, country: str = "us") -> AppInfo
    def get_reviews(self, app_id: str, sort: int = 1) -> tuple[list[Review], str | None]
    def get_all_reviews(self, app_id: str, max_pages: int | None = None) -> list[Review]
    def search(self, query: str, country: str = "us", n_hits: int = 30) -> list[SearchResult]

    # Async wrappers
    async def get_app_async(self, app_id: str, country: str = "us") -> AppInfo
    async def get_apps_parallel(self, app_ids: list[str], countries: list[str]) -> dict[str, list[AppInfo]]
```

### AsyncClient

```python
class AsyncClient:
    def __init__(self, max_concurrent: int = 10, timeout: int = 30)

    async def get_app(self, app_id: str, country: str = "us") -> AppInfo
    async def get_reviews(self, app_id: str, sort: int = 1) -> tuple[list[Review], str | None]
    async def search(self, query: str, country: str = "us", n_hits: int = 30) -> list[SearchResult]
```

### Models

- **AppInfo**: Complete app information (title, score, ratings, description, permissions, etc.)
- **Review**: User reviews with scores, content, timestamps
- **SearchResult**: Search/list results with basic app info
- **Permission**: Permission groups and individual permissions

See API Reference for complete documentation.

## 🌍 Countries & Categories

```python
from playfast.constants import Category, Collection, get_countries, get_unique_countries

# All 247 countries
all_countries = get_countries()

# 93 unique Play Store regions (optimized!)
unique_countries = get_unique_countries()

# Categories
Category.GAME_ACTION
Category.SOCIAL
Category.PRODUCTIVITY

# Collections
Collection.TOP_FREE
Collection.TOP_PAID
Collection.TOP_GROSSING
```

## 🔧 Development

### Setup

```bash
# Clone repository
git clone https://github.com/mixL1nk/playfast.git
cd playfast

# Install dependencies
uv sync

# Build Rust extension
uv run maturin develop --release

# Run tests
uv run pytest

# Run examples
uv run python examples/basic.py

# Run benchmarks
uv run python benchmarks/batch_apps_benchmark.py
```

See [Development Setup](development/setup.md) for detailed instructions.

## 📝 License

MIT License - see [License](license.md) for details.

## 🙏 Acknowledgments

- Built with [PyO3](https://github.com/PyO3/pyo3)
- Inspired by [google-play-scraper](https://github.com/facundoolano/google-play-scraper)
- HTTP: [reqwest](https://github.com/seanmonstar/reqwest)
- Parsing: [scraper](https://github.com/causal-agent/scraper)

## ⚠️ Disclaimer

This tool is for educational and research purposes only. Please respect Google Play Store's Terms of Service. Use responsibly with appropriate rate limiting.

## 📚 Next Steps

- [Getting Started](getting_started.md) - Installation and basics
- [Quick Start](quick_start.md) - Practical examples
- [Batch API](BATCH_API.md) - Batch processing guide
- See `examples/` folder for real-world use cases
- See `benchmarks/` folder for performance tests

______________________________________________________________________

**Made with ❤️ using Rust + Python**

# Batch API Reference

## Overview

Playfast provides three levels of batch processing APIs:

1. **High-Level API** (Recommended) - Simple, intuitive functions
1. **Mid-Level API** - Flexible builders for complex scenarios
1. **Low-Level API** - Direct `_core` access for advanced users

______________________________________________________________________

## High-Level API (Recommended)

### `fetch_category_lists()`

Fetch category/collection lists from multiple countries in parallel.

**Signature:**

```python
def fetch_category_lists(
    countries: list[str],
    categories: list[Optional[str]],
    collection: str = "topselling_free",
    lang: str = "en",
    num_results: int = 100,
) -> list[list[SearchResult]]
```

**Example:**

```python
from playfast import fetch_category_lists

results = fetch_category_lists(
    countries=["us", "kr", "jp"], categories=["GAME_ACTION", "SOCIAL"], num_results=50
)

# results[0] = US GAME_ACTION
# results[1] = US SOCIAL
# results[2] = KR GAME_ACTION
# ...
```

______________________________________________________________________

### `fetch_top_apps()`

Fetch top apps organized by country and category (convenience wrapper).

**Signature:**

```python
def fetch_top_apps(
    countries: list[str],
    categories: list[str],
    collection: str = "topselling_free",
    num_results: int = 100,
    lang: str = "en",
) -> dict[str, dict[str, list[SearchResult]]]
```

**Example:**

```python
from playfast import fetch_top_apps

organized = fetch_top_apps(
    countries=["us", "kr"], categories=["GAME_ACTION", "SOCIAL"], num_results=50
)

# Easy access
us_games = organized["us"]["GAME_ACTION"]
kr_social = organized["kr"]["SOCIAL"]

print(f"Top US game: {us_games[0].title}")
```

______________________________________________________________________

### `fetch_apps()`

Fetch multiple apps across multiple countries.

**Signature:**

```python
def fetch_apps(
    app_ids: list[str],
    countries: list[str],
    lang: str = "en",
) -> list[AppInfo]
```

**Example:**

```python
from playfast import fetch_apps

apps = fetch_apps(
    app_ids=["com.spotify.music", "com.netflix.mediaclient"],
    countries=["us", "kr", "jp"],
    lang="en",
)

# Returns 6 AppInfo objects (2 apps × 3 countries)
```

______________________________________________________________________

### `fetch_multi_country_apps()`

Fetch the same app from multiple countries (convenience wrapper).

**Signature:**

```python
def fetch_multi_country_apps(
    app_id: str,
    countries: list[str],
    lang: str = "en",
) -> dict[str, AppInfo]
```

**Example:**

```python
from playfast import fetch_multi_country_apps

apps = fetch_multi_country_apps(
    app_id="com.spotify.music", countries=["us", "kr", "jp", "de"]
)

for country, app in apps.items():
    print(f"{country}: {app.score} stars, {app.ratings:,} ratings")
```

______________________________________________________________________

### `search_apps()`

Perform multiple searches across multiple countries.

**Signature:**

```python
def search_apps(
    queries: list[str],
    countries: list[str],
    lang: str = "en",
) -> list[list[SearchResult]]
```

**Example:**

```python
from playfast import search_apps

results = search_apps(queries=["spotify", "netflix"], countries=["us", "kr"])

# results[0] = US spotify results
# results[1] = US netflix results
# results[2] = KR spotify results
# results[3] = KR netflix results
```

______________________________________________________________________

### `fetch_reviews()`

Fetch reviews for multiple apps across multiple countries.

**Signature:**

```python
def fetch_reviews(
    app_ids: list[str],
    countries: list[str],
    lang: str = "en",
    sort: int = 1,
) -> list[tuple[list[Review], Optional[str]]]
```

**Example:**

```python
from playfast import fetch_reviews

results = fetch_reviews(
    app_ids=["com.spotify.music"],
    countries=["us", "kr"],
    sort=1,  # 1=newest, 2=highest, 3=most helpful
)

for reviews, next_token in results:
    print(f"Got {len(reviews)} reviews")
    if next_token:
        print("More reviews available")
```

______________________________________________________________________

## Mid-Level API

### `BatchFetcher`

Builder pattern for batch operations with shared defaults.

**Signature:**

```python
class BatchFetcher:
    def __init__(
        self,
        lang: str = "en",
        default_num_results: int = 100,
        default_collection: str = "topselling_free",
    )

    def apps(
        self,
        app_ids: list[str],
        countries: list[str],
        lang: Optional[str] = None,
    ) -> list[AppInfo]

    def category_lists(
        self,
        countries: list[str],
        categories: list[Optional[str]],
        collection: Optional[str] = None,
        num_results: Optional[int] = None,
        lang: Optional[str] = None,
    ) -> list[list[SearchResult]]

    def search(
        self,
        queries: list[str],
        countries: list[str],
        lang: Optional[str] = None,
    ) -> list[list[SearchResult]]

    def get_builder_stats(self) -> dict
```

**Example:**

```python
from playfast import BatchFetcher

# Create fetcher with defaults
fetcher = BatchFetcher(
    lang="en", default_num_results=100, default_collection="topselling_free"
)

# Multiple fetches reuse defaults
batch1 = fetcher.category_lists(
    countries=["us", "kr"],
    categories=["GAME_ACTION", "SOCIAL"],
    # Uses: lang="en", num_results=100
)

batch2 = fetcher.category_lists(
    countries=["jp", "de"],
    categories=["PRODUCTIVITY"],
    num_results=50,  # Override default
)

# Check memory stats
stats = fetcher.get_builder_stats()
print(f"Cached strings: {stats['cached_strings']}")
```

______________________________________________________________________

## Low-Level API (Advanced)

### `BatchRequestBuilder`

Manual request building with string interning and memory optimization.

**Signature:**

```python
class BatchRequestBuilder:
    def __init__(
        self,
        collection: str = "topselling_free",
        lang: str = "en",
        num_results: int = 100,
        intern_strings: bool = True,
    )

    def build_list_requests(
        self,
        countries: list[str],
        categories: list[Optional[str]],
        collection: Optional[str] = None,
        lang: Optional[str] = None,
        num: Optional[int] = None,
    ) -> Iterator[tuple[Optional[str], str, str, str, int]]

    def get_memory_stats(self) -> dict
```

**Example:**

```python
from playfast import BatchRequestBuilder
from playfast._core import fetch_and_parse_list_batch

# Build requests
builder = BatchRequestBuilder(
    collection="topselling_free", lang="en", num_results=100, intern_strings=True
)

requests = list(
    builder.build_list_requests(countries=["us", "kr"], categories=["GAME_ACTION"])
)

# Call low-level function
results = fetch_and_parse_list_batch(requests)

# Manual conversion to Pydantic models
from playfast.models import SearchResult

apps = [[SearchResult.from_rust(app) for app in apps] for apps in results]
```

______________________________________________________________________

### Direct `_core` Functions

For maximum control (advanced users only).

**Available Functions:**

```python
from playfast._core import (
    fetch_and_parse_apps_batch,
    fetch_and_parse_list_batch,
    fetch_and_parse_search_batch,
    fetch_and_parse_reviews_batch,
)
```

**Example:**

```python
from playfast._core import fetch_and_parse_list_batch

# Manual request building
requests = [
    ("GAME_ACTION", "topselling_free", "en", "us", 100),
    ("SOCIAL", "topselling_free", "en", "kr", 100),
]

# Returns Rust objects (not Pydantic)
rust_results = fetch_and_parse_list_batch(requests)

# Manual conversion needed
from playfast.models import SearchResult

results = [[SearchResult.from_rust(app) for app in apps] for apps in rust_results]
```

______________________________________________________________________

## Performance Comparison

| Method                   | Time (15 req) | Difficulty | When to Use                           |
| ------------------------ | ------------- | ---------- | ------------------------------------- |
| `fetch_category_lists()` | 0.69s         | Easy       | **Most cases**                        |
| `BatchFetcher`           | 0.69s         | Medium     | Multiple batches with shared settings |
| `BatchRequestBuilder`    | 0.69s         | Hard       | Need memory stats                     |
| Direct `_core`           | 0.69s         | Very Hard  | Maximum control needed                |
| Sequential (loop)        | 5.12s         | Easy       | **Never** (7x slower!)                |

**Recommendation**: Use `fetch_category_lists()` or `fetch_top_apps()` for 95% of use cases!

______________________________________________________________________

## Quick Reference

### Choose Your API Level

```python
# ✅ RECOMMENDED: High-level (easy, intuitive)
from playfast import fetch_category_lists

results = fetch_category_lists(countries, categories, num_results=100)

# 🔧 Advanced: Builder pattern (flexible)
from playfast import BatchFetcher

fetcher = BatchFetcher(lang="en", default_num_results=100)
results = fetcher.category_lists(countries, categories)

# ⚙️ Expert: Low-level (maximum control)
from playfast import BatchRequestBuilder
from playfast._core import fetch_and_parse_list_batch

builder = BatchRequestBuilder()
requests = list(builder.build_list_requests(countries, categories))
results = fetch_and_parse_list_batch(requests)
```

______________________________________________________________________

## AsyncIO Integration

All batch functions work with `asyncio.to_thread()`:

```python
import asyncio
from playfast import fetch_category_lists


async def fetch_data():
    # Run batch function in thread (doesn't block event loop)
    results = await asyncio.to_thread(
        fetch_category_lists,
        countries=["us", "kr"],
        categories=["GAME_ACTION"],
        num_results=100,
    )
    return results


# Can mix with other async operations
async def complex_workflow():
    other_data, apps = await asyncio.gather(
        fetch_from_api(), asyncio.to_thread(fetch_category_lists, countries, categories)
    )
    return combine(other_data, apps)
```

______________________________________________________________________

## Error Handling

```python
from playfast import fetch_category_lists
from playfast.exceptions import PlayfastError

try:
    results = fetch_category_lists(
        countries=["us", "kr"], categories=["GAME_ACTION"], num_results=100
    )
except PlayfastError as e:
    print(f"Error fetching data: {e}")
    # Handle error (retry, log, etc.)
```

**Note**: Currently, batch functions fail fast on first error. Future versions may support per-request error handling.

______________________________________________________________________

## See Also

- [OPTIMIZATION_SUMMARY.md](./OPTIMIZATION_SUMMARY.md) - Performance benchmarks
- [MEMORY_OPTIMIZATION.md](./MEMORY_OPTIMIZATION.md) - Memory efficiency guide
- See `examples/03_batch_api.py` for working code examples

______________________________________________________________________

**Last Updated**: 2025-10-13

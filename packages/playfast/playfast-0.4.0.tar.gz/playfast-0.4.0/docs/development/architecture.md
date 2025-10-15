# Architecture

Understanding Playfast's hybrid Rust + Python architecture.

## Overview

Playfast uses a **hybrid architecture** combining Python's async I/O with Rust's performance:

```
┌─────────────────────────────────────┐
│   Python Layer (High-Level API)     │
│   - AsyncClient (aiohttp)           │
│   - RustClient (wrapper)            │
│   - Pydantic Models                 │
│   - Type Hints                      │
└──────────────┬──────────────────────┘
               │ PyO3 Bindings
               ▼
┌─────────────────────────────────────┐
│   Rust Core (High-Performance)      │
│   - HTTP Client (reqwest)           │
│   - HTML Parser (scraper)           │
│   - JSON Parser (serde_json)        │
│   - Zero-Copy Operations            │
└─────────────────────────────────────┘
```

## Design Philosophy

### Why Hybrid?

**Two Client Options:**

1. **AsyncClient** (Recommended - 15x Faster!)

   - Python aiohttp for async I/O
   - Rust for CPU-intensive parsing (GIL-free)
   - True concurrent I/O operations
   - Best for: Bulk data collection, production use

1. **RustClient** (Synchronous)

   - Rust HTTP + Rust parsing
   - Complete GIL-free execution
   - Blocking, synchronous API
   - Best for: Simple scripts, Python 3.14t (future)

### Performance Comparison

| Use Case             | AsyncClient | RustClient | Winner            |
| -------------------- | ----------- | ---------- | ----------------- |
| Single request       | ~0.5s       | ~0.5s      | Tie               |
| 15 parallel requests | 0.53s       | 8.37s      | AsyncClient (15x) |
| I/O-bound tasks      | ⚡ Fast     | 🐌 Slow    | AsyncClient       |
| CPU-bound tasks      | Fast        | ⚡ Fast    | Tie               |

**Why AsyncClient is faster:**

- I/O is the bottleneck (network latency >> CPU parsing)
- AsyncClient overlaps network waiting with other requests
- RustClient blocks on each request (Python GIL prevents parallelism)

## Data Flow

### AsyncClient Flow

```
1. User calls: await client.get_app('com.spotify.music')
                       ↓
2. AsyncClient._fetch_html()
   - Uses aiohttp to download HTML (async, no blocking)
                       ↓
3. parse_app_page(html, app_id)  [Rust function via PyO3]
   - Parses HTML in Rust (GIL released, true parallelism)
   - Returns RustAppInfo
                       ↓
4. AppInfo.from_rust(rust_app_info)
   - Converts to Pydantic model
   - Validates data
                       ↓
5. Returns AppInfo to user
```

### Parallel Flow (get_apps_parallel)

```
User: await client.get_apps_parallel(['app1', 'app2', ...], ['us', 'kr', ...])
         ↓
AsyncClient creates tasks for all combinations:
  - Task 1: get_app('app1', country='us')
  - Task 2: get_app('app1', country='kr')
  - Task 3: get_app('app2', country='us')
  - Task 4: get_app('app2', country='kr')
  ...
         ↓
All tasks run concurrently (up to max_concurrent limit)
         ↓
Results collected and grouped by country
         ↓
Return: {'us': [AppInfo, AppInfo], 'kr': [AppInfo, AppInfo]}
```

## Module Structure

### Python Layer (`python/playfast/`)

**`client.py`** - AsyncClient

- High-level async API
- Uses aiohttp for HTTP
- Calls Rust parsing functions
- Manages concurrency (semaphore)

**`rust_client.py`** - RustClient

- Wrapper around Rust functions
- Synchronous API
- Direct calls to `_core` module

**`models.py`** - Pydantic Models

- `AppInfo`, `Review`, `SearchResult`, `Permission`
- Data validation
- Type coercion
- `from_rust()` classmethod for conversion

**`constants.py`** - Enums

- `Category` (GAME_ACTION, SOCIAL, etc.)
- `Collection` (TOP_FREE, NEW_FREE, etc.)
- `Age` ratings

**`exceptions.py`** - Custom Exceptions

- `AppNotFoundError`
- `RateLimitError`
- `ParseError`
- `NetworkError`

### Rust Core (`src/`)

**`lib.rs`** - PyO3 Bindings

- Python-facing API
- Function exports (`parse_app_page`, `fetch_and_parse_app`, etc.)
- Type conversions (Rust ↔ Python)

**`http.rs`** - HTTP Client

- `reqwest` for HTTP requests
- Timeout handling
- Header management

**`parser.rs`** - HTML/JSON Parsing

- Uses `scraper` for HTML
- CSS selectors for data extraction
- JSON parsing for batchexecute responses

**`models.rs`** - Rust Data Structures

- `RustAppInfo`, `RustReview`, etc.
- Serialize to Python objects
- Zero-copy where possible

**`error.rs`** - Error Types

- `PlayfastError` enum
- Converts to Python exceptions via PyO3

## Key Technologies

### Python Stack

- **aiohttp**: Async HTTP client
- **Pydantic**: Data validation
- **asyncio**: Concurrency primitives

### Rust Stack

- **PyO3**: Python bindings
- **reqwest**: HTTP client
- **scraper**: HTML parsing (based on html5ever)
- **serde**: Serialization
- **tokio**: Async runtime

## Performance Optimizations

### 1. GIL Release

Rust functions release the Python GIL:

```rust
#[pyfunction]
fn parse_app_page(py: Python, html: &str, app_id: &str) -> PyResult<RustAppInfo> {
    py.allow_threads(|| {
        // This code runs without GIL
        // Multiple threads can execute in parallel
        parse_app_page_internal(html, app_id)
    })
}
```

### 2. Zero-Copy Strings

Pass strings by reference where possible:

```rust
// ❌ Bad: copies string
fn parse(html: String) -> Result<...>

// ✅ Good: borrows string
fn parse(html: &str) -> Result<...>
```

### 3. Concurrent I/O

AsyncClient uses asyncio semaphore:

```python
async def get_app(self, app_id: str) -> AppInfo:
    async with self._semaphore:  # Limit concurrency
        html = await self._fetch_html(app_id)
        return parse_app_page(html, app_id)  # Rust (GIL released)
```

### 4. Memory Efficiency

Stream large datasets instead of loading all at once:

```python
async def stream_reviews(self, app_id: str):
    token = None
    while True:
        reviews, token = await self._fetch_reviews(app_id, token)
        for review in reviews:
            yield review  # Stream one at a time
        if not token:
            break
```

## Future: Python 3.14t Free-Threading

With PEP 703 (removing GIL), RustClient will become much faster:

```
Current (Python 3.12 with GIL):
- RustClient + ThreadPoolExecutor: ❌ No speedup (GIL blocks)
- AsyncClient: ✅ Fast (async I/O bypasses GIL)

Future (Python 3.14t without GIL):
- RustClient + threads: ✅ Fast (true parallelism)
- AsyncClient: ✅ Still fast (async I/O still works)
```

## Testing Strategy

- **Unit Tests**: Test individual functions in isolation
- **Integration Tests**: Test full workflows (marked with `@pytest.mark.integration`)
- **Property Tests**: Test invariants (e.g., all apps have app_id)
- **Performance Tests**: Benchmark critical paths

See [Testing](testing.md) for details.

## Next Steps

- [Contributing](contributing.md) - Make changes
- [Testing](testing.md) - Write tests
- [Benchmarking](benchmarking.md) - Measure performance

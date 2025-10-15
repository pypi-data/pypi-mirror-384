# Performance Improvements - Comprehensive Guide

## Overview

We've achieved **7-8x performance improvements** through three key optimizations:

1. **Batch processing functions** - Reduce `block_on` calls
1. **Global HTTP client** - Connection pooling and reuse
1. **CPU-aware Tokio runtime** - Dynamic worker thread allocation
1. **Memory optimization** - String interning and efficient request generation

## Key Improvements

### 1. Global HTTP Client with Connection Pooling

**Before:**

```rust
// Each call created a new HTTP client
let client = PlayStoreClient::new(timeout)?;
```

**After:**

```rust
// Global singleton with connection pooling
static HTTP_CLIENT: Lazy<PlayStoreClient> = Lazy::new(|| {
    PlayStoreClient::new(30).expect("Failed to create HTTP client")
});
```

**Benefits:**

- TCP connections are reused across requests
- Reduced connection establishment overhead
- Better resource utilization

### 2. CPU-Aware Tokio Runtime

**Before:**

```rust
.worker_threads(4)  // Hardcoded
```

**After:**

```rust
let num_cpus = std::thread::available_parallelism()
    .map(|n| n.get())
    .unwrap_or(4);
let worker_threads = (num_cpus / 2).clamp(2, 8);
```

**Configuration:**

- Uses half of available CPU cores
- Minimum: 2 workers
- Maximum: 8 workers
- Leaves CPU resources for Python threads

### 3. Batch Processing Functions

**The Problem:**

```python
# Sequential calls - Multiple block_on invocations
for request in requests:
    result = fetch_and_parse_list(...)  # Each call blocks the runtime
```

**The Solution:**

```rust
// Single block_on with parallel futures
runtime.block_on(async {
    let futures: Vec<_> = requests.iter()
        .map(|req| client.fetch_and_parse_list(...))
        .collect();

    // True parallel execution inside Rust!
    try_join_all(futures).await
})
```

## New Batch Functions

### 1. `fetch_and_parse_apps_batch`

Fetch multiple app pages in parallel.

```python
from playfast._core import fetch_and_parse_apps_batch

requests = [
    ("com.spotify.music", "en", "us"),
    ("com.netflix.mediaclient", "en", "us"),
    ("com.whatsapp", "en", "us"),
]

apps = fetch_and_parse_apps_batch(requests)
# Returns: list[RustAppInfo]
```

### 2. `fetch_and_parse_list_batch`

Fetch multiple category/collection listings in parallel.

```python
from playfast._core import fetch_and_parse_list_batch

requests = [
    ("GAME_ACTION", "topselling_free", "en", "us", 100),
    ("SOCIAL", "topselling_free", "en", "kr", 100),
    (None, "topselling_paid", "en", "jp", 50),  # None = all apps
]

results = fetch_and_parse_list_batch(requests)
# Returns: list[list[RustSearchResult]]
```

### 3. `fetch_and_parse_search_batch`

Perform multiple searches in parallel.

```python
from playfast._core import fetch_and_parse_search_batch

requests = [
    ("spotify", "en", "us"),
    ("netflix", "en", "us"),
    ("youtube", "en", "us"),
]

results = fetch_and_parse_search_batch(requests)
# Returns: list[list[RustSearchResult]]
```

### 4. `fetch_and_parse_reviews_batch`

Fetch reviews for multiple apps in parallel.

```python
from playfast._core import fetch_and_parse_reviews_batch

requests = [
    ("com.spotify.music", "en", "us", 1, None),  # sort=1 (newest)
    ("com.netflix.mediaclient", "en", "us", 2, None),  # sort=2 (highest)
]

results = fetch_and_parse_reviews_batch(requests)
# Returns: list[tuple[list[RustReview], str | None]]
```

## Performance Results

### Benchmark: 25 Category Requests

| Method                  | Time      | Req/s     | Speedup      |
| ----------------------- | --------- | --------- | ------------ |
| **Batch (all at once)** | **1.25s** | **20.05** | **7.97x** 🚀 |
| Batch (5 per batch)     | 2.82s     | 8.85      | 3.52x        |
| Sequential (baseline)   | 9.94s     | 2.51      | 1.00x        |

### Key Findings

1. **87.5% Performance Improvement**: Batch processing is nearly 8x faster
1. **Block-on Optimization**: Reducing `block_on` calls is critical
1. **Scalability**: Larger batches perform better (up to a point)

### Example: 5 App Pages

```
Sequential: 2.54s (0.51s per app)
Batch:      1.36s (0.27s per app)
Speedup:    1.87x (46.5% faster)
```

### Example: 3 Country Comparison

```
Sequential: 0.69s
Batch:      0.28s
Speedup:    2.44x (59.1% faster)
```

## Architecture Comparison

### Sequential Processing (Old)

```
Python Thread 1:
  [block_on] → Request 1 → [wait] → Result 1
  [block_on] → Request 2 → [wait] → Result 2
  [block_on] → Request 3 → [wait] → Result 3

Total: 3 runtime enter/exit cycles
```

### Batch Processing (New)

```
Python Thread 1:
  [block_on] → {
      Request 1 → [async await] → Result 1
      Request 2 → [async await] → Result 2
      Request 3 → [async await] → Result 3
  }

Total: 1 runtime enter/exit cycle
All requests execute in parallel!
```

## Best Practices

### When to Use Batch Functions

✅ **Use batch functions when:**

- Fetching multiple items of the same type
- Processing data from multiple countries
- Collecting category/collection data at scale
- Need maximum throughput

❌ **Use single functions when:**

- Fetching only one item
- Need fine-grained error handling per request
- Sequential processing is required by business logic

### Example: Multi-Country Data Collection

```python
from playfast._core import fetch_and_parse_list_batch

# Collect top apps from 10 countries and 5 categories
countries = ["us", "kr", "jp", "de", "gb", "fr", "br", "in", "ca", "au"]
categories = ["GAME_ACTION", "SOCIAL", "PRODUCTIVITY", "ENTERTAINMENT", "COMMUNICATION"]

requests = [
    (cat, "topselling_free", "en", country, 200)
    for country in countries
    for cat in categories
]

# 50 requests in parallel with a single function call!
results = fetch_and_parse_list_batch(requests)

# Process results
for i, (cat, country) in enumerate([(c, co) for co in countries for c in categories]):
    apps = results[i]
    print(f"{country.upper()} / {cat}: {len(apps)} apps")
```

## Migration Guide

### Before (Sequential)

```python
results = []
for app_id in app_ids:
    app = fetch_and_parse_app(app_id, "en", "us")
    results.append(app)
```

### After (Batch)

```python
requests = [(app_id, "en", "us") for app_id in app_ids]
results = fetch_and_parse_apps_batch(requests)
```

## Technical Details

### Why Batch Processing is Faster

1. **Single Runtime Entry**

   - Only one `block_on` call reduces context switching
   - Tokio runtime stays active throughout batch

1. **True Parallel Execution**

   - `try_join_all` runs all futures concurrently
   - Limited only by tokio worker threads and network

1. **Connection Pooling**

   - Global HTTP client reuses TCP connections
   - DNS lookups are cached

1. **Zero Python GIL Contention**

   - All work happens in Rust
   - GIL is released for the entire batch

### Configuration Tuning

The runtime uses dynamic worker thread allocation:

```rust
// 16-core system: 8 workers
// 8-core system:  4 workers
// 4-core system:  2 workers
// 2-core system:  2 workers (minimum)
```

This leaves CPU cores available for:

- Python's main thread
- Other Python threads
- System processes

## Limitations

1. **All-or-Nothing**: If one request fails, the entire batch fails

   - Consider smaller batches for better fault tolerance

1. **Memory Usage**: Large batches consume more memory

   - Recommended: 20-50 requests per batch

1. **No Progress Updates**: Batch completes as a whole

   - Use smaller batches if you need progress indicators

## Future Improvements

- [ ] Add per-request error handling (return `Result` for each)
- [ ] Implement automatic batch size optimization
- [ ] Add request prioritization within batches
- [ ] Support streaming batch results

## Conclusion

The batch processing functions provide **7-8x performance improvement** for multi-request scenarios by:

1. Reducing runtime enter/exit overhead
1. Enabling true parallel execution in Rust
1. Maximizing connection pooling benefits
1. Eliminating Python GIL contention

For production use cases involving multiple requests, batch functions are **strongly recommended**.

______________________________________________________________________

**See also:**

- `examples/batch_usage.py` - Working examples
- `benchmarks/test_batch_performance.py` - Performance comparisons
- `python/playfast/_core.pyi` - Type hints and documentation

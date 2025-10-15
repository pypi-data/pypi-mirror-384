# Memory Optimization for Batch Processing

## Overview

This document explains memory usage patterns in batch processing and provides utilities for memory-efficient request generation.

## Memory Analysis Results

### Single Request Memory Footprint

```
Single Request Tuple: 88 bytes
  - category string: 68 bytes
  - collection string: 72 bytes
  - lang string: 59 bytes
  - country string: 59 bytes
  - num integer: 44 bytes
Total string content: ~302 bytes
```

### Batch Request Memory Usage

For 15 requests (5 countries × 3 categories):

- List container overhead: 184 bytes
- Per-request overhead: ~12 bytes
- **String memory (with sharing): ~630 bytes**
- **String memory (without sharing): ~3,870 bytes**

**Potential savings: 83.7% through string sharing!**

### Large-Scale Scenario (10,000 requests)

```
Memory Breakdown:
  - List container: ~78 KB
  - Tuple overhead: ~859 KB
  - Strings (shared): ~0.6 KB
  Total: ~938 KB

Per-request average: ~96 bytes
```

## Python's Built-in Optimizations

### String Interning (Automatic)

**Good News**: Python automatically interns string literals at compile time!

```python
# These strings are AUTOMATICALLY shared:
req1 = ("GAME_ACTION", "topselling_free", "en", "us", 100)
req2 = ("SOCIAL", "topselling_free", "en", "kr", 100)

# Same object!
assert req1[1] is req2[1]  # "topselling_free" is shared
assert req1[2] is req2[2]  # "en" is shared
```

### When Manual Interning Helps

String interning is beneficial for strings from:

1. **User input**
1. **File reading**
1. **Network responses**
1. **String concatenation/formatting**

```python
import sys

# Strings from runtime (e.g., config file)
country = load_from_config()  # New string object each time

# Manual interning for reuse
country_interned = sys.intern(country)
```

## BatchRequestBuilder - Memory-Efficient Utility

### Basic Usage

```python
from playfast import BatchRequestBuilder
from playfast._core import fetch_and_parse_list_batch

# Create builder with common parameters
builder = BatchRequestBuilder(
    collection="topselling_free",
    lang="en",
    num_results=100,
    intern_strings=True,  # Enable string interning
)

# Generate requests (uses generator for lazy evaluation)
requests = list(
    builder.build_list_requests(
        countries=["us", "kr", "jp", "de", "gb"],
        categories=["GAME_ACTION", "SOCIAL", "PRODUCTIVITY"],
    )
)

# Fetch data in batch
results = fetch_and_parse_list_batch(requests)
```

### Features

#### 1. String Interning & Caching

```python
builder = BatchRequestBuilder(intern_strings=True)

# First call: interns the string
req1 = builder.build_list_requests(["us"], ["GAME_ACTION"])

# Subsequent calls: reuses interned string from cache
req2 = builder.build_list_requests(["us"], ["SOCIAL"])

# Check cache
stats = builder.get_memory_stats()
print(stats["cached_strings"])  # Number of unique interned strings
```

#### 2. Lazy Evaluation with Generators

```python
# Generator doesn't allocate memory until consumed
request_gen = builder.build_list_requests(
    countries=large_country_list,  # 100 countries
    categories=large_category_list,  # 20 categories
)

# Process in chunks without loading all 2000 requests at once
for i in range(0, 2000, 100):
    chunk = list(itertools.islice(request_gen, 100))
    results = fetch_and_parse_list_batch(chunk)
    process_results(results)
```

#### 3. Convenience Functions

```python
from playfast import build_multi_country_requests

# Quick helper for common use case
requests = build_multi_country_requests(
    countries=["us", "kr", "jp"], categories=["GAME_ACTION", "SOCIAL"], num_results=50
)
```

### Advanced Usage

#### Multi-Country App Collection

```python
from playfast import build_app_country_matrix
from playfast._core import fetch_and_parse_apps_batch

# Collect same apps from multiple countries
requests = build_app_country_matrix(
    app_ids=["com.spotify.music", "com.netflix.mediaclient", "com.whatsapp"],
    countries=["us", "kr", "jp", "de", "gb"],
)

# 3 apps × 5 countries = 15 requests
apps = fetch_and_parse_apps_batch(requests)
```

#### Custom Builder for Specific Use Case

```python
class MyCustomBuilder(BatchRequestBuilder):
    """Custom builder with preset configuration"""

    def __init__(self):
        super().__init__(
            collection="topselling_paid",  # Paid apps only
            lang="en",
            num_results=200,  # More results
            intern_strings=True,
        )

    def build_premium_game_requests(self, countries):
        """Shortcut for premium games"""
        return self.build_list_requests(
            countries=countries, categories=["GAME_ACTION", "GAME_STRATEGY", "GAME_RPG"]
        )


# Usage
builder = MyCustomBuilder()
requests = list(builder.build_premium_game_requests(["us", "kr", "jp"]))
```

## Performance Comparison

### Request Generation Performance

Tested with 15 requests (5 countries × 3 categories):

| Method             | Time   | vs Standard |
| ------------------ | ------ | ----------- |
| Variable Caching   | 0.669s | -15.0%      |
| Explicit Interning | 0.670s | -14.9%      |
| Itertools Product  | 0.678s | -13.9%      |
| Standard           | 0.788s | baseline    |

**Conclusion**: All approaches perform similarly. The slight improvements are within margin of error.

### Memory vs Performance Trade-offs

```
Memory Optimization Priority:
  1. Use batch functions (7-8x faster) ✅ CRITICAL
  2. Reduce block_on calls ✅ CRITICAL
  3. String interning (~83% memory savings) ✅ Nice-to-have
  4. Generator-based construction ✅ Nice-to-have

Performance Impact:
  - Batch processing: +700% faster ⚡
  - String interning: ~0.1% slower (negligible)
  - Generators: No overhead until consumed
```

## Best Practices

### When to Use BatchRequestBuilder

✅ **Use when:**

- Generating 100+ requests
- Many repeated parameter values
- Memory-constrained environments
- Need organized request management

❌ **Don't use when:**

- Very small batches (< 10 requests) - overhead not worth it
- All parameters are unique - no reuse benefit
- Simple one-off requests

### Memory-Efficient Patterns

#### Pattern 1: Chunked Processing

```python
builder = BatchRequestBuilder()

# Generate all requests
all_requests = builder.build_list_requests(
    countries=countries, categories=categories  # 100 countries  # 10 categories
)

# Process in manageable chunks
CHUNK_SIZE = 50
for chunk in chunks(all_requests, CHUNK_SIZE):
    results = fetch_and_parse_list_batch(list(chunk))
    process_and_save(results)
    # Chunk memory is freed before next iteration
```

#### Pattern 2: Streaming with Generators

```python
def generate_requests():
    """Generate requests on-demand"""
    builder = BatchRequestBuilder()

    for country in countries:
        for category in categories:
            # Yield single request
            yield next(builder.build_list_requests([country], [category]))


# Process without loading all requests into memory
for request_batch in batch_generator(generate_requests(), 20):
    results = fetch_and_parse_list_batch(request_batch)
```

#### Pattern 3: Parameter Reuse

```python
# Reuse common parameters across batches
builder = BatchRequestBuilder(
    collection="topselling_free",  # Shared
    lang="en",  # Shared
    num_results=100,  # Shared
)

# Batch 1: Different countries, same categories
batch1 = list(
    builder.build_list_requests(
        countries=["us", "ca", "gb"], categories=["GAME_ACTION", "SOCIAL"]
    )
)

# Batch 2: Different countries, same categories
# Strings are reused from builder's cache
batch2 = list(
    builder.build_list_requests(
        countries=["kr", "jp", "cn"], categories=["GAME_ACTION", "SOCIAL"]
    )
)
```

## Memory Profiling

### Using memory_profiler (Optional)

```bash
# Install
pip install memory-profiler

# Profile your script
python -m memory_profiler your_script.py
```

### Manual Memory Tracking

```python
import sys
import tracemalloc

tracemalloc.start()

# Your code here
builder = BatchRequestBuilder()
requests = list(builder.build_list_requests(countries, categories))

current, peak = tracemalloc.get_traced_memory()
print(f"Current: {current / 1024 / 1024:.1f} MB")
print(f"Peak: {peak / 1024 / 1024:.1f} MB")

tracemalloc.stop()
```

## Real-World Example

### Scenario: Daily Collection of Top Apps from 50 Countries

```python
from playfast import BatchRequestBuilder
from playfast._core import fetch_and_parse_list_batch

# Configuration
COUNTRIES = ["us", "kr", "jp", ...]  # 50 countries
CATEGORIES = ["GAME_ACTION", "SOCIAL", "PRODUCTIVITY", ...]  # 10 categories
CHUNK_SIZE = 25  # Process 25 requests at a time


def daily_collection():
    """Collect top apps daily - memory efficient"""
    builder = BatchRequestBuilder(
        collection="topselling_free", num_results=200, intern_strings=True
    )

    # Generate all requests (50 × 10 = 500)
    print("Generating requests...")
    all_requests = list(
        builder.build_list_requests(countries=COUNTRIES, categories=CATEGORIES)
    )

    print(f"Memory stats: {builder.get_memory_stats()}")
    print(f"Total requests: {len(all_requests)}")

    # Process in chunks
    total_apps = 0
    for i in range(0, len(all_requests), CHUNK_SIZE):
        chunk = all_requests[i : i + CHUNK_SIZE]

        print(f"Processing chunk {i//CHUNK_SIZE + 1}...")
        results = fetch_and_parse_list_batch(chunk)

        # Save to database
        for apps in results:
            save_to_db(apps)
            total_apps += len(apps)

        print(f"  Collected {len(results)} lists, {total_apps} apps total")

    print(f"\nDaily collection complete: {total_apps} apps")


if __name__ == "__main__":
    daily_collection()
```

**Expected Performance**:

- 500 requests in ~20 chunks
- ~10-15 seconds total time
- ~1-2 MB peak memory (with chunks)
- vs ~5-10 MB if all loaded at once

## Summary

### Key Takeaways

1. **Python's automatic string interning is effective**

   - String literals are automatically shared
   - Manual interning helps for runtime-generated strings

1. **Memory savings are significant at scale**

   - 83.7% memory reduction with string sharing
   - ~96 bytes per request (10K request scenario)

1. **Performance impact is negligible**

   - \<5% difference between approaches
   - Focus on batch processing (7-8x speedup!) instead

1. **BatchRequestBuilder provides convenience**

   - Organized request management
   - Built-in string caching
   - Generator support for streaming
   - Minimal overhead

### Recommendations

| Scenario                 | Approach                       |
| ------------------------ | ------------------------------ |
| Small batches (< 10)     | Direct list comprehension      |
| Medium batches (10-100)  | BatchRequestBuilder or direct  |
| Large batches (100-1000) | BatchRequestBuilder + chunking |
| Very large (1000+)       | Generator + streaming          |
| Memory constrained       | Always use builders + chunking |

______________________________________________________________________

**See also**:

- `examples/batch_builder_usage.py` - Working examples
- `benchmarks/memory_simple.py` - Memory analysis
- `python/playfast/batch_builder.py` - Source code

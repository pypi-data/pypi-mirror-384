# Playfast Benchmarks

This directory contains benchmarks to measure the performance of Playfast's various APIs.

## Benchmark Files

### 1. `single_app_benchmark.py`

Tests single app fetching performance:

- RustClient (Rust HTTP + Rust parsing)
- AsyncClient (Python async HTTP + Rust parsing)

**Usage:**

```bash
uv run python benchmarks/single_app_benchmark.py
```

### 2. `batch_apps_benchmark.py`

Tests batch app fetching across multiple countries:

- Sequential (baseline)
- RustClient + ThreadPoolExecutor
- AsyncClient with async/await
- High-level batch API (`fetch_apps`)

**Usage:**

```bash
uv run python benchmarks/batch_apps_benchmark.py
```

### 3. `batch_category_benchmark.py`

Tests category list fetching (top apps):

- Sequential (baseline)
- High-level batch API (`fetch_category_lists`)

**Usage:**

```bash
uv run python benchmarks/batch_category_benchmark.py
```

## Running All Benchmarks

Run all benchmarks at once:

```bash
uv run python benchmarks/single_app_benchmark.py
uv run python benchmarks/batch_apps_benchmark.py
uv run python benchmarks/batch_category_benchmark.py
```

## Expected Performance

Based on current implementation:

**Single App:**

- RustClient: ~0.5-1.0s per request
- AsyncClient: ~0.5-1.0s per request

**Batch Apps (9 apps × 3 countries = 27 requests):**

- Sequential: ~20-30s
- ThreadPool-10: ~3-5s (5-7x faster)
- AsyncClient-10: ~3-5s (5-7x faster)
- Batch API: ~3-5s (5-7x faster)

**Batch Categories (3 countries × 3 categories = 9 requests):**

- Sequential: ~10-15s
- Batch API: ~2-3s (4-6x faster)

## Performance Tips

1. **Use batch APIs for multiple requests**: `fetch_apps()`, `fetch_category_lists()` are optimized for parallel execution
1. **RustClient is fastest for CPU-bound workloads**: True parallel execution with GIL release
1. **AsyncClient is easier for I/O-bound workloads**: Natural async/await syntax
1. **Adjust concurrency**: Balance between speed and rate limiting (default: 10-15 concurrent)

## Customizing Benchmarks

Edit the configuration variables at the top of each file:

- `APP_IDS`: List of app package IDs to test
- `COUNTRIES`: List of country codes
- `CATEGORIES`: List of category names
- `NUM_RESULTS`: Number of results per request

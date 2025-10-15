# Benchmarking

Performance testing and benchmarking in Playfast.

## Running Benchmarks

### Compare Clients

```bash
# Compare AsyncClient vs RustClient
uv run python benchmarks/compare_clients.py

# Output:
# AsyncClient (15 concurrent): 0.53s (28.3 req/s) - 15.8x speedup
# RustClient (sequential):     8.37s (1.8 req/s) - 1.0x baseline
```

### Memory Profiling

```bash
# Profile memory usage
uv run python benchmarks/memory_profiling.py

# Output:
# 200 apps: 15.18 MB peak, 0.29 MB after GC (1.5 KB/app)
```

### Large Scale Collection

```bash
# Test with 1000+ apps
uv run python benchmarks/large_scale_collection_v2.py
```

## Benchmark Results

### AsyncClient Performance (15 concurrent requests)

| Method                      | Time  | Req/s | Speedup   |
| --------------------------- | ----- | ----- | --------- |
| AsyncClient (15 concurrent) | 0.53s | 28.3  | **15.8x** |
| AsyncClient (10 concurrent) | 0.84s | 17.8  | 10.0x     |
| RustClient (sequential)     | 8.37s | 1.8   | 1.0x      |

**Key Findings:**

- ⚡ AsyncClient is **15-16x faster** for I/O-bound operations
- 🎯 **93.7% time saved** (8.37s → 0.53s)
- 💡 Optimal concurrency: 15-20 concurrent requests

### Memory Efficiency

| Apps | Peak Memory | After GC | Per App    |
| ---- | ----------- | -------- | ---------- |
| 50   | 4.09 MB     | 0.10 MB  | 2.0 KB     |
| 100  | 7.73 MB     | 0.16 MB  | 1.7 KB     |
| 200  | 15.18 MB    | 0.29 MB  | **1.5 KB** |

**Linear scaling, no memory leaks!**

## Writing Benchmarks

### Simple Benchmark

```python
import asyncio
import time
from playfast import AsyncClient


async def benchmark_get_app():
    """Benchmark single app fetch."""
    client = AsyncClient()

    start = time.time()
    app = await client.get_app("com.spotify.music")
    elapsed = time.time() - start

    print(f"Time: {elapsed:.2f}s")


asyncio.run(benchmark_get_app())
```

### Parallel Benchmark

```python
async def benchmark_parallel():
    """Benchmark parallel fetches."""
    app_ids = ["com.spotify.music", "com.netflix.mediaclient", ...]

    client = AsyncClient(max_concurrent=15)

    start = time.time()
    results = await client.get_apps_parallel(app_ids)
    elapsed = time.time() - start

    print(f"Fetched {len(app_ids)} apps in {elapsed:.2f}s")
    print(f"Rate: {len(app_ids)/elapsed:.1f} req/s")
```

### Memory Benchmark

```python
import tracemalloc
import asyncio
from playfast import AsyncClient


async def benchmark_memory():
    """Benchmark memory usage."""
    tracemalloc.start()

    client = AsyncClient()
    apps = []

    snapshot1 = tracemalloc.take_snapshot()

    # Fetch 200 apps
    for i in range(200):
        app = await client.get_app(f"com.app{i}")
        apps.append(app)

    snapshot2 = tracemalloc.take_snapshot()

    stats = snapshot2.compare_to(snapshot1, "lineno")
    total = sum(stat.size_diff for stat in stats)

    print(f"Memory used: {total / 1024 / 1024:.2f} MB")
    print(f"Per app: {total / 200 / 1024:.2f} KB")

    tracemalloc.stop()
```

## Profiling

### Python Profiling

```python
import cProfile
import pstats
import asyncio

# Profile code
cProfile.run("asyncio.run(main())", "profile.stats")

# Analyze results
stats = pstats.Stats("profile.stats")
stats.sort_stats("cumulative")
stats.print_stats(20)
```

### Using py-spy

```bash
# Record profile
py-spy record -o profile.svg -- python benchmarks/compare_clients.py

# Live view
py-spy top -- python benchmarks/compare_clients.py
```

### Rust Profiling

```bash
# Build with debug symbols
cargo build --release --profile release-with-debug

# Profile with perf (Linux)
perf record -g target/release/playfast
perf report

# Profile with Instruments (macOS)
instruments -t "Time Profiler" target/release/playfast
```

## Optimization Tips

### 1. Increase Concurrency

```python
# Try different concurrency levels
for concurrent in [5, 10, 15, 20, 25, 30]:
    client = AsyncClient(max_concurrent=concurrent)
    # benchmark...
```

### 2. Batch Operations

```python
# Process in chunks
chunk_size = 100
for i in range(0, len(app_ids), chunk_size):
    chunk = app_ids[i : i + chunk_size]
    results = await client.get_apps_parallel(chunk)
```

### 3. Use Connection Pooling

AsyncClient automatically uses connection pooling via aiohttp.

### 4. Optimize Parsing

Rust parsing is already optimized, but you can:

- Use release builds (`--release`)
- Enable LTO in Cargo.toml
- Use CPU-specific optimizations

## Performance Targets

- **Single request**: < 1 second
- **100 parallel requests**: < 5 seconds
- **Memory per app**: < 2 KB
- **Throughput**: > 20 req/s

## Continuous Performance Monitoring

Run benchmarks regularly:

- Before major releases
- After performance-related changes
- Weekly automated runs

Track metrics over time:

- Request latency (p50, p95, p99)
- Throughput (requests/second)
- Memory usage
- Error rates

## Next Steps

- [Architecture](architecture.md) - Understand performance design
- [Contributing](contributing.md) - Optimize performance
- [Testing](testing.md) - Test performance changes

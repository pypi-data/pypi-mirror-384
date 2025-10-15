"""Benchmark: Single App Fetching.

Tests the performance of fetching a single app using different methods:
1. RustClient.get_app() - Direct Rust HTTP + parsing
2. AsyncClient.get_app() - Python async HTTP + Rust parsing
"""

import asyncio
import time

from playfast import AsyncClient, RustClient


def benchmark_rust_client(
    app_id: str = "com.spotify.music", iterations: int = 10
) -> None:
    """Benchmark RustClient for single app fetching."""
    print("\n" + "=" * 80)
    print("Benchmark 1: RustClient (Rust HTTP + Rust parsing)")
    print("=" * 80)

    client = RustClient(timeout=30)
    times = []

    for i in range(iterations):
        start = time.time()
        app = client.get_app(app_id)
        elapsed = time.time() - start
        times.append(elapsed)
        print(
            f"  [{i + 1:2d}/{iterations}] {elapsed:.3f}s - {app.title} ({app.score}⭐)"
        )

    avg_time = sum(times) / len(times)
    print(f"\n>> Average: {avg_time:.3f}s per request")
    print(f">> Throughput: {1 / avg_time:.2f} requests/second")


async def benchmark_async_client(
    app_id: str = "com.spotify.music", iterations: int = 10
) -> None:
    """Benchmark AsyncClient for single app fetching."""
    print("\n" + "=" * 80)
    print("Benchmark 2: AsyncClient (Python async HTTP + Rust parsing)")
    print("=" * 80)

    async with AsyncClient() as client:
        times = []

        for i in range(iterations):
            start = time.time()
            app = await client.get_app(app_id)
            elapsed = time.time() - start
            times.append(elapsed)
            print(
                f"  [{i + 1:2d}/{iterations}] {elapsed:.3f}s - {app.title} ({app.score}⭐)"
            )

        avg_time = sum(times) / len(times)
        print(f"\n>> Average: {avg_time:.3f}s per request")
        print(f">> Throughput: {1 / avg_time:.2f} requests/second")


async def main() -> None:
    """Run all benchmarks."""
    print("=" * 80)
    print("SINGLE APP FETCHING BENCHMARK")
    print("=" * 80)
    print("\nConfiguration:")
    print("  App ID: com.spotify.music")
    print("  Iterations: 10")
    print("  Country: us")

    # Run benchmarks
    benchmark_rust_client()
    await benchmark_async_client()

    print("\n" + "=" * 80)
    print("Benchmark completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

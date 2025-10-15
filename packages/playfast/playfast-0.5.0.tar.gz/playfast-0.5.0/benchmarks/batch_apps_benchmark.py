"""Benchmark: Batch App Fetching.

Tests the performance of fetching multiple apps across multiple countries:
1. Sequential fetching (baseline)
2. RustClient with ThreadPoolExecutor
3. AsyncClient with async/await
4. High-level batch API (fetch_apps)
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
from typing import Any

from playfast import AsyncClient, RustClient, fetch_apps
from playfast.models import AppInfo


# Test data
APP_IDS = [
    "com.spotify.music",
    "com.netflix.mediaclient",
    "com.google.android.youtube",
]
COUNTRIES = ["us", "kr", "jp"]


def print_header(title: str) -> None:
    """Print section header."""
    print("\n" + "=" * 80)
    print(f"{title:^80}")
    print("=" * 80)


def benchmark_sequential() -> float:
    """Benchmark 1: Sequential fetching (baseline)."""
    print_header("Benchmark 1: Sequential (Baseline)")

    client = RustClient(timeout=30)
    start = time.time()
    apps: list[AppInfo] = []

    for country in COUNTRIES:
        for app_id in APP_IDS:
            try:
                app = client.get_app(app_id, country=country)
                apps.append(app)
                print(
                    f"  [{len(apps):2d}/{len(APP_IDS) * len(COUNTRIES)}] {country.upper()}/{app_id[-20:]:20s} - {app.title[:30]}"
                )
            except Exception as e:
                print(f"  Error: {app_id} in {country}: {e}")

    elapsed = time.time() - start
    print(f"\n>> Collected {len(apps)} apps in {elapsed:.2f}s")
    print(f">> Average: {elapsed / len(apps):.3f}s per app")
    print(f">> Throughput: {len(apps) / elapsed:.2f} apps/second")
    return elapsed


def benchmark_rust_threads(max_workers: int = 10) -> float:
    """Benchmark 2: RustClient with ThreadPoolExecutor."""
    print_header(
        f"Benchmark 2: RustClient + ThreadPoolExecutor ({max_workers} workers)"
    )

    client = RustClient(timeout=30)

    def fetch_one(app_id: str, country: str) -> AppInfo:
        return client.get_app(app_id, country=country)

    start = time.time()
    apps: list[AppInfo] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures: list[tuple[str, str, Any]] = []
        for country in COUNTRIES:
            for app_id in APP_IDS:
                future = executor.submit(fetch_one, app_id, country)
                futures.append((country, app_id, future))

        for country, app_id, future in futures:
            try:
                app = future.result()
                apps.append(app)
                print(
                    f"  [{len(apps):2d}/{len(futures)}] {country.upper()}/{app_id[-20:]:20s} - {app.title[:30]}"
                )
            except Exception as e:
                print(f"  Error: {app_id} in {country}: {e}")

    elapsed = time.time() - start
    print(f"\n>> Collected {len(apps)} apps in {elapsed:.2f}s")
    print(f">> Average: {elapsed / len(apps):.3f}s per app")
    print(f">> Throughput: {len(apps) / elapsed:.2f} apps/second")
    return elapsed


async def benchmark_async_client(max_concurrent: int = 10) -> float:
    """Benchmark 3: AsyncClient with async/await."""
    print_header(f"Benchmark 3: AsyncClient ({max_concurrent} concurrent)")

    async with AsyncClient(max_concurrent=max_concurrent) as client:
        start = time.time()
        tasks: list[tuple[str, str, Any]] = []

        for country in COUNTRIES:
            for app_id in APP_IDS:
                task = asyncio.create_task(client.get_app(app_id, country=country))
                tasks.append((country, app_id, task))

        apps: list[AppInfo] = []
        for country, app_id, task in tasks:
            try:
                app = await task
                apps.append(app)
                print(
                    f"  [{len(apps):2d}/{len(tasks)}] {country.upper()}/{app_id[-20:]:20s} - {app.title[:30]}"
                )
            except Exception as e:
                print(f"  Error: {app_id} in {country}: {e}")

    elapsed = time.time() - start
    print(f"\n>> Collected {len(apps)} apps in {elapsed:.2f}s")
    print(f">> Average: {elapsed / len(apps):.3f}s per app")
    print(f">> Throughput: {len(apps) / elapsed:.2f} apps/second")
    return elapsed


def benchmark_batch_api() -> float:
    """Benchmark 4: High-level batch API."""
    print_header("Benchmark 4: Batch API (fetch_apps)")

    start = time.time()
    apps = fetch_apps(app_ids=APP_IDS, countries=COUNTRIES, lang="en")
    elapsed = time.time() - start

    for i, app in enumerate(apps, 1):
        print(f"  [{i:2d}/{len(apps)}] {app.title[:30]}")

    print(f"\n>> Collected {len(apps)} apps in {elapsed:.2f}s")
    print(f">> Average: {elapsed / len(apps):.3f}s per app")
    print(f">> Throughput: {len(apps) / elapsed:.2f} apps/second")
    return elapsed


async def main() -> None:
    """Run all benchmarks."""
    print_header("BATCH APP FETCHING BENCHMARK")
    print("\nConfiguration:")
    print(f"  Apps: {len(APP_IDS)} ({', '.join([a.split('.')[-1] for a in APP_IDS])})")
    print(f"  Countries: {len(COUNTRIES)} ({', '.join(COUNTRIES)})")
    print(f"  Total requests: {len(APP_IDS) * len(COUNTRIES)}")

    results = {}

    # Run benchmarks
    results["Sequential"] = benchmark_sequential()
    results["ThreadPool-10"] = benchmark_rust_threads(10)
    results["AsyncClient-10"] = await benchmark_async_client(10)
    results["Batch API"] = benchmark_batch_api()

    # Summary
    print_header("SUMMARY")
    sorted_results = sorted(results.items(), key=lambda x: x[1])

    print(f"\n{'Method':<25} {'Time':>10} {'Speedup':>10}")
    print("-" * 50)

    baseline = results["Sequential"]
    for method, elapsed in sorted_results:
        speedup = baseline / elapsed
        print(f"{method:<25} {elapsed:>8.2f}s {speedup:>9.2f}x")

    fastest = sorted_results[0]
    print(f"\nFastest: {fastest[0]} ({fastest[1]:.2f}s)")
    print(f"Speedup vs Sequential: {baseline / fastest[1]:.2f}x")


if __name__ == "__main__":
    asyncio.run(main())

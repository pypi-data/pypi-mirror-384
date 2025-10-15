"""Benchmark: Batch Category List Fetching.

Tests the performance of fetching category lists (top apps) across countries:
1. Sequential fetching (baseline)
2. High-level batch API (fetch_category_lists)
"""

import time

from playfast import RustClient, fetch_category_lists


# Test data
COUNTRIES = ["us", "kr", "jp"]
CATEGORIES = ["GAME_ACTION", "SOCIAL", "PRODUCTIVITY"]
COLLECTION = "topselling_free"
NUM_RESULTS = 50


def print_header(title: str) -> None:
    """Print section header."""
    print("\n" + "=" * 80)
    print(f"{title:^80}")
    print("=" * 80)


def benchmark_sequential() -> float:
    """Benchmark 1: Sequential category list fetching."""
    print_header("Benchmark 1: Sequential (Baseline)")

    client = RustClient(timeout=30)
    start = time.time()
    all_apps = []
    completed = 0
    total = len(COUNTRIES) * len(CATEGORIES)

    for country in COUNTRIES:
        for category in CATEGORIES:
            try:
                apps = client.list(
                    collection=COLLECTION,
                    category=category,
                    country=country,
                    num=NUM_RESULTS,
                    lang="en",
                )
                all_apps.extend(apps)
                completed += 1
                elapsed = time.time() - start
                print(
                    f"  [{completed:2d}/{total}] {country.upper()}/{category:20s} - {len(apps):3d} apps | Time: {elapsed:.2f}s"
                )
            except Exception as e:
                print(f"  Error: {country}/{category}: {e}")

    elapsed = time.time() - start
    print(
        f"\n>> Collected {len(all_apps)} apps from {completed} requests in {elapsed:.2f}s"
    )
    print(f">> Average: {elapsed / completed:.3f}s per request")
    print(f">> Throughput: {len(all_apps) / elapsed:.2f} apps/second")
    return elapsed


def benchmark_batch_api() -> float:
    """Benchmark 2: Batch API for category lists."""
    print_header("Benchmark 2: Batch API (fetch_category_lists)")

    start = time.time()
    results = fetch_category_lists(
        countries=COUNTRIES,
        categories=CATEGORIES,
        collection=COLLECTION,
        num_results=NUM_RESULTS,
        lang="en",
    )
    elapsed = time.time() - start

    total_apps = sum(len(apps) for apps in results)

    for i, apps in enumerate(results, 1):
        country = COUNTRIES[(i - 1) // len(CATEGORIES)]
        category = CATEGORIES[(i - 1) % len(CATEGORIES)]
        print(
            f"  [{i:2d}/{len(results)}] {country.upper()}/{category:20s} - {len(apps):3d} apps"
        )

    print(
        f"\n>> Collected {total_apps} apps from {len(results)} requests in {elapsed:.2f}s"
    )
    print(f">> Average: {elapsed / len(results):.3f}s per request")
    print(f">> Throughput: {total_apps / elapsed:.2f} apps/second")
    return elapsed


def main() -> None:
    """Run all benchmarks."""
    print_header("BATCH CATEGORY LIST FETCHING BENCHMARK")
    print("\nConfiguration:")
    print(f"  Countries: {len(COUNTRIES)} ({', '.join(COUNTRIES)})")
    print(f"  Categories: {len(CATEGORIES)} ({', '.join(CATEGORIES)})")
    print(f"  Results per request: {NUM_RESULTS}")
    print(f"  Total requests: {len(COUNTRIES) * len(CATEGORIES)}")

    results = {}

    # Run benchmarks
    results["Sequential"] = benchmark_sequential()
    results["Batch API"] = benchmark_batch_api()

    # Summary
    print_header("SUMMARY")

    print(f"\n{'Method':<25} {'Time':>10} {'Speedup':>10}")
    print("-" * 50)

    baseline = results["Sequential"]
    sorted_results = sorted(results.items(), key=lambda x: x[1])

    for method, elapsed in sorted_results:
        speedup = baseline / elapsed
        print(f"{method:<25} {elapsed:>8.2f}s {speedup:>9.2f}x")

    fastest = sorted_results[0]
    print(f"\nFastest: {fastest[0]} ({fastest[1]:.2f}s)")
    print(f"Speedup vs Sequential: {baseline / fastest[1]:.2f}x")


if __name__ == "__main__":
    main()

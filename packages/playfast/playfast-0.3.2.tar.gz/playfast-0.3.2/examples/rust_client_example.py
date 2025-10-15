"""
Example: Using RustClient for maximum performance.

RustClient uses Rust for both HTTP requests and parsing,
achieving complete GIL-free parallel execution.

Performance: 30-40% faster than AsyncClient
Best for: Batch processing, periodic collection, high throughput
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from playfast import RustClient
from playfast.models import AppInfo


def example_basic():
    """Basic usage - single app"""
    print("=== Example 1: Basic Usage ===")

    client = RustClient(timeout=30)

    # Get app info (Rust HTTP + parsing, completely GIL-free)
    app = client.get_app('com.google.android.apps.maps', country='us')

    print(f"Title: {app.title}")
    print(f"Developer: {app.developer}")
    print(f"Score: {app.score} stars")
    print(f"Ratings: {app.ratings:,}")
    print(f"Is Free: {app.is_free}")
    print()


def example_parallel_batch():
    """Parallel batch processing with ThreadPoolExecutor"""
    print("=== Example 2: Parallel Batch Processing ===")

    client = RustClient(timeout=30)

    # List of apps to fetch
    app_ids = [
        'com.spotify.music',
        'com.netflix.mediaclient',
        'com.google.android.apps.maps',
        'com.facebook.katana',
        'com.instagram.android',
    ]

    # Parallel execution with ThreadPoolExecutor
    # Since Rust releases GIL, these truly execute in parallel!
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(client.get_app, app_id): app_id
            for app_id in app_ids
        }

        for future in as_completed(futures):
            app_id = futures[future]
            try:
                app = future.result()
                print(f"[OK] {app.title}")
                print(f"     {app.score} stars, {app.ratings:,} ratings")
            except Exception as e:
                print(f"[ERROR] {app_id}: {e}")

    print()


def example_multi_country():
    """Fetch same app from multiple countries in parallel"""
    print("=== Example 3: Multi-Country Parallel ===")

    client = RustClient(timeout=30)
    app_id = 'com.spotify.music'
    countries = ['us', 'kr', 'jp', 'de', 'fr', 'gb', 'br', 'in']

    def fetch_for_country(country: str) -> tuple[str, AppInfo | None]:
        try:
            app = client.get_app(app_id, country=country)
            return (country, app)
        except Exception:
            return (country, None)

    # Parallel execution
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(fetch_for_country, country)
            for country in countries
        ]

        results = [f.result() for f in futures]

    # Display results
    print(f"Fetched {app_id} from {len(countries)} countries:")
    for country, app in results:
        if app:
            print(f"  {country.upper()}: {app.score} stars")
        else:
            print(f"  {country.upper()}: Failed")

    print()


def example_reviews():
    """Get reviews"""
    print("=== Example 4: Get Reviews ===")

    client = RustClient(timeout=30)

    # Get first page of reviews
    reviews, next_token = client.get_reviews(
        'com.google.android.apps.maps',
        sort=1  # 1=newest, 2=highest, 3=most helpful
    )

    print(f"Got {len(reviews)} reviews")
    if reviews:
        print(f"\nFirst review:")
        print(f"  User: {reviews[0].user_name}")
        print(f"  Score: {reviews[0].score} stars")
        print(f"  Content: {reviews[0].content[:100]}...")

    if next_token:
        print(f"\nMore pages available (token: {next_token[:20]}...)")

    print()


def example_search():
    """Search for apps"""
    print("=== Example 5: Search ===")

    client = RustClient(timeout=30)

    # Search for music streaming apps
    results = client.search('music streaming', n_hits=10)

    print(f"Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result.title}")
        print(f"     by {result.developer}")
        if result.score:
            print(f"     {result.score} stars")

    print()


def example_massive_batch():
    """Process large number of apps efficiently"""
    print("=== Example 6: Massive Batch (100 apps) ===")

    import time

    client = RustClient(timeout=30)

    # Generate 100 app IDs (in real scenario, you'd have actual IDs)
    app_ids = [f'com.example.app{i}' for i in range(100)]

    start_time = time.time()

    # Process with high parallelism
    # Rust's GIL-free execution allows true parallel processing
    successful = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {
            executor.submit(client.get_app, app_id): app_id
            for app_id in app_ids
        }

        for future in as_completed(futures):
            try:
                _ = future.result()  # We only care about success/failure, not the app data
                successful += 1
            except Exception:
                failed += 1

    elapsed = time.time() - start_time

    print(f"Processed {len(app_ids)} apps in {elapsed:.2f} seconds")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Rate: {len(app_ids) / elapsed:.1f} apps/second")
    print()


if __name__ == '__main__':
    print("Playfast RustClient Examples")
    print("=" * 50)
    print()

    try:
        example_basic()
        example_parallel_batch()
        example_multi_country()
        example_reviews()
        example_search()
        # example_massive_batch()  # Uncomment to test

        print("=" * 50)
        print("All examples completed!")
        print("\nKey Takeaways:")
        print("  - RustClient releases GIL completely")
        print("  - True parallel execution with ThreadPoolExecutor")
        print("  - 30-40% faster than AsyncClient")
        print("  - Perfect for batch processing & periodic collection")

    except Exception as e:
        print(f"Error running examples: {e}")
        print("\nNote: These examples require actual network access")
        print("      and may fail if apps don't exist or parsing fails.")

"""Example 2: RustClient - Rust HTTP + Rust parsing (Maximum Performance)

RustClient is perfect for:
- Batch processing (1000s of apps)
- High-throughput scenarios
- True parallel execution (GIL-free)

Performance: 30-40% faster than AsyncClient
"""

from concurrent.futures import ThreadPoolExecutor, as_completed

from playfast import RustClient


def example_single_app():
    """Fetch a single app."""
    print("=== Example 1: Single App ===\n")

    client = RustClient(timeout=30)
    app = client.get_app("com.spotify.music")

    print(f"📱 {app.title}")
    print(f"👨‍💻 Developer: {app.developer}")
    print(f"⭐ Rating: {app.score} ({app.ratings:,} ratings)")
    print(f"💰 Price: ${app.price}")
    print(f"✅ Free: {app.is_free}")


def example_parallel_batch():
    """Fetch multiple apps in parallel using ThreadPoolExecutor."""
    print("\n=== Example 2: Parallel Batch (True GIL-free) ===\n")

    client = RustClient(timeout=30)

    app_ids = [
        "com.spotify.music",
        "com.netflix.mediaclient",
        "com.instagram.android",
        "com.facebook.katana",
        "com.google.android.youtube",
    ]

    # ThreadPoolExecutor + Rust = True parallel execution!
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(client.get_app, app_id): app_id
            for app_id in app_ids
        }

        for future in as_completed(futures):
            app_id = futures[future]
            try:
                app = future.result()
                print(f"✓ {app.title} - {app.score}⭐")
            except Exception as e:
                print(f"✗ {app_id}: {e}")


def example_multi_country():
    """Fetch same app from multiple countries in parallel."""
    print("\n=== Example 3: Multi-Country Parallel ===\n")

    client = RustClient(timeout=30)
    app_id = "com.spotify.music"
    countries = ["us", "kr", "jp", "de", "fr", "gb"]

    def fetch_for_country(country: str):
        return country, client.get_app(app_id, country=country)

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(fetch_for_country, country)
            for country in countries
        ]

        results = [f.result() for f in futures]

    print(f"Spotify ratings across countries:")
    for country, app in results:
        print(f"  {country.upper()}: {app.score}⭐ ({app.ratings:,} ratings)")


def example_reviews():
    """Fetch app reviews."""
    print("\n=== Example 4: Reviews ===\n")

    client = RustClient(timeout=30)

    reviews, next_token = client.get_reviews(
        "com.google.android.apps.maps",
        sort=1,  # 1=newest, 2=highest, 3=most helpful
    )

    print(f"Got {len(reviews)} reviews")
    if reviews:
        print(f"\nFirst review:")
        print(f"  User: {reviews[0].user_name}")
        print(f"  Score: {reviews[0].score}⭐")
        print(f"  Content: {reviews[0].content[:100]}...")


def example_search():
    """Search for apps."""
    print("\n=== Example 5: Search ===\n")

    client = RustClient(timeout=30)
    results = client.search("music streaming", n_hits=5)

    print("Top 5 music streaming apps:")
    for i, result in enumerate(results, 1):
        score_text = f"{result.score}⭐" if result.score else "N/A"
        print(f"  {i}. {result.title} - {score_text}")


def main():
    """Run all examples."""
    print("=" * 60)
    print("RustClient Examples (Maximum Performance)")
    print("=" * 60)

    example_single_app()
    example_parallel_batch()
    example_multi_country()
    example_reviews()
    example_search()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("\nKey Takeaways:")
    print("  ✓ RustClient releases GIL completely")
    print("  ✓ True parallel execution with ThreadPoolExecutor")
    print("  ✓ 30-40% faster than AsyncClient")
    print("  ✓ Perfect for batch processing")
    print("=" * 60)


if __name__ == "__main__":
    main()

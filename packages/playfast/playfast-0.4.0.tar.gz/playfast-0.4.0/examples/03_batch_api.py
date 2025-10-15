"""Example 3: High-Level Batch API

The batch API provides the easiest way to fetch multiple items in parallel:
- fetch_apps() - Multiple apps across countries
- fetch_category_lists() - Top apps by category
- search_apps() - Search queries across countries
- fetch_reviews() - Reviews for multiple apps

Performance: 5-10x faster than sequential processing
"""

import time

from playfast import (
    fetch_apps,
    fetch_category_lists,
    fetch_multi_country_apps,
    fetch_reviews,
    search_apps,
)


def example_fetch_apps():
    """Fetch multiple apps across multiple countries."""
    print("=== Example 1: Fetch Apps (Multi-Country) ===\n")

    app_ids = [
        "com.spotify.music",
        "com.netflix.mediaclient",
        "com.instagram.android",
    ]
    countries = ["us", "kr", "jp"]

    print(f"Fetching {len(app_ids)} apps from {len(countries)} countries...")
    start = time.time()

    apps = fetch_apps(
        app_ids=app_ids,
        countries=countries,
        lang="en",
    )

    elapsed = time.time() - start

    print(f"\nGot {len(apps)} apps in {elapsed:.2f}s")
    print("\nSample results:")
    for app in apps[:5]:
        print(f"  {app.title} - {app.score}⭐")


def example_fetch_category_lists():
    """Fetch top apps by category from multiple countries."""
    print("\n=== Example 2: Fetch Category Lists ===\n")

    countries = ["us", "kr"]
    categories = ["GAME_ACTION", "SOCIAL"]

    print(f"Fetching top apps for {len(categories)} categories from {len(countries)} countries...")
    start = time.time()

    results = fetch_category_lists(
        countries=countries,
        categories=categories,
        collection="topselling_free",
        num_results=20,
        lang="en",
    )

    elapsed = time.time() - start

    total_apps = sum(len(apps) for apps in results)
    print(f"\nGot {total_apps} apps in {elapsed:.2f}s")

    print("\nTop 3 from each category:")
    idx = 0
    for country in countries:
        for category in categories:
            apps = results[idx]
            print(f"\n{country.upper()} - {category}:")
            for i, app in enumerate(apps[:3], 1):
                print(f"  {i}. {app.title} - {app.score}⭐")
            idx += 1


def example_multi_country_apps():
    """Fetch same app from multiple countries (convenience function)."""
    print("\n=== Example 3: Multi-Country Apps ===\n")

    app_id = "com.spotify.music"
    countries = ["us", "kr", "jp", "de"]

    print(f"Fetching {app_id} from {len(countries)} countries...")
    start = time.time()

    apps_by_country = fetch_multi_country_apps(
        app_id=app_id,
        countries=countries,
        lang="en",
    )

    elapsed = time.time() - start

    print(f"\nCompleted in {elapsed:.2f}s")
    print("\nSpotify ratings across countries:")
    for country, app in apps_by_country.items():
        print(f"  {country.upper()}: {app.score}⭐ ({app.ratings:,} ratings)")


def example_search_apps():
    """Search for apps across multiple countries."""
    print("\n=== Example 4: Search Apps ===\n")

    queries = ["music streaming", "video chat"]
    countries = ["us", "kr"]

    print(f"Searching for {len(queries)} queries in {len(countries)} countries...")
    start = time.time()

    results = search_apps(
        queries=queries,
        countries=countries,
        lang="en",
    )

    elapsed = time.time() - start

    total_apps = sum(len(apps) for apps in results)
    print(f"\nGot {total_apps} results in {elapsed:.2f}s")

    print("\nTop 3 results per query:")
    idx = 0
    for query in queries:
        for country in countries:
            apps = results[idx]
            print(f"\n'{query}' in {country.upper()}:")
            for i, app in enumerate(apps[:3], 1):
                print(f"  {i}. {app.title}")
            idx += 1


def example_fetch_reviews():
    """Fetch reviews for multiple apps across countries."""
    print("\n=== Example 5: Fetch Reviews ===\n")

    app_ids = ["com.spotify.music", "com.netflix.mediaclient"]
    countries = ["us", "kr"]

    print(f"Fetching reviews for {len(app_ids)} apps from {len(countries)} countries...")
    start = time.time()

    results = fetch_reviews(
        app_ids=app_ids,
        countries=countries,
        lang="en",
        sort=1,  # 1=newest, 2=highest, 3=most helpful
    )

    elapsed = time.time() - start

    total_reviews = sum(len(reviews) for reviews, _ in results)
    print(f"\nGot {total_reviews} reviews in {elapsed:.2f}s")

    print("\nSample reviews:")
    for i, (reviews, next_token) in enumerate(results[:2], 1):
        if reviews:
            review = reviews[0]
            print(f"\n{i}. {review.user_name}: {review.score}⭐")
            print(f"   {review.content[:80]}...")


def main():
    """Run all examples."""
    print("=" * 60)
    print("High-Level Batch API Examples")
    print("=" * 60)

    example_fetch_apps()
    example_fetch_category_lists()
    example_multi_country_apps()
    example_search_apps()
    example_fetch_reviews()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("\nKey Takeaways:")
    print("  ✓ Batch API is the easiest way to fetch multiple items")
    print("  ✓ 5-10x faster than sequential processing")
    print("  ✓ Handles parallelization automatically")
    print("  ✓ Clean, simple interface")
    print("=" * 60)


if __name__ == "__main__":
    main()

"""Example 1: AsyncClient - Python async HTTP + Rust parsing

AsyncClient is perfect for:
- Easy async/await syntax
- I/O-bound workloads
- Integration with existing async code

Features:
- Natural async/await interface
- Automatic connection pooling
- Context manager support
"""

import asyncio

from playfast import AsyncClient


async def example_single_app():
    """Fetch a single app."""
    print("=== Example 1: Single App ===\n")

    async with AsyncClient() as client:
        app = await client.get_app("com.spotify.music")

        print(f"📱 {app.title}")
        print(f"👨‍💻 Developer: {app.developer}")
        print(f"⭐ Rating: {app.score} ({app.ratings:,} ratings)")
        print(f"💰 Price: ${app.price}")
        print(f"✅ Free: {app.is_free}")


async def example_multiple_apps():
    """Fetch multiple apps concurrently."""
    print("\n=== Example 2: Multiple Apps (Concurrent) ===\n")

    app_ids = [
        "com.spotify.music",
        "com.netflix.mediaclient",
        "com.instagram.android",
    ]

    async with AsyncClient(max_concurrent=10) as client:
        # Create tasks for all apps
        tasks = [client.get_app(app_id) for app_id in app_ids]

        # Execute concurrently
        apps = await asyncio.gather(*tasks)

        for app in apps:
            print(f"✓ {app.title} - {app.score}⭐")


async def example_multi_country():
    """Fetch same app from multiple countries."""
    print("\n=== Example 3: Multi-Country ===\n")

    app_id = "com.spotify.music"
    countries = ["us", "kr", "jp", "de"]

    async with AsyncClient() as client:
        tasks = [
            client.get_app(app_id, country=country)
            for country in countries
        ]

        apps = await asyncio.gather(*tasks)

        print(f"Spotify ratings across countries:")
        for country, app in zip(countries, apps):
            print(f"  {country.upper()}: {app.score}⭐ ({app.ratings:,} ratings)")


async def example_reviews():
    """Fetch app reviews."""
    print("\n=== Example 4: Reviews ===\n")

    async with AsyncClient() as client:
        reviews, next_token = await client.get_reviews(
            "com.google.android.apps.maps",
            sort=1,  # 1=newest, 2=highest, 3=most helpful
        )

        print(f"Got {len(reviews)} reviews")
        if reviews:
            print(f"\nFirst review:")
            print(f"  User: {reviews[0].user_name}")
            print(f"  Score: {reviews[0].score}⭐")
            print(f"  Content: {reviews[0].content[:100]}...")


async def example_search():
    """Search for apps."""
    print("\n=== Example 5: Search ===\n")

    async with AsyncClient() as client:
        results = await client.search("music streaming", n_hits=5)

        print("Top 5 music streaming apps:")
        for i, result in enumerate(results, 1):
            score_text = f"{result.score}⭐" if result.score else "N/A"
            print(f"  {i}. {result.title} - {score_text}")


async def main():
    """Run all examples."""
    print("=" * 60)
    print("AsyncClient Examples")
    print("=" * 60)

    await example_single_app()
    await example_multiple_apps()
    await example_multi_country()
    await example_reviews()
    await example_search()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

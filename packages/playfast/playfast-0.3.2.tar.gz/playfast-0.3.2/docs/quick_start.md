# Quick Start

Jump right in with these practical examples.

## Basic App Information

```python
import asyncio
from playfast import AsyncClient


async def get_app_info():
    """Get basic information about an app."""
    async with AsyncClient() as client:
        app = await client.get_app("com.spotify.music")

        print(f"Title: {app.title}")
        print(f"Developer: {app.developer}")
        print(f"Score: {app.score}⭐")
        print(f"Ratings: {app.ratings:,}")
        print(f"Price: ${app.price}")
        print(f"Category: {app.category}")
        print(f"Version: {app.version}")
        print(f"Installs: {app.installs}")


asyncio.run(get_app_info())
```

## Multiple Apps in Parallel

```python
import asyncio
from playfast import AsyncClient


async def get_multiple_apps():
    """Fetch multiple apps concurrently."""
    app_ids = [
        "com.spotify.music",
        "com.netflix.mediaclient",
        "com.instagram.android",
        "com.whatsapp",
    ]

    async with AsyncClient(max_concurrent=10) as client:
        # Parallel fetch
        results = await client.get_apps_parallel(app_ids)

        for country, apps in results.items():
            print(f"\n{country.upper()}:")
            for app in apps:
                if app:
                    print(f"  {app.title}: {app.score}⭐")


asyncio.run(get_multiple_apps())
```

## Streaming Reviews

```python
import asyncio
from playfast import AsyncClient


async def analyze_reviews():
    """Stream and analyze reviews."""
    async with AsyncClient() as client:
        positive = 0
        negative = 0
        total = 0

        async for review in client.stream_reviews("com.spotify.music"):
            total += 1

            if review.score >= 4:
                positive += 1
            else:
                negative += 1

            # Print progress every 100 reviews
            if total % 100 == 0:
                print(f"Processed {total} reviews...")
                print(f"  Positive: {positive} ({positive/total*100:.1f}%)")
                print(f"  Negative: {negative} ({negative/total*100:.1f}%)")

            # Limit for demo purposes
            if total >= 500:
                break

        print(f"\nFinal Results:")
        print(f"  Total: {total}")
        print(f"  Positive: {positive} ({positive/total*100:.1f}%)")
        print(f"  Negative: {negative} ({negative/total*100:.1f}%)")


asyncio.run(analyze_reviews())
```

## Multi-Country Analysis

```python
import asyncio
from playfast import AsyncClient


async def multi_country_comparison():
    """Compare app ratings across countries."""
    app_id = "com.spotify.music"
    countries = ["us", "kr", "jp", "de", "fr", "gb", "br", "in"]

    async with AsyncClient(max_concurrent=20) as client:
        results = await client.get_apps_parallel(app_ids=[app_id], countries=countries)

        print(f"Ratings for {app_id} across countries:\n")

        for country, apps in results.items():
            if apps and apps[0]:
                app = apps[0]
                print(f"{country.upper():4s}: {app.score}⭐ ({app.ratings:,} ratings)")


asyncio.run(multi_country_comparison())
```

## Search Apps

```python
import asyncio
from playfast import AsyncClient


async def search_apps():
    """Search for apps."""
    async with AsyncClient() as client:
        results = await client.search(query="music streaming", n_hits=20)

        print(f"Found {len(results)} apps:\n")

        for i, result in enumerate(results, 1):
            print(f"{i}. {result.title}")
            print(f"   Developer: {result.developer}")
            print(f"   Score: {result.score}⭐")
            print(f"   Price: ${result.price}")
            print()


asyncio.run(search_apps())
```

## Batch Processing

```python
import asyncio
from playfast import AsyncClient


async def batch_collect():
    """Collect data in batches."""
    # Simulate a large list of app IDs
    all_app_ids = [f"com.app{i}" for i in range(100)]
    batch_size = 20

    async with AsyncClient(max_concurrent=30) as client:
        for i in range(0, len(all_app_ids), batch_size):
            batch = all_app_ids[i : i + batch_size]

            print(f"Processing batch {i//batch_size + 1} ({i+1}-{i+len(batch)})...")

            results = await client.get_apps_parallel(batch)

            # Process results (e.g., save to database)
            # await save_to_database(results)

            print(f"  Completed: {len(batch)} apps")


asyncio.run(batch_collect())
```

## Error Handling

```python
import asyncio
from playfast import AsyncClient
from playfast.exceptions import (
    AppNotFoundError,
    RateLimitError,
    ParseError,
)


async def robust_fetch():
    """Fetch app with proper error handling."""
    async with AsyncClient() as client:
        try:
            app = await client.get_app("com.invalid.app.id")
            print(f"Found: {app.title}")

        except AppNotFoundError:
            print("App not found on the Play Store")

        except RateLimitError as e:
            print(f"Rate limited! Retry after {e.retry_after} seconds")
            await asyncio.sleep(e.retry_after)

        except ParseError as e:
            print(f"Failed to parse response: {e}")

        except Exception as e:
            print(f"Unexpected error: {e}")


asyncio.run(robust_fetch())
```

## Custom Configuration

```python
import asyncio
from playfast import AsyncClient


async def custom_config():
    """Use custom client configuration."""
    async with AsyncClient(
        max_concurrent=50,  # Increase parallelism
        timeout=60,  # Increase timeout
        headers={  # Custom headers
            "User-Agent": "MyBot/1.0",
        },
    ) as client:
        app = await client.get_app(
            "com.spotify.music",
            lang="ko",  # Korean language
            country="kr",  # South Korea
        )

        print(f"Title: {app.title}")
        print(f"Developer: {app.developer}")


asyncio.run(custom_config())
```

## Next Steps

- [User Guide](guides/overview.md) - Comprehensive documentation
- [API Reference](api/client.md) - Detailed API docs
- [Examples](examples/basic.md) - More examples
- [Performance Tips](guides/performance.md) - Optimization guide

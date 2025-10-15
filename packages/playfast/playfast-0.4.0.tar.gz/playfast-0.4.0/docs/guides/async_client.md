# Async Client Guide

Understanding Playfast's async architecture.

## Why Async?

Playfast uses async/await for:

1. **Concurrent I/O**: Multiple network requests simultaneously
1. **Efficient Resource Usage**: Don't block on I/O
1. **Scalability**: Handle hundreds of concurrent operations

## Basic Async Pattern

```python
import asyncio
from playfast import AsyncClient


async def main():
    async with AsyncClient() as client:
        app = await client.get_app("com.spotify.music")
        print(app.title)


asyncio.run(main())
```

## Concurrent Operations

```python
import asyncio


async def fetch_multiple():
    async with AsyncClient() as client:
        # Sequential (slow)
        app1 = await client.get_app("app1")
        app2 = await client.get_app("app2")

        # Concurrent (fast)
        app1, app2 = await asyncio.gather(
            client.get_app("app1"), client.get_app("app2")
        )

        # Or use the built-in parallel method (fastest)
        results = await client.get_apps_parallel(["app1", "app2"])
```

## Streaming

```python
async def process_reviews():
    async with AsyncClient() as client:
        async for review in client.stream_reviews("com.spotify.music"):
            process(review)
```

Learn more in the [API Reference](../api/client.md).

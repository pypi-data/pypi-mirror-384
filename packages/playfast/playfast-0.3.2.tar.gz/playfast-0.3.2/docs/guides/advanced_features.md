# Advanced Features

Advanced techniques for power users.

## Custom HTTP Headers

```python
async with AsyncClient(
    headers={
        "User-Agent": "MyBot/1.0",
        "Accept-Language": "en-US,en;q=0.9",
    }
) as client:
    pass
```

## Rate Limiting

Implement custom rate limiting:

```python
import asyncio
from playfast import AsyncClient


class RateLimitedClient:
    def __init__(self, requests_per_second=10):
        self.client = AsyncClient()
        self.semaphore = asyncio.Semaphore(requests_per_second)
        self.delay = 1.0 / requests_per_second

    async def get_app(self, app_id):
        async with self.semaphore:
            result = await self.client.get_app(app_id)
            await asyncio.sleep(self.delay)
            return result
```

## Proxy Support

```python
async with AsyncClient(proxy="http://proxy.example.com:8080") as client:
    pass
```

See more in the [API Reference](../api/client.md).

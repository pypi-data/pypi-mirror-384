# Error Handling

Handle errors gracefully in Playfast.

## Exception Hierarchy

```python
from playfast.exceptions import (
    PlayfastError,  # Base exception
    AppNotFoundError,  # App doesn't exist
    RateLimitError,  # Rate limited
    ParseError,  # Failed to parse response
    NetworkError,  # Network issues
)
```

## Basic Error Handling

```python
try:
    app = await client.get_app("invalid.app.id")
except AppNotFoundError:
    print("App not found")
except RateLimitError as e:
    print(f"Rate limited, retry after {e.retry_after}s")
except PlayfastError as e:
    print(f"Error: {e}")
```

## Retry Logic

```python
import asyncio


async def fetch_with_retry(client, app_id, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await client.get_app(app_id)
        except RateLimitError as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(e.retry_after)
            else:
                raise
        except NetworkError:
            if attempt < max_retries - 1:
                await asyncio.sleep(2**attempt)  # Exponential backoff
            else:
                raise
```

See [Exceptions API](../api/exceptions.md) for all exception types.

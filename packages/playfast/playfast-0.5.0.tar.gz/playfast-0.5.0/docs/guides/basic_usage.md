# Basic Usage

Learn the fundamental patterns for using Playfast.

## Client Initialization

Always use the `AsyncClient` as a context manager:

```python
from playfast import AsyncClient

async with AsyncClient() as client:
    # Your code here
    pass
```

## Fetching App Information

```python
app = await client.get_app("com.spotify.music")

print(app.title)  # App name
print(app.developer)  # Developer name
print(app.score)  # Rating (1-5)
print(app.ratings)  # Number of ratings
print(app.price)  # Price (0.0 for free)
print(app.is_free)  # Boolean
```

## Multi-Language and Multi-Country

```python
# Korean app page from South Korea
app_kr = await client.get_app("com.spotify.music", lang="ko", country="kr")

# English app page from US
app_us = await client.get_app("com.spotify.music", lang="en", country="us")
```

See [API Reference](../api/client.md) for all available options.

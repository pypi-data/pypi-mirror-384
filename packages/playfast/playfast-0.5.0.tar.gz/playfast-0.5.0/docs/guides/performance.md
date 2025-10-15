# Performance Tips

Optimize your Playfast usage for maximum performance.

## 1. Use Parallel Methods

```python
# ❌ Slow
for app_id in app_ids:
    app = await client.get_app(app_id)

# ✅ Fast
results = await client.get_apps_parallel(app_ids)
```

## 2. Increase Concurrency

```python
async with AsyncClient(max_concurrent=50) as client:
    # Up to 50 concurrent requests
    pass
```

## 3. Enable Free-Threading

```bash
uv python install 3.14t
uv python pin 3.14t
```

## 4. Batch Processing

```python
# Process in chunks
for chunk in chunks(app_ids, 100):
    results = await client.get_apps_parallel(chunk)
    await save_to_db(results)
```

## 5. Stream Large Datasets

```python
# Memory-efficient
async for review in client.stream_reviews("app_id"):
    process(review)
```

See [Architecture](../development/architecture.md) for more details.

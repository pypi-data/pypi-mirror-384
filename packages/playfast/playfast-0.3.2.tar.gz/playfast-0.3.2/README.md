# Playfast ⚡

> Lightning-Fast Google Play Store Scraper

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Built with Rust](https://img.shields.io/badge/built%20with-Rust-orange.svg)](https://www.rust-lang.org/)
[![CI](https://github.com/mixL1nk/playfast/actions/workflows/ci.yml/badge.svg)](https://github.com/mixL1nk/playfast/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/mixL1nk/6a5cda65b343fffe18719b3a9d6d6a3b/raw/playfast-coverage.json)](https://github.com/mixL1nk/playfast/actions/workflows/ci.yml)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue)](https://mixL1nk.github.io/playfast/)

Playfast is a high-performance Google Play Store scraper built with **Rust + PyO3**, delivering **5-10x faster performance** with true parallel batch processing.

## ✨ Features

- 🚀 **Blazingly Fast**: Batch API is 5-10x faster than sequential
- ⚡ **True Parallel**: Rust core completely releases GIL
- 🦀 **Pure Rust**: HTTP + parsing all in Rust for maximum performance
- 🔒 **Type Safe**: Full Pydantic validation and type hints
- 💾 **Memory Efficient**: Only 1.5 KB per app, linear scaling
- 🌍 **Multi-Country**: 247 countries, 93 unique Play Stores
- 📦 **Batch API**: High-level functions for easy parallel processing

## 📊 Performance

**Batch Processing** makes bulk operations **5-10x faster** through true Rust parallelism!

| Method                   | Time    | Speedup     |
| ------------------------ | ------- | ----------- |
| **Batch API**            | **~3s** | **6-8x** 🚀 |
| RustClient + ThreadPool  | ~3-4s   | 6-7x        |
| AsyncClient (concurrent) | ~3-5s   | 5-7x        |
| Sequential               | ~20-30s | 1x          |

*Benchmark: Fetching 3 apps across 3 countries (9 requests total)*

## 🚀 Quick Start

### Installation

```bash
pip install playfast
```

### Option 1: Batch API (Recommended - Easiest & Fastest)

```python
from playfast import fetch_apps

# Fetch multiple apps across countries (parallel!)
apps = fetch_apps(
    app_ids=["com.spotify.music", "com.netflix.mediaclient"],
    countries=["us", "kr", "jp"],
)
print(f"Fetched {len(apps)} apps in ~3 seconds!")
```

### Option 2: RustClient (Maximum Performance)

```python
from playfast import RustClient

client = RustClient()

# Get app information (GIL-free!)
app = client.get_app("com.spotify.music")
print(f"{app.title}: {app.score}⭐ ({app.ratings:,} ratings)")

# Get reviews
reviews, next_token = client.get_reviews("com.spotify.music")
for review in reviews[:5]:
    print(f"{review.user_name}: {review.score}⭐")
```

### Option 3: AsyncClient (Easy Async)

```python
import asyncio
from playfast import AsyncClient


async def main():
    async with AsyncClient() as client:
        app = await client.get_app("com.spotify.music")
        print(f"{app.title}: {app.score}⭐")


asyncio.run(main())
```

## 📚 Examples

See the [`examples/`](examples/) directory for more:

- [`01_async_client.py`](examples/01_async_client.py) - AsyncClient basics
- [`02_rust_client.py`](examples/02_rust_client.py) - RustClient for max performance
- [`03_batch_api.py`](examples/03_batch_api.py) - High-level batch API
- [`04_countries_and_categories.py`](examples/04_countries_and_categories.py) - Country optimization

## 📖 Documentation

- **[Getting Started](docs/getting_started.md)** - Installation and first steps
- **[Quick Start](docs/quick_start.md)** - Practical examples
- **[API Reference](docs/api/)** - Complete API documentation
- **[Batch API Guide](docs/BATCH_API.md)** - Batch processing guide

## 🏗️ Architecture

Playfast uses **pure Rust** for both HTTP and parsing:

```bash
┌─────────────────────────────────────┐
│   Python Layer                      │
│   - Batch API (high-level)          │
│   - RustClient / AsyncClient        │
│   - Pydantic Models                 │
└──────────────┬──────────────────────┘
               │ PyO3 Bindings
               ▼
┌─────────────────────────────────────┐
│   Rust Core                         │
│   - HTTP Client (reqwest)           │
│   - HTML Parser (scraper)           │
│   - Parallel Processing (rayon)     │
│   - Complete GIL Release            │
└─────────────────────────────────────┘
```

### Three Client Options

| Method          | Speed  | Ease   | Best For       |
| --------------- | ------ | ------ | -------------- |
| **Batch API**   | ⚡⚡⚡ | ⭐⭐⭐ | Multiple items |
| **RustClient**  | ⚡⚡⚡ | ⭐⭐   | Single items   |
| **AsyncClient** | ⚡⚡   | ⭐⭐   | Async code     |

## 🌍 Multi-Country Optimization

Playfast optimizes global data collection:

```python
from playfast import get_unique_countries, get_representative_country

# Instead of 247 countries, use 93 unique stores (2.7x faster!)
unique = get_unique_countries()  # 93 unique Play Stores

# Get representative for any country
rep = get_representative_country(
    "fi"
)  # Finland → Vanuatu store (shared by 138 countries)
```

## 🔧 Development

```bash
# Clone repository
git clone https://github.com/mixL1nk/playfast.git
cd playfast

# Install dependencies
uv sync

# Build Rust extension
uv run maturin develop --release

# Run tests
uv run pytest

# Run examples
uv run python examples/basic.py

# Run benchmarks
uv run python benchmarks/batch_apps_benchmark.py
```

See [Development Setup](docs/development/setup.md) for detailed instructions.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
1. Create a feature branch
1. Make your changes
1. Add tests
1. Submit a pull request

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Built with [PyO3](https://github.com/PyO3/pyo3) (Rust-Python bindings)
- Inspired by [google-play-scraper](https://github.com/facundoolano/google-play-scraper)
- HTTP: [reqwest](https://github.com/seanmonstar/reqwest)
- Parsing: [scraper](https://github.com/causal-agent/scraper)

## ⚠️ Disclaimer

This tool is for educational and research purposes only. Please respect Google Play Store's Terms of Service. Use responsibly with appropriate rate limiting.

______________________________________________________________________

**Made with ❤️ using Rust + Python**

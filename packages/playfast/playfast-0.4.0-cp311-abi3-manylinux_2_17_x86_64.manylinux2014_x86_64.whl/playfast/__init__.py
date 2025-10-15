"""Playfast - Lightning-fast Google Play Store scraper.

High-performance scraping powered by Rust + Python:
- Rust core for HTTP + parsing (completely GIL-free)
- Python asyncio for easy async programming
- Pydantic for validation and type safety

Two client options:
1. RustClient - Rust HTTP + parsing (maximum performance, 30-40% faster)
2. AsyncClient - Python async HTTP + Rust parsing (easier to use)

Quick Start (RustClient - Recommended for performance):
    >>> from playfast import RustClient
    >>>
    >>> client = RustClient()
    >>> app = client.get_app("com.spotify.music")
    >>> print(f"{app.title}: {app.score}⭐")

Quick Start (AsyncClient):
    >>> import asyncio
    >>> from playfast import AsyncClient
    >>>
    >>> async def main():
    ...     async with AsyncClient() as client:
    ...         app = await client.get_app("com.spotify.music")
    ...         print(f"{app.title}: {app.score}⭐")
    >>>
    >>> asyncio.run(main())
"""

__version__ = "0.1.0"
__author__ = "Taeyun Jang"
__license__ = "MIT"

# High-level API
# Low-level Rust API (advanced users)
from playfast import core

# High-level batch API (recommended)
from playfast.batch import (
    BatchFetcher,
    fetch_apps,
    fetch_category_lists,
    fetch_multi_country_apps,
    fetch_reviews,
    fetch_top_apps,
    search_apps,
)

# Low-level batch utilities (advanced users)
from playfast.batch_builder import (
    BatchRequestBuilder,
    build_app_country_matrix,
    build_multi_country_requests,
)
from playfast.client import AsyncClient

# Constants
from playfast.constants import (
    REGION_MAPPING,
    UNIQUE_REGION_CODES,
    Age,
    Category,
    Collection,
    Country,
    get_countries,
    get_countries_in_region,
    get_country_by_code,
    get_representative_country,
    get_unique_countries,
    is_unique_region,
)

# Exceptions
from playfast.exceptions import (
    AppNotFoundError,
    NetworkError,
    ParseError,
    PlayfastError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)

# Pydantic models
from playfast.models import AppInfo, Permission, Review, SearchResult
from playfast.rust_client import RustClient, quick_get_app


__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__license__",
    # High-level API
    "AsyncClient",
    "RustClient",
    "quick_get_app",
    # Models
    "AppInfo",
    "Review",
    "SearchResult",
    "Permission",
    # Constants - Enums
    "Category",
    "Collection",
    "Age",
    "Country",
    # Constants - All countries
    "get_countries",
    "get_country_by_code",
    # Constants - Unique regions (optimized)
    "get_unique_countries",
    "get_representative_country",
    "is_unique_region",
    "get_countries_in_region",
    "UNIQUE_REGION_CODES",
    "REGION_MAPPING",
    # Exceptions
    "PlayfastError",
    "AppNotFoundError",
    "RateLimitError",
    "ParseError",
    "NetworkError",
    "ValidationError",
    "TimeoutError",
    # High-level batch API
    "fetch_apps",
    "fetch_category_lists",
    "search_apps",
    "fetch_reviews",
    "fetch_top_apps",
    "fetch_multi_country_apps",
    "BatchFetcher",
    # Low-level batch utilities
    "BatchRequestBuilder",
    "build_multi_country_requests",
    "build_app_country_matrix",
    # Low-level API (advanced)
    "core",
]


def main() -> None:
    """CLI entry point (placeholder)."""
    print("Playfast v0.1.0 - Lightning-fast Google Play Store scraper")
    print("Two client options:")
    print("  - RustClient: Maximum performance (Rust HTTP + parsing)")
    print("  - AsyncClient: Easy async (Python HTTP + Rust parsing)")
    print("See documentation at: https://github.com/mixL1nk/playfast")

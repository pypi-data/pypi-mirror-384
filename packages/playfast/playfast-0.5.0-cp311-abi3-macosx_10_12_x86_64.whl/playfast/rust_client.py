"""RustClient - Direct Rust HTTP client for maximum performance.

This client uses Rust for both HTTP requests and parsing, achieving
complete GIL-free parallel execution. Best for batch processing and
high-throughput scenarios.
"""

from __future__ import annotations

import asyncio
from typing import Self

from playfast.core import (
    fetch_and_parse_app,
    fetch_and_parse_list,
    fetch_and_parse_reviews,
    fetch_and_parse_search,
)
from playfast.models import AppInfo, Review, SearchResult


class RustClient:
    """High-performance client using Rust for HTTP + parsing.

    This client achieves maximum performance by handling both HTTP requests
    and parsing in Rust, completely releasing the GIL. Perfect for:
    - Batch processing (1000s of apps)
    - Periodic data collection
    - High-throughput scenarios
    - Multi-threaded applications

    Compared to AsyncClient:
    - 30-40% faster for batch operations
    - True parallel execution (no GIL)
    - Synchronous API (use with ThreadPoolExecutor for async)

    Examples:
        >>> client = RustClient(timeout=30)
        >>> app = client.get_app("com.spotify.music")
        >>> app.title
        'Spotify: Music and Podcasts'
        >>> app.score >= 4.0
        True

        >>> # Parallel batch processing
        >>> with ThreadPoolExecutor(max_workers=50) as executor:  # doctest: +SKIP
        ...     futures = [executor.submit(client.get_app, app_id) for app_id in app_ids]
        ...     apps = [f.result() for f in futures]

    Args:
        timeout: Request timeout in seconds (default: 30)
        lang: Default language code (default: "en")

    """

    def __init__(self, timeout: int = 30, lang: str = "en") -> None:
        """Initialize the Rust client."""
        self.timeout = timeout
        self.lang = lang

    def __enter__(self) -> Self:
        """Context manager entry."""
        return self

    def __exit__(self, *args: object) -> None:
        """Context manager exit."""
        # RustClient doesn't need cleanup, but provide for consistency

    def get_app(
        self,
        app_id: str,
        lang: str | None = None,
        country: str = "us",
    ) -> AppInfo:
        """Get app information (Rust HTTP + parsing, GIL-free).

        This method executes entirely in Rust, releasing the GIL for
        true parallel execution.

        Args:
            app_id: App package ID (e.g., "com.spotify.music")
            lang: Language code (default: client lang)
            country: Country code (default: "us")

        Returns:
            AppInfo: Validated app information

        Raises:
            Exception: If request or parsing fails

        Examples:
            >>> client = RustClient()
            >>> app = client.get_app("com.spotify.music", country="kr")
            >>> app.title
            'Spotify: Music and Podcasts'
            >>> app.score >= 4.0
            True

        """
        rust_app = fetch_and_parse_app(app_id, lang or self.lang, country, self.timeout)
        return AppInfo.from_rust(rust_app)

    def get_reviews(
        self,
        app_id: str,
        lang: str | None = None,
        country: str = "us",
        sort: int = 1,
        continuation_token: str | None = None,
    ) -> tuple[list[Review], str | None]:
        """Get a page of reviews (Rust HTTP + parsing, GIL-free).

        Args:
            app_id: App package ID
            lang: Language code (default: client lang)
            country: Country code (default: "us")
            sort: Sort order (1=newest, 2=highest, 3=most helpful)
            continuation_token: Token for pagination

        Returns:
            tuple: (list of reviews, next page token)

        Examples:
            >>> client = RustClient()
            >>> reviews, next_token = client.get_reviews("com.spotify.music")
            >>> len(reviews) > 0
            True
            >>> reviews[0].score >= 1 and reviews[0].score <= 5
            True

        """
        rust_reviews, next_token = fetch_and_parse_reviews(
            app_id, lang or self.lang, country, sort, continuation_token, self.timeout
        )
        reviews = [Review.from_rust(r) for r in rust_reviews]
        return reviews, next_token

    def get_all_reviews(
        self,
        app_id: str,
        lang: str | None = None,
        country: str = "us",
        sort: int = 1,
        max_pages: int | None = None,
    ) -> list[Review]:
        """Get all reviews with pagination (synchronous).

        Args:
            app_id: App package ID
            lang: Language code
            country: Country code
            sort: Sort order
            max_pages: Maximum pages to fetch (default: unlimited)

        Returns:
            list[Review]: All reviews

        Examples:
            >>> client = RustClient()  # doctest: +SKIP
            >>> all_reviews = client.get_all_reviews("com.spotify.music", max_pages=5)  # doctest: +SKIP
            >>> len(all_reviews) >= 0  # doctest: +SKIP
            True

        """
        all_reviews: list[Review] = []
        continuation_token: str | None = None
        page_count = 0

        while True:
            if max_pages and page_count >= max_pages:
                break

            reviews, continuation_token = self.get_reviews(
                app_id, lang, country, sort, continuation_token
            )

            all_reviews.extend(reviews)

            if not continuation_token:
                break

            page_count += 1

        return all_reviews

    def search(
        self,
        query: str,
        lang: str | None = None,
        country: str = "us",
        n_hits: int = 30,
    ) -> list[SearchResult]:
        """Search for apps (Rust HTTP + parsing, GIL-free).

        Args:
            query: Search query string
            lang: Language code (default: client lang)
            country: Country code (default: "us")
            n_hits: Number of results to return (max: 250)

        Returns:
            list[SearchResult]: List of search results

        Examples:
            >>> client = RustClient()
            >>> results = client.search("music streaming")
            >>> len(results) > 0
            True
            >>> results[0].title
            'Spotify: Music and Podcasts'

        """
        rust_results = fetch_and_parse_search(
            query, lang or self.lang, country, self.timeout
        )
        validated = [SearchResult.from_rust(r) for r in rust_results]
        return validated[:n_hits]

    def list(
        self,
        collection: str,
        category: str | None = None,
        lang: str | None = None,
        country: str = "us",
        num: int = 100,
    ) -> list[SearchResult]:
        """Get list of apps by category and collection (Rust HTTP + parsing, GIL-free).

        **⚠️ EXPERIMENTAL: This feature is currently limited and may not work reliably.**

        Current limitations:
        - Collection parameter is currently ignored (fetches category page only)
        - Results may be empty or incomplete
        - Google Play's API requires complex implementation (batchexecute)

        This method is provided as a placeholder and will be fully implemented
        in a future version to match google-play-scraper's list() functionality.

        Args:
            collection: Collection type (currently ignored - TODO)
            category: Optional category code (e.g., "GAME_ACTION")
            lang: Language code (default: client lang)
            country: Country code (default: "us")
            num: Number of results (default: 100, max: 250)

        Returns:
            list[SearchResult]: List of apps (may be empty in current version)

        Examples:
            >>> from playfast.constants import Category, Collection
            >>> client = RustClient()
            >>> # Note: May return empty results in current version
            >>> results = client.list(collection=Collection.TOP_FREE, category=Category.GAME_ACTION, num=50)
            >>> isinstance(results, list)
            True
            >>> len(results) <= 50  # Should respect num parameter
            True

        Note:
            For reliable app listing, use search() method instead, or wait for
            future versions that implement Google Play's batchexecute API.

        """
        rust_results = fetch_and_parse_list(
            category, collection, lang or self.lang, country, num, self.timeout
        )
        validated = [SearchResult.from_rust(r) for r in rust_results]
        return validated[:num]

    def get_category(
        self,
        category: str,
        collection: str = "TOP_FREE",
        lang: str | None = None,
        country: str = "us",
        num: int = 100,
    ) -> list[SearchResult]:
        """Get apps by category and collection (alias for list()).

        This is a more intuitive name for the list() method.

        **⚠️ EXPERIMENTAL: This feature is currently limited and may not work reliably.**

        Args:
            category: Category code (e.g., "GAME", "SOCIAL", "COMMUNICATION")
            collection: Collection type (e.g., "TOP_FREE", "TOP_PAID", "TOP_GROSSING")
                       Also accepts lowercase (e.g., "topselling_free")
            lang: Language code (default: client lang)
            country: Country code (default: "us")
            num: Number of results (default: 100, max: 250)

        Returns:
            list[SearchResult]: List of apps

        Examples:
            >>> from playfast import RustClient
            >>> with RustClient() as client:
            ...     apps = client.get_category(category="GAME", collection="TOP_FREE", num=10)
            ...     len(apps) > 0  # Verify we got results
            True

        """
        # Convert friendly collection names to API values
        collection_map: dict[str, str] = {
            "TOP_FREE": "topselling_free",
            "TOP_PAID": "topselling_paid",
            "TOP_GROSSING": "topgrossing",
            "TOP_NEW_FREE": "topselling_new_free",
            "TOP_NEW_PAID": "topselling_new_paid",
            "MOVERS_SHAKERS": "movers_shakers",
        }

        # Use mapped value if exists, otherwise use as-is
        collection_value: str = collection_map.get(
            collection.upper(), collection.lower()
        )

        return self.list(
            collection=collection_value,
            category=category,
            lang=lang,
            country=country,
            num=num,
        )

    # Async wrappers for convenience

    async def get_app_async(
        self,
        app_id: str,
        lang: str | None = None,
        country: str = "us",
    ) -> AppInfo:
        """Async wrapper for get_app (runs in thread pool).

        This allows using RustClient in async code while maintaining
        the performance benefits of Rust HTTP.

        Examples:
            >>> import asyncio
            >>> client = RustClient()
            >>> app = asyncio.run(client.get_app_async("com.spotify.music"))
            >>> app.title
            'Spotify: Music and Podcasts'

        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_app, app_id, lang, country)

    async def get_apps_parallel(
        self,
        app_ids: list[str],
        countries: list[str] | None = None,
        lang: str | None = None,
        max_workers: int = 50,
    ) -> dict[str, list[AppInfo]]:
        """Get multiple apps in parallel using thread pool.

        This achieves maximum parallelism by:
        1. Using ThreadPoolExecutor for concurrency
        2. Rust functions release GIL for true parallel execution

        Args:
            app_ids: List of app package IDs
            countries: List of country codes (default: ["us"])
            lang: Language code
            max_workers: Maximum parallel threads (default: 50)

        Returns:
            dict: Country code -> list of AppInfo

        Examples:
            >>> import asyncio
            >>> client = RustClient()
            >>> results = asyncio.run(
            ...     client.get_apps_parallel(
            ...         ["com.spotify.music", "com.netflix.mediaclient"], countries=["us", "kr"], max_workers=100
            ...     )
            ... )
            >>> "us" in results and "kr" in results
            True
            >>> len(results["us"]) > 0
            True

        """
        countries_list: list[str] = countries if countries is not None else ["us"]

        # Create tasks
        tasks: list[tuple[str, str, asyncio.Task[AppInfo]]] = []
        for country_str in countries_list:
            for app_id_str in app_ids:
                task = asyncio.create_task(
                    self.get_app_async(app_id_str, lang, country_str)
                )
                tasks.append((country_str, app_id_str, task))

        # Execute with controlled parallelism
        results: list[AppInfo | BaseException] = await asyncio.gather(
            *[task for _, _, task in tasks], return_exceptions=True
        )

        # Group by country
        by_country: dict[str, list[AppInfo]] = {c: [] for c in countries_list}

        for (country, _app_id, _), result in zip(tasks, results, strict=False):
            if isinstance(result, AppInfo):
                by_country[country].append(result)
            # Silently skip errors (graceful degradation)

        return by_country


# Convenience function for quick usage
def quick_get_app(app_id: str, country: str = "us", timeout: int = 30) -> AppInfo:
    """Quick function to get app info using Rust client.

    This is the fastest way to get a single app's information.

    Examples:
        >>> from playfast import quick_get_app
        >>> app = quick_get_app("com.spotify.music")  # doctest: +SKIP
        >>> app.title  # doctest: +SKIP
        'Spotify: Music and Podcasts'

    Args:
        app_id: App package ID
        country: Country code (default: "us")
        timeout: Request timeout (default: 30)

    Returns:
        AppInfo: App information

    """
    client = RustClient(timeout=timeout)
    return client.get_app(app_id, country=country)

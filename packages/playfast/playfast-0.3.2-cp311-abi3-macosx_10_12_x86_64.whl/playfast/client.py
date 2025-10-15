"""AsyncClient for Playfast - High-level async API for Google Play scraping.

This module provides an easy-to-use async interface that combines:
- aiohttp for async I/O (network requests)
- Rust core for CPU-intensive parsing (GIL-free)
- Pydantic for validation and type safety
"""

import asyncio
from collections.abc import AsyncIterator

import aiohttp

from playfast.core import (
    build_list_request_body,
    fetch_and_parse_reviews,
    parse_app_page,
    parse_batchexecute_list_response,
    parse_search_results,
)
from playfast.exceptions import (
    AppNotFoundError,
    NetworkError,
    ParseError,
    RateLimitError,
)
from playfast.exceptions import (
    TimeoutError as PlayfastTimeoutError,
)
from playfast.models import AppInfo, Review, SearchResult


class AsyncClient:
    """High-level async client for Google Play Store scraping.

    This client combines async I/O (aiohttp) for network requests with
    Rust-powered CPU-intensive parsing for maximum performance.

    Examples:
        >>> async with AsyncClient() as client:
        ...     app = await client.get_app("com.spotify.music")
        ...     print(f"{app.title}: {app.score}⭐")

        >>> async with AsyncClient(max_concurrent=50) as client:
        ...     results = await client.get_apps_parallel(
        ...         ["com.spotify.music", "com.netflix.mediaclient"], countries=["us", "kr", "jp"]
        ...     )

    Args:
        max_concurrent: Maximum concurrent HTTP requests (default: 10)
        timeout: Request timeout in seconds (default: 30)
        headers: Custom HTTP headers (default: Chrome user agent)
        lang: Default language code (default: "en")

    """

    BASE_URL = "https://play.google.com"

    def __init__(
        self,
        max_concurrent: int = 10,
        timeout: int = 30,
        headers: dict[str, str] | None = None,
        lang: str = "en",
    ) -> None:
        """Initialize the async client."""
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.lang = lang

        # Default headers (mimic Chrome browser)
        self._headers = headers or {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept-Language": f"{lang},en-US;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        self._session: aiohttp.ClientSession | None = None
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def __aenter__(self) -> "AsyncClient":
        """Async context manager entry."""
        timeout_config = aiohttp.ClientTimeout(total=self.timeout)

        # Use default connector (already optimized by aiohttp)
        # Custom settings can add overhead for high-concurrency scenarios
        self._session = aiohttp.ClientSession(
            timeout=timeout_config,
            headers=self._headers,
        )
        return self

    async def __aexit__(self, *args: object) -> None:
        """Async context manager exit."""
        if self._session:
            await self._session.close()

    async def _fetch_html(self, url: str, params: dict[str, str] | None = None) -> str:
        """Fetch HTML from URL with rate limiting.

        Args:
            url: URL to fetch
            params: Query parameters

        Returns:
            str: HTML content

        Raises:
            NetworkError: If request fails
            RateLimitError: If rate limited

        """
        if not self._session:
            error_msg = "Client not initialized. Use 'async with AsyncClient()'"
            raise RuntimeError(error_msg)

        async with self._semaphore:  # Rate limiting
            try:
                async with self._session.get(url, params=params) as response:
                    # Check for rate limiting
                    if response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", 60))
                        raise RateLimitError(retry_after)

                    # Check for not found
                    if response.status == 404:
                        raise AppNotFoundError(
                            app_id=params.get("id", "unknown") if params else "unknown"
                        )

                    # Check for other errors
                    if response.status >= 400:
                        raise NetworkError(url, response.status)

                    return await response.text()

            except TimeoutError as e:
                msg = "HTTP request"
                raise PlayfastTimeoutError(msg, self.timeout) from e
            except aiohttp.ClientError as e:
                raise NetworkError(url) from e

    async def get_app(
        self, app_id: str, lang: str | None = None, country: str = "us"
    ) -> AppInfo:
        """Get app information.

        This method performs 3 steps:
        1. Download HTML (async I/O with aiohttp)
        2. Parse HTML (CPU-intensive Rust, GIL-free)
        3. Validate with Pydantic (Python)

        Args:
            app_id: App package ID (e.g., "com.spotify.music")
            lang: Language code (default: client lang)
            country: Country code (default: "us")

        Returns:
            AppInfo: Validated app information

        Raises:
            AppNotFoundError: If app doesn't exist
            ParseError: If parsing fails
            NetworkError: If network request fails

        Examples:
            >>> app = await client.get_app("com.spotify.music")
            >>> print(f"{app.title}: {app.score}⭐")

        """
        # Step 1: Async I/O - Download HTML
        url = f"{self.BASE_URL}/store/apps/details"
        params = {"id": app_id, "hl": lang or self.lang, "gl": country}

        html = await self._fetch_html(url, params)

        # Step 2: CPU-intensive - Parse with Rust (GIL-free)
        try:
            loop = asyncio.get_event_loop()
            rust_app = await loop.run_in_executor(None, parse_app_page, html, app_id)
        except Exception as e:
            msg = f"Failed to parse app page: {e}"
            raise ParseError(msg) from e

        # Step 3: Validation - Pydantic
        return AppInfo.from_rust(rust_app)

    async def get_apps_parallel(
        self,
        app_ids: list[str],
        countries: list[str] | None = None,
        lang: str | None = None,
    ) -> dict[str, list[AppInfo]]:
        """Get multiple apps in parallel across multiple countries.

        This method leverages true parallelism:
        - Async I/O for concurrent network requests
        - Rust parsing releases GIL for parallel CPU work

        Args:
            app_ids: List of app package IDs
            countries: List of country codes (default: ["us"])
            lang: Language code (default: client lang)

        Returns:
            dict: Country code -> list of AppInfo

        Examples:
            >>> results = await client.get_apps_parallel(
            ...     ["com.spotify.music", "com.netflix.mediaclient"], countries=["us", "kr", "jp"]
            ... )
            >>> for country, apps in results.items():
            ...     print(f"{country}: {len(apps)} apps")

        """
        countries = countries or ["us"]

        # Create tasks for all app+country combinations
        tasks: list[asyncio.Task[AppInfo]] = []
        task_metadata: list[tuple[str, str]] = []

        for country in countries:
            for app_id in app_ids:
                task = asyncio.create_task(
                    self.get_app(app_id, lang=lang, country=country)
                )
                tasks.append(task)
                task_metadata.append((country, app_id))

        # Execute all tasks in parallel
        results: list[AppInfo | BaseException] = await asyncio.gather(
            *tasks, return_exceptions=True
        )

        # Group by country
        by_country: dict[str, list[AppInfo]] = {c: [] for c in countries}

        for (country, _app_id), result in zip(task_metadata, results, strict=False):
            if isinstance(result, AppInfo):
                by_country[country].append(result)
            elif isinstance(result, Exception):
                # Log error but continue (graceful degradation)
                # In production, you might want proper logging here
                pass

        return by_country

    async def stream_reviews(
        self,
        app_id: str,
        lang: str | None = None,
        country: str = "us",
        sort: int = 1,
        max_pages: int | None = None,
    ) -> AsyncIterator[Review]:
        """Stream reviews with pagination (memory efficient).

        This is a generator that yields reviews one by one without
        loading all reviews into memory at once.

        Args:
            app_id: App package ID
            lang: Language code (default: client lang)
            country: Country code (default: "us")
            sort: Sort order (1=newest, 2=highest rating, 3=most helpful)
            max_pages: Maximum number of pages to fetch (default: unlimited)

        Yields:
            Review: Individual review objects

        Examples:
            >>> async for review in client.stream_reviews("com.spotify.music"):
            ...     print(f"{review.user_name}: {review.score}⭐")
            ...     if review.is_positive():
            ...         print("  Positive review!")

        """
        continuation_token: str | None = None
        page_count = 0

        while True:
            # Check page limit
            if max_pages and page_count >= max_pages:
                break

            # Use Rust fetch_and_parse_reviews (batchexecute API)
            try:
                loop = asyncio.get_event_loop()
                rust_reviews, next_token = await loop.run_in_executor(
                    None,
                    fetch_and_parse_reviews,
                    app_id,
                    lang or self.lang,
                    country,
                    sort,
                    continuation_token,
                    self.timeout,
                )
            except Exception as e:
                msg = f"Failed to fetch reviews: {e}"
                raise ParseError(msg) from e

            # Yield validated reviews
            for rust_review in rust_reviews:
                yield Review.from_rust(rust_review)

            # Check for next page
            if not next_token:
                break

            continuation_token = next_token
            page_count += 1

    async def search(
        self,
        query: str,
        lang: str | None = None,
        country: str = "us",
        n_hits: int = 30,
    ) -> list[SearchResult]:
        """Search for apps.

        Args:
            query: Search query string
            lang: Language code (default: client lang)
            country: Country code (default: "us")
            n_hits: Number of results to return (max: 250)

        Returns:
            list[SearchResult]: List of search results

        Examples:
            >>> results = await client.search("music streaming")
            >>> for result in results:
            ...     print(f"{result.title} by {result.developer}")

        """
        url = f"{self.BASE_URL}/store/search"
        params = {
            "q": query,
            "hl": lang or self.lang,
            "gl": country,
            "c": "apps",
        }

        # Fetch HTML
        html = await self._fetch_html(url, params)

        # Parse search results (Rust, GIL-free)
        try:
            loop = asyncio.get_event_loop()
            rust_results = await loop.run_in_executor(None, parse_search_results, html)
        except Exception as e:
            msg = f"Failed to parse search results: {e}"
            raise ParseError(msg) from e

        # Validate and limit results
        validated = [SearchResult.from_rust(r) for r in rust_results]
        return validated[:n_hits]

    async def list(
        self,
        collection: str,
        category: str | None = None,
        lang: str | None = None,
        country: str = "us",
        num: int = 100,
    ) -> list[SearchResult]:
        """Get apps from a category/collection.

        This method uses the async HTTP + Rust parsing approach for true parallelism:
        1. Build request body with Rust (GIL-free)
        2. Download response with async I/O (aiohttp)
        3. Parse with Rust (GIL-free, parallel-ready)

        Args:
            collection: Collection type (e.g., "topselling_free", "topgrossing")
            category: Category code (e.g., "GAME_ACTION", "SOCIAL") or None for all
            lang: Language code (default: client lang)
            country: Country code (default: "us")
            num: Number of results (default: 100, max: 250)

        Returns:
            list[SearchResult]: List of apps

        Examples:
            >>> apps = await client.list(
            ...     collection="topselling_free", category="GAME_ACTION", country="us", num=200
            ... )
            >>> for app in apps:
            ...     print(f"{app.title} by {app.developer}")

        """
        if not self._session:
            error_msg = "Client not initialized. Use 'async with AsyncClient()'"
            raise RuntimeError(error_msg)

        # Step 1: Build request body (Rust, GIL-free)
        loop = asyncio.get_event_loop()
        body = await loop.run_in_executor(
            None, build_list_request_body, category, collection, num
        )

        # Prepare batchexecute URL with params
        url = f"{self.BASE_URL}/_/PlayStoreUi/data/batchexecute"
        params = {
            "rpcids": "vyAe2",
            "source-path": "/store/apps",
            "f.sid": "-4178618388443751758",
            "bl": "boq_playuiserver_20220612.08_p0",
            "hl": lang or self.lang,
            "gl": country,
            "authuser": "0",
            "soc-app": "121",
            "soc-platform": "1",
            "soc-device": "1",
            "_reqid": "82003",
            "rt": "c",
        }

        headers = {
            **self._headers,
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        }

        # Step 2: Fetch response (async I/O)
        async with self._semaphore:
            try:
                async with self._session.post(
                    url, params=params, data=body, headers=headers
                ) as response:
                    if response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", 60))
                        raise RateLimitError(retry_after)

                    if response.status >= 400:
                        raise NetworkError(url, response.status)

                    response_text = await response.text()

            except TimeoutError as e:
                msg = "HTTP request"
                raise PlayfastTimeoutError(msg, self.timeout) from e
            except aiohttp.ClientError as e:
                raise NetworkError(url) from e

        # Step 3: Parse with Rust (GIL-free, parallel-ready)
        try:
            rust_results = await loop.run_in_executor(
                None, parse_batchexecute_list_response, response_text
            )
        except Exception as e:
            msg = f"Failed to parse list response: {e}"
            raise ParseError(msg) from e

        # Validate and return
        return [SearchResult.from_rust(r) for r in rust_results]

    async def close(self) -> None:
        """Close the HTTP session manually (if not using context manager)."""
        if self._session:
            await self._session.close()
            self._session = None

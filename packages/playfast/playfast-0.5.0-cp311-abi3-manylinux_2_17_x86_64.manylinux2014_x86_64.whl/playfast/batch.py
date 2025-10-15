"""High-level batch processing API for Playfast.

This module provides user-friendly batch functions that wrap the low-level
core functions, making batch processing easier and more intuitive.
"""

from playfast.batch_builder import BatchRequestBuilder
from playfast.core import (
    fetch_and_parse_apps_batch as _fetch_apps_batch,
)
from playfast.core import (
    fetch_and_parse_list_batch as _fetch_list_batch,
)
from playfast.core import (
    fetch_and_parse_reviews_batch as _fetch_reviews_batch,
)
from playfast.core import (
    fetch_and_parse_search_batch as _fetch_search_batch,
)
from playfast.models import AppInfo, Review, SearchResult


# =============================================================================
# High-level batch functions (user-friendly API)
# =============================================================================


def fetch_apps(
    app_ids: list[str],
    countries: list[str],
    lang: str = "en",
) -> list[AppInfo]:
    """Fetch multiple apps across multiple countries in parallel.

    Args:
        app_ids: List of app package IDs (e.g., ["com.spotify.music", ...])
        countries: List of country codes (e.g., ["us", "kr", "jp"])
        lang: Language code (default: "en")

    Returns:
        List of AppInfo objects (one per app per country)

    Example:
        >>> apps = fetch_apps(  # doctest: +SKIP
        ...     app_ids=["com.spotify.music", "com.netflix.mediaclient"], countries=["us", "kr"], lang="en"
        ... )
        >>> print(f"Fetched {len(apps)} apps")  # doctest: +SKIP

    """
    requests = [(app_id, lang, country) for app_id in app_ids for country in countries]
    rust_apps = _fetch_apps_batch(requests)
    return [AppInfo.from_rust(app) for app in rust_apps]


def fetch_category_lists(
    countries: list[str],
    categories: list[str | None],
    collection: str = "topselling_free",
    lang: str = "en",
    num_results: int = 100,
) -> list[list[SearchResult]]:
    """Fetch category/collection lists from multiple countries in parallel.

    Args:
        countries: List of country codes (e.g., ["us", "kr", "jp"])
        categories: List of category names or None for all apps
        collection: Collection name (default: "topselling_free")
        lang: Language code (default: "en")
        num_results: Number of results per request (default: 100)

    Returns:
        List of result lists (one list per request, in same order as input)

    Example:
        >>> results = fetch_category_lists(  # doctest: +SKIP
        ...     countries=["us", "kr", "jp"], categories=["GAME_ACTION", "SOCIAL"], num_results=50
        ... )
        >>> for result_list in results:  # doctest: +SKIP
        ...     print(f"Got {len(result_list)} apps")  # doctest: +SKIP

    """
    requests = [
        (category, collection, lang, country, num_results)
        for country in countries
        for category in categories
    ]
    rust_results = _fetch_list_batch(requests)
    return [[SearchResult.from_rust(app) for app in apps] for apps in rust_results]


def search_apps(
    queries: list[str],
    countries: list[str],
    lang: str = "en",
) -> list[list[SearchResult]]:
    """Perform multiple searches across multiple countries in parallel.

    Args:
        queries: List of search queries
        countries: List of country codes
        lang: Language code (default: "en")

    Returns:
        List of search result lists (one list per query per country)

    Example:
        >>> results = search_apps(queries=["spotify", "netflix"], countries=["us", "kr"])  # doctest: +SKIP
        >>> for result_list in results:  # doctest: +SKIP
        ...     for app in result_list:  # doctest: +SKIP
        ...         print(app.title)  # doctest: +SKIP

    """
    requests = [(query, lang, country) for query in queries for country in countries]
    rust_results = _fetch_search_batch(requests)
    return [[SearchResult.from_rust(app) for app in apps] for apps in rust_results]


def fetch_reviews(
    app_ids: list[str],
    countries: list[str],
    lang: str = "en",
    sort: int = 1,
) -> list[tuple[list[Review], str | None]]:
    """Fetch reviews for multiple apps across multiple countries in parallel.

    Args:
        app_ids: List of app package IDs
        countries: List of country codes
        lang: Language code (default: "en")
        sort: Sort order (1=newest, 2=highest, 3=most helpful)

    Returns:
        List of (reviews, next_token) tuples

    Example:
        >>> results = fetch_reviews(app_ids=["com.spotify.music"], countries=["us", "kr"])  # doctest: +SKIP
        >>> for reviews, token in results:  # doctest: +SKIP
        ...     print(f"Got {len(reviews)} reviews")  # doctest: +SKIP

    """
    requests: list[tuple[str, str, str, int, str | None]] = [
        (app_id, lang, country, sort, None)
        for app_id in app_ids
        for country in countries
    ]
    rust_results = _fetch_reviews_batch(requests)
    return [
        ([Review.from_rust(review) for review in reviews], token)
        for reviews, token in rust_results
    ]


# =============================================================================
# Convenience functions for common use cases
# =============================================================================


def fetch_top_apps(
    countries: list[str],
    categories: list[str],
    collection: str = "topselling_free",
    num_results: int = 100,
    lang: str = "en",
) -> dict[str, dict[str, list[SearchResult]]]:
    """Fetch top apps organized by country and category.

    This is a convenience wrapper that returns organized results.

    Args:
        countries: List of country codes
        categories: List of category names
        collection: Collection name (default: "topselling_free")
        num_results: Number of results per request (default: 100)
        lang: Language code (default: "en")

    Returns:
        Nested dict: {country: {category: [apps]}}

    Example:
        >>> results = fetch_top_apps(  # doctest: +SKIP
        ...     countries=["us", "kr"], categories=["GAME_ACTION", "SOCIAL"], num_results=50
        ... )
        >>> us_games = results["us"]["GAME_ACTION"]  # doctest: +SKIP
        >>> print(f"US top games: {len(us_games)}")  # doctest: +SKIP

    """
    # Fetch all in one batch
    categories_list: list[str | None] = list(categories)
    all_results = fetch_category_lists(
        countries=countries,
        categories=categories_list,
        collection=collection,
        lang=lang,
        num_results=num_results,
    )

    # Organize by country and category
    organized: dict[str, dict[str, list[SearchResult]]] = {}
    idx = 0
    for country in countries:
        organized[country] = {}
        for category in categories:
            organized[country][category] = all_results[idx]
            idx += 1

    return organized


def fetch_multi_country_apps(
    app_id: str,
    countries: list[str],
    lang: str = "en",
) -> dict[str, AppInfo]:
    """Fetch the same app from multiple countries.

    Args:
        app_id: App package ID
        countries: List of country codes
        lang: Language code (default: "en")

    Returns:
        Dict mapping country code to AppInfo

    Example:
        >>> apps = fetch_multi_country_apps(
        ...     "com.spotify.music", countries=["us", "kr", "jp", "de"]
        ... )  # doctest: +SKIP
        >>> for country, app in apps.items():  # doctest: +SKIP
        ...     print(f"{country}: {app.score} stars")  # doctest: +SKIP

    """
    apps = fetch_apps(
        app_ids=[app_id],
        countries=countries,
        lang=lang,
    )

    return dict(zip(countries, apps, strict=False))


# =============================================================================
# Advanced: Builder-based API for complex scenarios
# =============================================================================


class BatchFetcher:
    """Advanced batch fetcher with builder pattern.

    This class provides a more flexible interface for complex batch operations,
    with progress tracking and error handling.

    Example:
        >>> fetcher = BatchFetcher(lang="en")
        >>> results = fetcher.category_lists(
        ...     countries=["us", "kr", "jp"], categories=["GAME_ACTION", "SOCIAL"], num_results=100
        ... )

    """

    def __init__(
        self,
        lang: str = "en",
        default_num_results: int = 100,
        default_collection: str = "topselling_free",
    ) -> None:
        """Initialize batch fetcher with default parameters.

        Args:
            lang: Default language code
            default_num_results: Default number of results per request
            default_collection: Default collection name

        """
        self.lang = lang
        self.default_num_results = default_num_results
        self.default_collection = default_collection
        self._builder = BatchRequestBuilder(
            collection=default_collection,
            lang=lang,
            num_results=default_num_results,
            intern_strings=True,
        )

    def apps(
        self,
        app_ids: list[str],
        countries: list[str],
        lang: str | None = None,
    ) -> list[AppInfo]:
        """Fetch apps (uses instance defaults)."""
        return fetch_apps(
            app_ids=app_ids,
            countries=countries,
            lang=lang or self.lang,
        )

    def category_lists(
        self,
        countries: list[str],
        categories: list[str | None],
        collection: str | None = None,
        num_results: int | None = None,
        lang: str | None = None,
    ) -> list[list[SearchResult]]:
        """Fetch category lists (uses instance defaults)."""
        return fetch_category_lists(
            countries=countries,
            categories=categories,
            collection=collection or self.default_collection,
            lang=lang or self.lang,
            num_results=num_results or self.default_num_results,
        )

    def search(
        self,
        queries: list[str],
        countries: list[str],
        lang: str | None = None,
    ) -> list[list[SearchResult]]:
        """Search apps (uses instance defaults)."""
        return search_apps(
            queries=queries,
            countries=countries,
            lang=lang or self.lang,
        )

    def get_builder_stats(self) -> dict[str, int | bool]:
        """Get memory statistics from internal builder."""
        return self._builder.get_memory_stats()

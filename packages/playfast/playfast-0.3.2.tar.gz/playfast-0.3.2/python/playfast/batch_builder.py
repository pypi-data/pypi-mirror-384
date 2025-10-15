"""Batch Request Builder - Memory-efficient request generation.

This module provides utilities for building batch requests efficiently,
minimizing memory usage through string interning and smart caching.
"""

from collections.abc import Iterator
from itertools import product
import sys


class BatchRequestBuilder:
    """Memory-efficient batch request builder.

    This class helps build large batches of requests while minimizing
    memory usage through:
    1. String interning for repeated values
    2. Lazy evaluation with generators
    3. Smart caching of common parameters

    Example:
        >>> builder = BatchRequestBuilder(collection="topselling_free", lang="en", num_results=100)
        >>> requests = list(
        ...     builder.build_list_requests(countries=["us", "kr", "jp"], categories=["GAME_ACTION", "SOCIAL"])
        ... )
        >>> len(requests)
        6

    """

    def __init__(
        self,
        collection: str = "topselling_free",
        lang: str = "en",
        num_results: int = 100,
        intern_strings: bool = True,
    ) -> None:
        """Initialize batch request builder.

        Args:
            collection: Default collection name
            lang: Default language code
            num_results: Default number of results per request
            intern_strings: Whether to intern strings for memory efficiency

        """
        self.intern_strings = intern_strings

        if intern_strings:
            self.collection = sys.intern(collection)
            self.lang = sys.intern(lang)
        else:
            self.collection = collection
            self.lang = lang

        self.num_results = num_results

        # Cache for interned strings
        self._string_cache: dict[str, str] = {}

    def _intern(self, s: str) -> str:
        """Intern string with caching."""
        if not self.intern_strings:
            return s

        if s not in self._string_cache:
            self._string_cache[s] = sys.intern(s)
        return self._string_cache[s]

    def build_list_requests(
        self,
        countries: list[str],
        categories: list[str | None],
        collection: str | None = None,
        lang: str | None = None,
        num: int | None = None,
    ) -> Iterator[tuple[str | None, str, str, str, int]]:
        """Generate list/category fetch requests.

        Args:
            countries: List of country codes
            categories: List of category names (None for all apps)
            collection: Override default collection
            lang: Override default language
            num: Override default num_results

        Yields:
            Request tuples: (category, collection, lang, country, num)

        Example:
            >>> builder = BatchRequestBuilder()
            >>> requests = list(
            ...     builder.build_list_requests(countries=["us", "kr"], categories=["GAME_ACTION", None])
            ... )
            >>> len(requests)
            4

        """
        coll = self._intern(collection) if collection else self.collection
        lng = self._intern(lang) if lang else self.lang
        n = num if num is not None else self.num_results

        # Use itertools.product for efficient iteration
        for country, category in product(countries, categories):
            yield (
                self._intern(category) if category else None,
                coll,
                lng,
                self._intern(country),
                n,
            )

    def build_app_requests(
        self,
        app_ids: list[str],
        countries: list[str],
        lang: str | None = None,
    ) -> Iterator[tuple[str, str, str]]:
        """Generate app fetch requests.

        Args:
            app_ids: List of app package IDs
            countries: List of country codes
            lang: Override default language

        Yields:
            Request tuples: (app_id, lang, country)

        """
        lng = self._intern(lang) if lang else self.lang

        for app_id, country in product(app_ids, countries):
            yield (
                self._intern(app_id),
                lng,
                self._intern(country),
            )

    def build_search_requests(
        self,
        queries: list[str],
        countries: list[str],
        lang: str | None = None,
    ) -> Iterator[tuple[str, str, str]]:
        """Generate search requests.

        Args:
            queries: List of search queries
            countries: List of country codes
            lang: Override default language

        Yields:
            Request tuples: (query, lang, country)

        """
        lng = self._intern(lang) if lang else self.lang

        for query, country in product(queries, countries):
            yield (
                self._intern(query),
                lng,
                self._intern(country),
            )

    def build_review_requests(
        self,
        app_ids: list[str],
        countries: list[str],
        lang: str | None = None,
        sort: int = 1,
        continuation_token: str | None = None,
    ) -> Iterator[tuple[str, str, str, int, str | None]]:
        """Generate review fetch requests.

        Args:
            app_ids: List of app package IDs
            countries: List of country codes
            lang: Override default language
            sort: Sort order (1=newest, 2=highest, 3=most helpful)
            continuation_token: Pagination token

        Yields:
            Request tuples: (app_id, lang, country, sort, token)

        """
        lng = self._intern(lang) if lang else self.lang
        token = self._intern(continuation_token) if continuation_token else None

        for app_id, country in product(app_ids, countries):
            yield (
                self._intern(app_id),
                lng,
                self._intern(country),
                sort,
                token,
            )

    def get_memory_stats(self) -> dict[str, int | bool]:
        """Get memory usage statistics.

        Returns:
            Dictionary with memory statistics

        """
        return {
            "cached_strings": len(self._string_cache),
            "cache_enabled": self.intern_strings,
            "shared_collection": id(self.collection),
            "shared_lang": id(self.lang),
        }


# Convenience functions for quick usage


def build_multi_country_requests(
    countries: list[str],
    categories: list[str],
    collection: str = "topselling_free",
    num_results: int = 100,
) -> list[tuple[str | None, str, str, str, int]]:
    """Quick helper for building multi-country category requests.

    Args:
        countries: List of country codes
        categories: List of category names
        collection: Collection name
        num_results: Number of results per request

    Returns:
        List of request tuples

    Example:
        >>> requests = build_multi_country_requests(
        ...     countries=["us", "kr", "jp"], categories=["GAME_ACTION", "SOCIAL"], num_results=50
        ... )
        >>> len(requests)
        6

    """
    builder = BatchRequestBuilder(collection=collection, num_results=num_results)
    categories_list: list[str | None] = list(categories)
    return list(builder.build_list_requests(countries, categories_list))


def build_app_country_matrix(
    app_ids: list[str],
    countries: list[str],
    lang: str = "en",
) -> list[tuple[str, str, str]]:
    """Build requests for multiple apps across multiple countries.

    Args:
        app_ids: List of app package IDs
        countries: List of country codes
        lang: Language code

    Returns:
        List of request tuples

    Example:
        >>> requests = build_app_country_matrix(
        ...     app_ids=["com.spotify.music", "com.netflix.mediaclient"], countries=["us", "kr", "jp"]
        ... )
        >>> len(requests)
        6

    """
    builder = BatchRequestBuilder(lang=lang)
    return list(builder.build_app_requests(app_ids, countries))

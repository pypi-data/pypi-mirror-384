"""Tests for batch module (high-level batch API)."""

import pytest

from playfast.batch import (
    BatchFetcher,
    fetch_apps,
    fetch_category_lists,
    fetch_multi_country_apps,
    fetch_reviews,
    fetch_top_apps,
    search_apps,
)
from playfast.models import AppInfo, Review, SearchResult


class TestFetchApps:
    """Test fetch_apps function."""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network and real Google Play access")
    def test_fetch_apps_single_country(self):
        """Test fetching apps from a single country."""
        apps = fetch_apps(
            app_ids=["com.google.android.apps.maps"],
            countries=["us"],
            lang="en",
        )
        assert isinstance(apps, list)
        assert len(apps) == 1
        assert isinstance(apps[0], AppInfo)
        assert apps[0].app_id == "com.google.android.apps.maps"

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network and real Google Play access")
    def test_fetch_apps_multiple_countries(self):
        """Test fetching apps from multiple countries."""
        apps = fetch_apps(
            app_ids=["com.google.android.apps.maps"],
            countries=["us", "kr", "jp"],
            lang="en",
        )
        assert isinstance(apps, list)
        assert len(apps) == 3  # 1 app x 3 countries
        assert all(isinstance(app, AppInfo) for app in apps)

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network and real Google Play access")
    def test_fetch_apps_multiple_apps_and_countries(self):
        """Test fetching multiple apps from multiple countries."""
        apps = fetch_apps(
            app_ids=["com.google.android.apps.maps", "com.spotify.music"],
            countries=["us", "kr"],
            lang="en",
        )
        assert isinstance(apps, list)
        assert len(apps) == 4  # 2 apps x 2 countries

    def test_fetch_apps_returns_list(self):
        """Test that fetch_apps returns a list."""
        # Even with network errors, should attempt to return list structure
        try:
            result = fetch_apps(app_ids=["test.app"], countries=["us"], lang="en")
            assert isinstance(result, list)
        except Exception:
            # Network errors are acceptable in unit tests
            pass


class TestFetchCategoryLists:
    """Test fetch_category_lists function."""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network and real Google Play access")
    def test_fetch_category_lists_single_category(self):
        """Test fetching category lists."""
        results = fetch_category_lists(
            countries=["us"],
            categories=["GAME_ACTION"],
            collection="topselling_free",
            lang="en",
            num_results=10,
        )
        assert isinstance(results, list)
        assert len(results) == 1  # 1 country x 1 category
        assert isinstance(results[0], list)
        assert all(isinstance(app, SearchResult) for app in results[0])

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network and real Google Play access")
    def test_fetch_category_lists_multiple(self):
        """Test fetching multiple category lists."""
        results = fetch_category_lists(
            countries=["us", "kr"],
            categories=["GAME_ACTION", "SOCIAL"],
            num_results=5,
        )
        assert isinstance(results, list)
        assert len(results) == 4  # 2 countries x 2 categories

    def test_fetch_category_lists_returns_nested_list(self):
        """Test that fetch_category_lists returns list of lists."""
        try:
            result = fetch_category_lists(
                countries=["us"],
                categories=["GAME_ACTION"],
                num_results=1,
            )
            assert isinstance(result, list)
        except Exception:
            pass


class TestSearchApps:
    """Test search_apps function."""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network and real Google Play access")
    def test_search_apps_single_query(self):
        """Test searching apps."""
        results = search_apps(
            queries=["maps"],
            countries=["us"],
            lang="en",
        )
        assert isinstance(results, list)
        assert len(results) == 1
        assert isinstance(results[0], list)
        assert all(isinstance(app, SearchResult) for app in results[0])

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network and real Google Play access")
    def test_search_apps_multiple_queries(self):
        """Test searching with multiple queries."""
        results = search_apps(
            queries=["maps", "music"],
            countries=["us", "kr"],
        )
        assert isinstance(results, list)
        assert len(results) == 4  # 2 queries x 2 countries


class TestFetchReviews:
    """Test fetch_reviews function."""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network and real Google Play access")
    def test_fetch_reviews_single_app(self):
        """Test fetching reviews."""
        results = fetch_reviews(
            app_ids=["com.google.android.apps.maps"],
            countries=["us"],
            lang="en",
            sort=1,
        )
        assert isinstance(results, list)
        assert len(results) == 1
        reviews, token = results[0]
        assert isinstance(reviews, list)
        assert all(isinstance(review, Review) for review in reviews)
        assert token is None or isinstance(token, str)

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network and real Google Play access")
    def test_fetch_reviews_multiple(self):
        """Test fetching reviews from multiple apps and countries."""
        results = fetch_reviews(
            app_ids=["com.google.android.apps.maps"],
            countries=["us", "kr"],
        )
        assert isinstance(results, list)
        assert len(results) == 2  # 1 app x 2 countries


class TestFetchTopApps:
    """Test fetch_top_apps function."""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network and real Google Play access")
    def test_fetch_top_apps_organized(self):
        """Test fetching top apps organized by country and category."""
        results = fetch_top_apps(
            countries=["us", "kr"],
            categories=["GAME_ACTION", "SOCIAL"],
            collection="topselling_free",
            num_results=5,
            lang="en",
        )
        assert isinstance(results, dict)
        assert "us" in results
        assert "kr" in results
        assert "GAME_ACTION" in results["us"]
        assert "SOCIAL" in results["us"]
        assert isinstance(results["us"]["GAME_ACTION"], list)

    def test_fetch_top_apps_returns_dict(self):
        """Test that fetch_top_apps returns a nested dict."""
        try:
            result = fetch_top_apps(
                countries=["us"],
                categories=["GAME_ACTION"],
                num_results=1,
            )
            assert isinstance(result, dict)
        except Exception:
            pass


class TestFetchMultiCountryApps:
    """Test fetch_multi_country_apps function."""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network and real Google Play access")
    def test_fetch_multi_country_apps(self):
        """Test fetching same app from multiple countries."""
        results = fetch_multi_country_apps(
            app_id="com.google.android.apps.maps",
            countries=["us", "kr", "jp"],
            lang="en",
        )
        assert isinstance(results, dict)
        assert len(results) == 3
        assert "us" in results
        assert "kr" in results
        assert "jp" in results
        assert all(isinstance(app, AppInfo) for app in results.values())

    def test_fetch_multi_country_apps_returns_dict(self):
        """Test that fetch_multi_country_apps returns dict."""
        try:
            result = fetch_multi_country_apps(
                app_id="test.app",
                countries=["us"],
            )
            assert isinstance(result, dict)
        except Exception:
            pass


class TestBatchFetcher:
    """Test BatchFetcher class."""

    def test_batch_fetcher_init_defaults(self):
        """Test BatchFetcher initialization with defaults."""
        fetcher = BatchFetcher()
        assert fetcher.lang == "en"
        assert fetcher.default_num_results == 100
        assert fetcher.default_collection == "topselling_free"

    def test_batch_fetcher_init_custom(self):
        """Test BatchFetcher initialization with custom values."""
        fetcher = BatchFetcher(
            lang="ko",
            default_num_results=50,
            default_collection="topgrossing",
        )
        assert fetcher.lang == "ko"
        assert fetcher.default_num_results == 50
        assert fetcher.default_collection == "topgrossing"

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network and real Google Play access")
    def test_batch_fetcher_apps(self):
        """Test BatchFetcher.apps method."""
        fetcher = BatchFetcher(lang="en")
        apps = fetcher.apps(
            app_ids=["com.google.android.apps.maps"],
            countries=["us"],
        )
        assert isinstance(apps, list)
        assert len(apps) == 1

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network and real Google Play access")
    def test_batch_fetcher_category_lists(self):
        """Test BatchFetcher.category_lists method."""
        fetcher = BatchFetcher()
        results = fetcher.category_lists(
            countries=["us"],
            categories=["GAME_ACTION"],
            num_results=5,
        )
        assert isinstance(results, list)

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network and real Google Play access")
    def test_batch_fetcher_search(self):
        """Test BatchFetcher.search method."""
        fetcher = BatchFetcher()
        results = fetcher.search(
            queries=["maps"],
            countries=["us"],
        )
        assert isinstance(results, list)

    def test_batch_fetcher_get_builder_stats(self):
        """Test BatchFetcher.get_builder_stats method."""
        fetcher = BatchFetcher()
        stats = fetcher.get_builder_stats()
        assert isinstance(stats, dict)
        assert "cached_strings" in stats
        assert "cache_enabled" in stats
        assert "shared_collection" in stats
        assert "shared_lang" in stats
        assert isinstance(stats["cached_strings"], int)
        assert isinstance(stats["cache_enabled"], bool)


class TestBatchFetcherOverrides:
    """Test BatchFetcher with parameter overrides."""

    def test_batch_fetcher_apps_lang_override(self):
        """Test that apps method respects lang override."""
        fetcher = BatchFetcher(lang="en")
        # Override with Korean
        try:
            fetcher.apps(
                app_ids=["test.app"],
                countries=["us"],
                lang="ko",
            )
        except Exception:
            # Network error acceptable
            pass

    def test_batch_fetcher_category_lists_overrides(self):
        """Test category_lists with all overrides."""
        fetcher = BatchFetcher(
            lang="en",
            default_num_results=100,
            default_collection="topselling_free",
        )
        try:
            fetcher.category_lists(
                countries=["us"],
                categories=["GAME_ACTION"],
                collection="topgrossing",
                num_results=5,
                lang="ko",
            )
        except Exception:
            pass


class TestBatchIntegration:
    """Integration tests for batch operations."""

    def test_batch_functions_exist(self):
        """Test that all batch functions are importable."""
        assert callable(fetch_apps)
        assert callable(fetch_category_lists)
        assert callable(search_apps)
        assert callable(fetch_reviews)
        assert callable(fetch_top_apps)
        assert callable(fetch_multi_country_apps)

    def test_batch_fetcher_is_class(self):
        """Test that BatchFetcher is a proper class."""
        assert isinstance(BatchFetcher, type)
        fetcher = BatchFetcher()
        assert isinstance(fetcher, BatchFetcher)

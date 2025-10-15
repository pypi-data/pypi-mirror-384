"""Tests for batch_builder module (memory-efficient request building)."""

import sys

from playfast.batch_builder import (
    BatchRequestBuilder,
    build_app_country_matrix,
    build_multi_country_requests,
)


class TestBatchRequestBuilder:
    """Test BatchRequestBuilder class."""

    def test_init_defaults(self):
        """Test initialization with default parameters."""
        builder = BatchRequestBuilder()
        assert builder.collection == "topselling_free"
        assert builder.lang == "en"
        assert builder.num_results == 100
        assert builder.intern_strings is True

    def test_init_custom(self):
        """Test initialization with custom parameters."""
        builder = BatchRequestBuilder(
            collection="topgrossing",
            lang="ko",
            num_results=50,
            intern_strings=False,
        )
        assert builder.collection == "topgrossing"
        assert builder.lang == "ko"
        assert builder.num_results == 50
        assert builder.intern_strings is False

    def test_init_string_interning_enabled(self):
        """Test that string interning works when enabled."""
        builder = BatchRequestBuilder(
            collection="test_collection",
            lang="test_lang",
            intern_strings=True,
        )
        # When interning is enabled, strings should be interned
        assert builder.collection == sys.intern("test_collection")
        assert builder.lang == sys.intern("test_lang")

    def test_init_string_interning_disabled(self):
        """Test that string interning is skipped when disabled."""
        builder = BatchRequestBuilder(
            collection="test_collection",
            lang="test_lang",
            intern_strings=False,
        )
        # When interning is disabled, strings are just regular strings
        assert builder.collection == "test_collection"
        assert builder.lang == "test_lang"


class TestBuildListRequests:
    """Test build_list_requests method."""

    def test_build_list_requests_basic(self):
        """Test building basic list requests."""
        builder = BatchRequestBuilder()
        requests = list(
            builder.build_list_requests(
                countries=["us", "kr"],
                categories=["GAME_ACTION", "SOCIAL"],
            )
        )
        # 2 countries x 2 categories = 4 requests
        assert len(requests) == 4
        # Check structure: (category, collection, lang, country, num)
        assert all(len(req) == 5 for req in requests)

    def test_build_list_requests_with_none_category(self):
        """Test building list requests with None category."""
        builder = BatchRequestBuilder()
        requests = list(
            builder.build_list_requests(
                countries=["us"],
                categories=[None, "GAME_ACTION"],
            )
        )
        assert len(requests) == 2
        # First request should have None category
        assert requests[0][0] is None
        # Second request should have category
        assert requests[1][0] == "GAME_ACTION"

    def test_build_list_requests_override_defaults(self):
        """Test overriding default parameters."""
        builder = BatchRequestBuilder(
            collection="topselling_free",
            lang="en",
            num_results=100,
        )
        requests = list(
            builder.build_list_requests(
                countries=["us"],
                categories=["GAME_ACTION"],
                collection="topgrossing",
                lang="ko",
                num=50,
            )
        )
        # Should use overridden values
        category, collection, lang, country, num = requests[0]
        assert collection == "topgrossing"
        assert lang == "ko"
        assert num == 50

    def test_build_list_requests_order(self):
        """Test that requests are generated in correct order."""
        builder = BatchRequestBuilder()
        requests = list(
            builder.build_list_requests(
                countries=["us", "kr"],
                categories=["GAME_ACTION", "SOCIAL"],
            )
        )
        # Order should be: (us, GAME_ACTION), (us, SOCIAL), (kr, GAME_ACTION), (kr, SOCIAL)
        assert requests[0][3] == "us"
        assert requests[0][0] == "GAME_ACTION"
        assert requests[1][3] == "us"
        assert requests[1][0] == "SOCIAL"
        assert requests[2][3] == "kr"
        assert requests[2][0] == "GAME_ACTION"
        assert requests[3][3] == "kr"
        assert requests[3][0] == "SOCIAL"

    def test_build_list_requests_empty_lists(self):
        """Test with empty country or category lists."""
        builder = BatchRequestBuilder()
        requests = list(
            builder.build_list_requests(countries=[], categories=["GAME_ACTION"])
        )
        assert len(requests) == 0


class TestBuildAppRequests:
    """Test build_app_requests method."""

    def test_build_app_requests_basic(self):
        """Test building basic app requests."""
        builder = BatchRequestBuilder()
        requests = list(
            builder.build_app_requests(
                app_ids=["com.app1", "com.app2"],
                countries=["us", "kr"],
            )
        )
        # 2 apps x 2 countries = 4 requests
        assert len(requests) == 4
        # Check structure: (app_id, lang, country)
        assert all(len(req) == 3 for req in requests)

    def test_build_app_requests_override_lang(self):
        """Test overriding language."""
        builder = BatchRequestBuilder(lang="en")
        requests = list(
            builder.build_app_requests(
                app_ids=["com.app1"],
                countries=["us"],
                lang="ko",
            )
        )
        app_id, lang, country = requests[0]
        assert lang == "ko"

    def test_build_app_requests_order(self):
        """Test request generation order."""
        builder = BatchRequestBuilder()
        requests = list(
            builder.build_app_requests(
                app_ids=["com.app1", "com.app2"],
                countries=["us", "kr"],
            )
        )
        # Order should be: (app1, us), (app1, kr), (app2, us), (app2, kr)
        assert requests[0][0] == "com.app1"
        assert requests[0][2] == "us"
        assert requests[1][0] == "com.app1"
        assert requests[1][2] == "kr"
        assert requests[2][0] == "com.app2"
        assert requests[2][2] == "us"


class TestBuildSearchRequests:
    """Test build_search_requests method."""

    def test_build_search_requests_basic(self):
        """Test building basic search requests."""
        builder = BatchRequestBuilder()
        requests = list(
            builder.build_search_requests(
                queries=["maps", "music"],
                countries=["us", "kr"],
            )
        )
        # 2 queries x 2 countries = 4 requests
        assert len(requests) == 4
        # Check structure: (query, lang, country)
        assert all(len(req) == 3 for req in requests)

    def test_build_search_requests_override_lang(self):
        """Test overriding language."""
        builder = BatchRequestBuilder(lang="en")
        requests = list(
            builder.build_search_requests(
                queries=["test"],
                countries=["us"],
                lang="ja",
            )
        )
        query, lang, country = requests[0]
        assert lang == "ja"


class TestBuildReviewRequests:
    """Test build_review_requests method."""

    def test_build_review_requests_basic(self):
        """Test building basic review requests."""
        builder = BatchRequestBuilder()
        requests = list(
            builder.build_review_requests(
                app_ids=["com.app1"],
                countries=["us", "kr"],
            )
        )
        # 1 app x 2 countries = 2 requests
        assert len(requests) == 2
        # Check structure: (app_id, lang, country, sort, token)
        assert all(len(req) == 5 for req in requests)

    def test_build_review_requests_with_sort(self):
        """Test building review requests with sort parameter."""
        builder = BatchRequestBuilder()
        requests = list(
            builder.build_review_requests(
                app_ids=["com.app1"],
                countries=["us"],
                sort=2,
            )
        )
        app_id, lang, country, sort, token = requests[0]
        assert sort == 2

    def test_build_review_requests_with_token(self):
        """Test building review requests with continuation token."""
        builder = BatchRequestBuilder()
        requests = list(
            builder.build_review_requests(
                app_ids=["com.app1"],
                countries=["us"],
                continuation_token="next_page_token",
            )
        )
        app_id, lang, country, sort, token = requests[0]
        assert token == "next_page_token"

    def test_build_review_requests_defaults(self):
        """Test default values for review requests."""
        builder = BatchRequestBuilder()
        requests = list(
            builder.build_review_requests(
                app_ids=["com.app1"],
                countries=["us"],
            )
        )
        app_id, lang, country, sort, token = requests[0]
        assert sort == 1  # default sort
        assert token is None  # default token


class TestStringInterning:
    """Test string interning functionality."""

    def test_intern_method_with_interning_enabled(self):
        """Test _intern method when interning is enabled."""
        builder = BatchRequestBuilder(intern_strings=True)
        test_str = "test_string"
        interned = builder._intern(test_str)
        assert interned == test_str
        # Should be the same object as sys.intern would create
        assert interned is sys.intern(test_str)

    def test_intern_method_with_interning_disabled(self):
        """Test _intern method when interning is disabled."""
        builder = BatchRequestBuilder(intern_strings=False)
        test_str = "test_string"
        result = builder._intern(test_str)
        assert result == test_str

    def test_string_cache_usage(self):
        """Test that string cache is used correctly."""
        builder = BatchRequestBuilder(intern_strings=True)
        # Cache should start empty (only default strings)
        initial_cache_size = len(builder._string_cache)

        # Intern a new string
        test_str = "new_test_string_12345"
        builder._intern(test_str)

        # Cache should now contain the new string
        assert len(builder._string_cache) == initial_cache_size + 1
        assert test_str in builder._string_cache

        # Interning again should reuse cached version
        builder._intern(test_str)
        assert len(builder._string_cache) == initial_cache_size + 1


class TestGetMemoryStats:
    """Test get_memory_stats method."""

    def test_get_memory_stats_structure(self):
        """Test memory stats return structure."""
        builder = BatchRequestBuilder()
        stats = builder.get_memory_stats()

        assert isinstance(stats, dict)
        assert "cached_strings" in stats
        assert "cache_enabled" in stats
        assert "shared_collection" in stats
        assert "shared_lang" in stats

    def test_get_memory_stats_types(self):
        """Test memory stats value types."""
        builder = BatchRequestBuilder()
        stats = builder.get_memory_stats()

        assert isinstance(stats["cached_strings"], int)
        assert isinstance(stats["cache_enabled"], bool)
        assert isinstance(stats["shared_collection"], int)
        assert isinstance(stats["shared_lang"], int)

    def test_get_memory_stats_cache_enabled(self):
        """Test stats reflect interning state."""
        builder_with_intern = BatchRequestBuilder(intern_strings=True)
        builder_without_intern = BatchRequestBuilder(intern_strings=False)

        assert builder_with_intern.get_memory_stats()["cache_enabled"] is True
        assert builder_without_intern.get_memory_stats()["cache_enabled"] is False

    def test_get_memory_stats_cached_strings_count(self):
        """Test that cached_strings count increases."""
        builder = BatchRequestBuilder(intern_strings=True)
        initial_count = builder.get_memory_stats()["cached_strings"]

        # Intern some strings
        builder._intern("test1")
        builder._intern("test2")
        builder._intern("test3")

        final_count = builder.get_memory_stats()["cached_strings"]
        assert final_count >= initial_count + 3


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_build_multi_country_requests(self):
        """Test build_multi_country_requests function."""
        requests = build_multi_country_requests(
            countries=["us", "kr"],
            categories=["GAME_ACTION", "SOCIAL"],
            collection="topselling_free",
            num_results=50,
        )
        assert isinstance(requests, list)
        assert len(requests) == 4  # 2 countries x 2 categories

    def test_build_multi_country_requests_structure(self):
        """Test structure of requests from build_multi_country_requests."""
        requests = build_multi_country_requests(
            countries=["us"],
            categories=["GAME_ACTION"],
        )
        # Should be (category, collection, lang, country, num)
        assert len(requests[0]) == 5

    def test_build_app_country_matrix(self):
        """Test build_app_country_matrix function."""
        requests = build_app_country_matrix(
            app_ids=["com.app1", "com.app2"],
            countries=["us", "kr"],
            lang="en",
        )
        assert isinstance(requests, list)
        assert len(requests) == 4  # 2 apps x 2 countries

    def test_build_app_country_matrix_structure(self):
        """Test structure of requests from build_app_country_matrix."""
        requests = build_app_country_matrix(
            app_ids=["com.app1"],
            countries=["us"],
        )
        # Should be (app_id, lang, country)
        assert len(requests[0]) == 3


class TestIteratorBehavior:
    """Test that builders return iterators."""

    def test_build_list_requests_returns_iterator(self):
        """Test that build_list_requests returns an iterator."""
        builder = BatchRequestBuilder()
        result = builder.build_list_requests(
            countries=["us"],
            categories=["GAME_ACTION"],
        )
        # Should be an iterator/generator
        assert hasattr(result, "__iter__")
        assert hasattr(result, "__next__")

    def test_build_app_requests_returns_iterator(self):
        """Test that build_app_requests returns an iterator."""
        builder = BatchRequestBuilder()
        result = builder.build_app_requests(
            app_ids=["com.app1"],
            countries=["us"],
        )
        assert hasattr(result, "__iter__")
        assert hasattr(result, "__next__")

    def test_iterator_lazy_evaluation(self):
        """Test that iterators use lazy evaluation."""
        builder = BatchRequestBuilder()
        # Creating the iterator should not generate all requests immediately
        iterator = builder.build_app_requests(
            app_ids=["app" + str(i) for i in range(1000)],
            countries=["us"],
        )
        # Iterator creation should be fast (lazy)
        # Actually consuming it will generate requests on demand
        first = next(iterator)
        assert first[0] == "app0"


class TestMemoryEfficiency:
    """Test memory efficiency features."""

    def test_large_batch_string_interning(self):
        """Test that string interning reduces memory with large batches."""
        builder = BatchRequestBuilder(intern_strings=True)
        countries = ["us"] * 100  # Same country repeated
        categories = ["GAME_ACTION"] * 100  # Same category repeated

        requests = list(
            builder.build_list_requests(
                countries=countries,
                categories=categories,
            )
        )
        # Should generate 10000 requests
        assert len(requests) == 10000

        # But cache should only have unique strings
        stats = builder.get_memory_stats()
        # Should have far fewer cached strings than total requests
        assert stats["cached_strings"] < 100

    def test_shared_default_strings(self):
        """Test that default strings are shared across requests."""
        builder = BatchRequestBuilder(collection="test", lang="en")
        stats1 = builder.get_memory_stats()

        # Generate requests (will use default collection and lang)
        list(
            builder.build_list_requests(
                countries=["us", "kr"],
                categories=["GAME_ACTION"],
            )
        )

        stats2 = builder.get_memory_stats()
        # Collection and lang IDs should remain the same (shared objects)
        assert stats1["shared_collection"] == stats2["shared_collection"]
        assert stats1["shared_lang"] == stats2["shared_lang"]

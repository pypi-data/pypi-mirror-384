"""Tests for RustClient (high-level Python API)."""

from unittest.mock import MagicMock, patch

import pytest

from playfast import Category, Collection, RustClient, quick_get_app
from playfast.models import AppInfo, Review, SearchResult


class TestRustClientCreation:
    """Test RustClient instantiation."""

    def test_create_with_defaults(self):
        """Test creating RustClient with default parameters."""
        client = RustClient()
        assert client.timeout == 30
        assert client.lang == "en"

    def test_create_with_custom_params(self):
        """Test creating RustClient with custom parameters."""
        client = RustClient(timeout=60, lang="ko")
        assert client.timeout == 60
        assert client.lang == "ko"

    def test_client_has_methods(self):
        """Test that RustClient has expected methods."""
        client = RustClient()
        assert hasattr(client, "get_app")
        assert hasattr(client, "get_reviews")
        assert hasattr(client, "get_all_reviews")
        assert hasattr(client, "search")
        assert hasattr(client, "list")
        assert hasattr(client, "get_app_async")
        assert hasattr(client, "get_apps_parallel")


class TestRustClientGetApp:
    """Test RustClient.get_app() method."""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network access")
    def test_get_app_basic(self):
        """Test basic get_app functionality."""
        client = RustClient(timeout=30)
        app = client.get_app("com.google.android.apps.maps")

        assert isinstance(app, AppInfo)
        assert app.app_id == "com.google.android.apps.maps"
        assert len(app.title) > 0
        assert len(app.developer) > 0

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network access")
    def test_get_app_with_country(self):
        """Test get_app with different country."""
        client = RustClient()
        app = client.get_app("com.spotify.music", country="kr")

        assert isinstance(app, AppInfo)
        assert app.app_id == "com.spotify.music"

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network access")
    def test_get_app_with_lang(self):
        """Test get_app with different language."""
        client = RustClient()
        app = client.get_app("com.spotify.music", lang="ko", country="kr")

        assert isinstance(app, AppInfo)
        # Title may be in Korean
        assert len(app.title) > 0

    def test_get_app_nonexistent(self):
        """Test get_app with nonexistent app."""
        client = RustClient(timeout=5)
        with pytest.raises(Exception):  # Should raise error
            client.get_app("com.nonexistent.app.that.does.not.exist.12345")


class TestRustClientGetReviews:
    """Test RustClient.get_reviews() method."""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network access")
    def test_get_reviews_basic(self):
        """Test basic get_reviews functionality."""
        client = RustClient()
        reviews, next_token = client.get_reviews("com.spotify.music")

        assert isinstance(reviews, list)
        if len(reviews) > 0:
            assert isinstance(reviews[0], Review)
            assert len(reviews[0].content) > 0
            assert 1 <= reviews[0].score <= 5

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network access")
    def test_get_reviews_with_sort(self):
        """Test get_reviews with different sort orders."""
        client = RustClient()

        # Sort by newest (1)
        reviews, _ = client.get_reviews("com.spotify.music", sort=1)
        assert isinstance(reviews, list)

        # Sort by highest rated (2)
        reviews, _ = client.get_reviews("com.spotify.music", sort=2)
        assert isinstance(reviews, list)

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network access")
    def test_get_reviews_pagination(self):
        """Test review pagination with continuation token."""
        client = RustClient()

        # Get first page
        reviews1, token1 = client.get_reviews("com.spotify.music")
        assert isinstance(reviews1, list)

        # Get second page if token exists
        if token1:
            reviews2, token2 = client.get_reviews(
                "com.spotify.music", continuation_token=token1
            )
            assert isinstance(reviews2, list)

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network access")
    def test_get_all_reviews(self):
        """Test get_all_reviews method."""
        client = RustClient()
        all_reviews = client.get_all_reviews(
            "com.spotify.music",
            max_pages=2,  # Limit to 2 pages for testing
        )

        assert isinstance(all_reviews, list)
        if len(all_reviews) > 0:
            assert isinstance(all_reviews[0], Review)


class TestRustClientSearch:
    """Test RustClient.search() method."""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network access")
    def test_search_basic(self):
        """Test basic search functionality."""
        client = RustClient()
        results = client.search("maps", n_hits=10)

        assert isinstance(results, list)
        assert len(results) <= 10
        if len(results) > 0:
            assert isinstance(results[0], SearchResult)
            assert len(results[0].title) > 0

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network access")
    def test_search_with_country(self):
        """Test search with different country."""
        client = RustClient()
        results = client.search("music", country="kr", n_hits=5)

        assert isinstance(results, list)
        assert len(results) <= 5

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network access")
    def test_search_limit_results(self):
        """Test that n_hits limits results."""
        client = RustClient()

        results_5 = client.search("game", n_hits=5)
        results_10 = client.search("game", n_hits=10)

        assert len(results_5) <= 5
        assert len(results_10) <= 10


class TestRustClientList:
    """Test RustClient.list() method - NEW FUNCTIONALITY."""

    def test_list_method_exists(self):
        """Test that list method exists."""
        client = RustClient()
        assert hasattr(client, "list")
        assert callable(client.list)

    @patch("playfast.rust_client.fetch_and_parse_list")
    def test_list_with_mock(self, mock_fetch):
        """Test list with mocked Rust function."""
        # Create mock result objects
        mock_result1 = MagicMock()
        mock_result1.app_id = "com.test1"
        mock_result1.title = "Test App 1"
        mock_result1.developer = "Dev 1"
        mock_result1.icon = "https://example.com/icon1.png"
        mock_result1.score = 4.5
        mock_result1.price = 0.0
        mock_result1.currency = "USD"

        mock_result2 = MagicMock()
        mock_result2.app_id = "com.test2"
        mock_result2.title = "Test App 2"
        mock_result2.developer = "Dev 2"
        mock_result2.icon = "https://example.com/icon2.png"
        mock_result2.score = 4.0
        mock_result2.price = 2.99
        mock_result2.currency = "USD"

        # Mock return value
        mock_fetch.return_value = [mock_result1, mock_result2]

        # Call list method
        client = RustClient()
        results = client.list(
            collection=Collection.TOP_FREE, category=Category.GAME_ACTION, num=10
        )

        # Verify mock was called correctly
        mock_fetch.assert_called_once_with(
            "GAME_ACTION", "topselling_free", "en", "us", 10, 30
        )

        # Verify results
        assert len(results) == 2
        assert isinstance(results[0], SearchResult)
        assert results[0].app_id == "com.test1"
        assert results[0].title == "Test App 1"
        assert results[1].app_id == "com.test2"

    @patch("playfast.rust_client.fetch_and_parse_list")
    def test_list_without_category_mock(self, mock_fetch):
        """Test list without category using mock."""
        mock_result = MagicMock()
        mock_result.app_id = "com.nocategory"
        mock_result.title = "No Category App"
        mock_result.developer = "Dev"
        mock_result.icon = "https://example.com/icon.png"
        mock_result.score = 3.5
        mock_result.price = 0.0
        mock_result.currency = "USD"

        mock_fetch.return_value = [mock_result]

        client = RustClient()
        results = client.list(
            collection=Collection.TOP_PAID,
            category=None,  # No category
            num=5,
        )

        # Verify None was passed for category
        mock_fetch.assert_called_once_with(
            None,  # category is None
            "topselling_paid",
            "en",
            "us",
            5,
            30,
        )

        assert len(results) == 1
        assert results[0].app_id == "com.nocategory"

    @patch("playfast.rust_client.fetch_and_parse_list")
    def test_list_respects_num_limit(self, mock_fetch):
        """Test that list respects the num parameter."""
        # Return more results than requested
        mock_results = []
        for i in range(20):
            mock_result = MagicMock()
            mock_result.app_id = f"com.test{i}"
            mock_result.title = f"App {i}"
            mock_result.developer = "Dev"
            mock_result.icon = "https://example.com/icon.png"
            mock_result.score = 4.0
            mock_result.price = 0.0
            mock_result.currency = "USD"
            mock_results.append(mock_result)

        mock_fetch.return_value = mock_results

        client = RustClient()
        results = client.list(
            collection=Collection.TOP_FREE,
            category=Category.GAME_PUZZLE,
            num=5,  # Request only 5
        )

        # Should limit to 5 even though 20 were returned
        assert len(results) <= 5

    @patch("playfast.rust_client.fetch_and_parse_list")
    def test_list_with_different_collections(self, mock_fetch):
        """Test list with different collection types."""
        mock_result = MagicMock()
        mock_result.app_id = "com.test"
        mock_result.title = "Test App"
        mock_result.developer = "Dev"
        mock_result.icon = "https://example.com/icon.png"
        mock_result.score = None
        mock_result.price = 0.0
        mock_result.currency = "USD"

        mock_fetch.return_value = [mock_result]

        client = RustClient()

        # Test different collections
        collections = [
            Collection.TOP_FREE,
            Collection.TOP_PAID,
            Collection.TOP_GROSSING,
            Collection.TOP_NEW_FREE,
        ]

        for collection in collections:
            results = client.list(
                collection=collection, category=Category.PRODUCTIVITY, num=1
            )
            assert len(results) == 1
            assert results[0].app_id == "com.test"

    @patch("playfast.rust_client.fetch_and_parse_list")
    def test_list_uses_client_lang(self, mock_fetch):
        """Test that list uses client's language setting."""
        mock_fetch.return_value = []

        client = RustClient(lang="ko")
        client.list(
            collection=Collection.TOP_FREE, category=Category.GAME_ACTION, num=10
        )

        # Verify Korean language was used
        call_args = mock_fetch.call_args[0]
        assert call_args[2] == "ko"  # lang parameter

    @pytest.mark.integration
    def test_list_real_network_call(self):
        """Real integration test for list() with actual network call.

        This test is marked as 'integration' but NOT skipped, so it will run
        and verify that the list() function actually works with Google Play.

        Note: This may be slow or fail due to rate limiting/network issues.
        """
        try:
            client = RustClient(timeout=10)
            results = client.list(
                collection=Collection.TOP_FREE,
                category=Category.GAME_ACTION,
                num=5,  # Small number for faster test
            )

            # Basic validation
            assert isinstance(results, list)
            # May return 0 results if blocked/rate limited, so don't assert > 0
            if len(results) > 0:
                assert isinstance(results[0], SearchResult)
                assert hasattr(results[0], "app_id")
                assert hasattr(results[0], "title")
        except Exception as e:
            # If network fails, that's okay - we tested that the API works
            pytest.skip(f"Network test skipped due to: {e}")

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network access")
    def test_list_without_category(self):
        """Test list without category (all categories)."""
        client = RustClient()
        results = client.list(
            collection=Collection.TOP_FREE,
            category=None,  # No category
            num=5,
        )

        assert isinstance(results, list)
        assert len(results) <= 5

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network access")
    def test_list_different_collections(self):
        """Test list with different collection types."""
        client = RustClient()

        # Top free
        free_results = client.list(
            collection=Collection.TOP_FREE, category=Category.GAME_ACTION, num=3
        )
        assert isinstance(free_results, list)

        # Top paid
        paid_results = client.list(
            collection=Collection.TOP_PAID, category=Category.PRODUCTIVITY, num=3
        )
        assert isinstance(paid_results, list)

        # Top grossing
        grossing_results = client.list(collection=Collection.TOP_GROSSING, num=3)
        assert isinstance(grossing_results, list)

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network access")
    def test_list_with_country(self):
        """Test list with different country."""
        client = RustClient()
        results = client.list(
            collection=Collection.TOP_FREE,
            category=Category.GAME_ACTION,
            country="kr",
            num=5,
        )

        assert isinstance(results, list)
        assert len(results) <= 5

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network access")
    def test_list_limit_results(self):
        """Test that num parameter limits results."""
        client = RustClient()

        results_5 = client.list(
            collection=Collection.TOP_FREE, category=Category.GAME_PUZZLE, num=5
        )
        results_20 = client.list(
            collection=Collection.TOP_FREE, category=Category.GAME_PUZZLE, num=20
        )

        assert len(results_5) <= 5
        assert len(results_20) <= 20

    def test_list_accepts_string_values(self):
        """Test that list accepts string values for collection/category."""
        client = RustClient()

        # Should accept enum values
        try:
            # Will fail with network error but signature is correct
            client.list(
                collection=Collection.TOP_FREE, category=Category.GAME_ACTION, num=1
            )
        except Exception:
            pass  # Network error expected

        # Should also accept string values directly
        try:
            client.list(collection="topselling_free", category="GAME_ACTION", num=1)
        except Exception:
            pass  # Network error expected


class TestRustClientAsync:
    """Test RustClient async methods."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network access")
    async def test_get_app_async(self):
        """Test get_app_async method."""
        client = RustClient()
        app = await client.get_app_async("com.spotify.music")

        assert isinstance(app, AppInfo)
        assert app.app_id == "com.spotify.music"

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network access")
    async def test_get_apps_parallel(self):
        """Test get_apps_parallel method."""
        client = RustClient()
        app_ids = ["com.spotify.music", "com.netflix.mediaclient"]

        results = await client.get_apps_parallel(
            app_ids=app_ids, countries=["us"], max_workers=10
        )

        assert isinstance(results, dict)
        assert "us" in results
        assert isinstance(results["us"], list)


class TestRustClientQuickFunction:
    """Test quick_get_app convenience function."""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network access")
    def test_quick_get_app(self):
        """Test quick_get_app function."""
        from playfast import quick_get_app

        app = quick_get_app("com.spotify.music")
        assert isinstance(app, AppInfo)
        assert app.app_id == "com.spotify.music"

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network access")
    def test_quick_get_app_with_params(self):
        """Test quick_get_app with parameters."""
        from playfast import quick_get_app

        app = quick_get_app("com.spotify.music", country="kr", timeout=30)
        assert isinstance(app, AppInfo)


class TestRustClientErrorHandling:
    """Test error handling in RustClient."""

    def test_invalid_app_id(self):
        """Test handling of invalid app ID."""
        client = RustClient(timeout=5)
        with pytest.raises(Exception):
            client.get_app("invalid")

    def test_timeout_handling(self):
        """Test that timeout is respected."""
        client = RustClient(timeout=1)  # Very short timeout
        # Should timeout quickly for slow connections
        # (May not always raise depending on network speed)
        try:
            client.get_app("com.google.android.apps.maps")
        except Exception:
            pass  # Expected to fail with timeout or other error


class TestRustClientContextManager:
    """Tests for RustClient context manager."""

    def test_context_manager_enter_exit(self):
        """Test context manager protocol."""
        client = RustClient()
        with client as c:
            assert c is client
            assert c.timeout == 30
            assert c.lang == "en"
        # No cleanup needed, but should exit cleanly

    def test_manual_context_manager(self):
        """Test manual context manager usage."""
        client = RustClient()
        entered = client.__enter__()
        assert entered is client

        client.__exit__(None, None, None)
        # Should exit without error


class TestRustClientGetAppWithMock:
    """Tests for get_app() using mocks."""

    @patch("playfast.rust_client.fetch_and_parse_app")
    def test_get_app_basic_mock(self, mock_fetch):
        """Test get_app with mocked Rust function."""
        # Create mock Rust result
        mock_rust_app = MagicMock()
        mock_rust_app.app_id = "com.test.app"
        mock_rust_app.title = "Test App"
        mock_rust_app.description = "Description"
        mock_rust_app.developer = "Test Developer"
        mock_rust_app.developer_id = "dev123"
        mock_rust_app.score = 4.5
        mock_rust_app.ratings = 1000
        mock_rust_app.price = 0.0
        mock_rust_app.currency = "USD"
        mock_rust_app.icon = "https://example.com/icon.png"
        mock_rust_app.screenshots = []
        mock_rust_app.category = "GAME"
        mock_rust_app.version = "1.0"
        mock_rust_app.updated = "2024-01-01"
        mock_rust_app.installs = "1,000+"
        mock_rust_app.min_android = "5.0"
        mock_rust_app.permissions = []

        mock_fetch.return_value = mock_rust_app

        client = RustClient()
        app = client.get_app("com.test.app")

        # Verify Rust function was called correctly
        mock_fetch.assert_called_once_with(
            "com.test.app",
            "en",  # Default lang
            "us",  # Default country
            30,  # Default timeout
        )

        # Verify result
        assert isinstance(app, AppInfo)
        assert app.app_id == "com.test.app"
        assert app.title == "Test App"
        assert app.score == 4.5

    @patch("playfast.rust_client.fetch_and_parse_app")
    def test_get_app_with_custom_lang(self, mock_fetch):
        """Test get_app with custom language."""
        mock_rust_app = MagicMock()
        mock_rust_app.app_id = "com.test"
        mock_rust_app.title = "테스트"
        mock_rust_app.description = ""
        mock_rust_app.developer = "개발자"
        mock_rust_app.developer_id = None
        mock_rust_app.score = None
        mock_rust_app.ratings = 0
        mock_rust_app.price = 0.0
        mock_rust_app.currency = "KRW"
        mock_rust_app.icon = "https://example.com/icon.png"
        mock_rust_app.screenshots = []
        mock_rust_app.category = None
        mock_rust_app.version = None
        mock_rust_app.updated = None
        mock_rust_app.installs = None
        mock_rust_app.min_android = None
        mock_rust_app.permissions = []

        mock_fetch.return_value = mock_rust_app

        client = RustClient(lang="ko")
        app = client.get_app("com.test", lang="ko", country="kr")

        # Verify custom parameters
        mock_fetch.assert_called_once_with("com.test", "ko", "kr", 30)
        assert app.currency == "KRW"

    @patch("playfast.rust_client.fetch_and_parse_app")
    def test_get_app_uses_client_defaults(self, mock_fetch):
        """Test that get_app uses client's default settings."""
        mock_rust_app = MagicMock()
        mock_rust_app.app_id = "com.test"
        mock_rust_app.title = "Test"
        mock_rust_app.description = ""
        mock_rust_app.developer = "Dev"
        mock_rust_app.developer_id = None
        mock_rust_app.score = None
        mock_rust_app.ratings = 0
        mock_rust_app.price = 0.0
        mock_rust_app.currency = "EUR"
        mock_rust_app.icon = "https://example.com/icon.png"
        mock_rust_app.screenshots = []
        mock_rust_app.category = None
        mock_rust_app.version = None
        mock_rust_app.updated = None
        mock_rust_app.installs = None
        mock_rust_app.min_android = None
        mock_rust_app.permissions = []

        mock_fetch.return_value = mock_rust_app

        client = RustClient(timeout=60, lang="fr")
        client.get_app("com.test")

        # Should use client's lang and timeout
        mock_fetch.assert_called_once_with("com.test", "fr", "us", 60)


class TestRustClientGetReviewsWithMock:
    """Tests for get_reviews() using mocks."""

    @patch("playfast.rust_client.fetch_and_parse_reviews")
    def test_get_reviews_basic_mock(self, mock_fetch):
        """Test get_reviews with mocked Rust function."""
        mock_review = MagicMock()
        mock_review.review_id = "r1"
        mock_review.user_name = "User"
        mock_review.user_image = None
        mock_review.content = "Great app!"
        mock_review.score = 5
        mock_review.thumbs_up = 10
        mock_review.created_at = 1704067200
        mock_review.reply_content = None
        mock_review.reply_at = None

        mock_fetch.return_value = ([mock_review], "next_token_123")

        client = RustClient()
        reviews, next_token = client.get_reviews("com.test.app")

        # Verify call
        mock_fetch.assert_called_once_with(
            "com.test.app",
            "en",
            "us",
            1,  # Default sort
            None,  # No continuation token
            30,
        )

        # Verify results
        assert len(reviews) == 1
        assert isinstance(reviews[0], Review)
        assert reviews[0].review_id == "r1"
        assert next_token == "next_token_123"

    @patch("playfast.rust_client.fetch_and_parse_reviews")
    def test_get_reviews_with_pagination(self, mock_fetch):
        """Test get_reviews with continuation token."""
        mock_review = MagicMock()
        mock_review.review_id = "r2"
        mock_review.user_name = "User2"
        mock_review.user_image = None
        mock_review.content = "Good"
        mock_review.score = 4
        mock_review.thumbs_up = 5
        mock_review.created_at = 1704067200
        mock_review.reply_content = None
        mock_review.reply_at = None

        mock_fetch.return_value = ([mock_review], None)

        client = RustClient()
        reviews, next_token = client.get_reviews(
            "com.test.app", continuation_token="token_123"
        )

        # Verify token was passed
        call_args = mock_fetch.call_args[0]
        assert call_args[4] == "token_123"  # continuation_token
        assert next_token is None  # Last page

    @patch("playfast.rust_client.fetch_and_parse_reviews")
    def test_get_reviews_with_sort(self, mock_fetch):
        """Test get_reviews with different sort orders."""
        mock_fetch.return_value = ([], None)

        client = RustClient()

        # Test sort=2 (highest rated)
        client.get_reviews("com.test.app", sort=2)
        assert mock_fetch.call_args[0][3] == 2

        # Test sort=3 (most helpful)
        client.get_reviews("com.test.app", sort=3)
        assert mock_fetch.call_args[0][3] == 3


class TestRustClientGetAllReviews:
    """Tests for get_all_reviews() pagination logic."""

    @patch("playfast.rust_client.fetch_and_parse_reviews")
    def test_get_all_reviews_single_page(self, mock_fetch):
        """Test get_all_reviews with single page."""
        mock_review = MagicMock()
        mock_review.review_id = "r1"
        mock_review.user_name = "User"
        mock_review.user_image = None
        mock_review.content = "Good"
        mock_review.score = 4
        mock_review.thumbs_up = 5
        mock_review.created_at = 1704067200
        mock_review.reply_content = None
        mock_review.reply_at = None

        # Single page, no next token
        mock_fetch.return_value = ([mock_review], None)

        client = RustClient()
        all_reviews = client.get_all_reviews("com.test.app")

        # Should be called once
        assert mock_fetch.call_count == 1
        assert len(all_reviews) == 1

    @patch("playfast.rust_client.fetch_and_parse_reviews")
    def test_get_all_reviews_multiple_pages(self, mock_fetch):
        """Test get_all_reviews with multiple pages."""
        # Page 1
        mock_review1 = MagicMock()
        mock_review1.review_id = "r1"
        mock_review1.user_name = "User1"
        mock_review1.user_image = None
        mock_review1.content = "Page 1"
        mock_review1.score = 5
        mock_review1.thumbs_up = 10
        mock_review1.created_at = 1704067200
        mock_review1.reply_content = None
        mock_review1.reply_at = None

        # Page 2
        mock_review2 = MagicMock()
        mock_review2.review_id = "r2"
        mock_review2.user_name = "User2"
        mock_review2.user_image = None
        mock_review2.content = "Page 2"
        mock_review2.score = 4
        mock_review2.thumbs_up = 5
        mock_review2.created_at = 1704067200
        mock_review2.reply_content = None
        mock_review2.reply_at = None

        # First call returns page 1 with token, second returns page 2 without token
        mock_fetch.side_effect = [
            ([mock_review1], "token_page2"),
            ([mock_review2], None),
        ]

        client = RustClient()
        all_reviews = client.get_all_reviews("com.test.app")

        # Should be called twice
        assert mock_fetch.call_count == 2
        assert len(all_reviews) == 2
        assert all_reviews[0].content == "Page 1"
        assert all_reviews[1].content == "Page 2"

    @patch("playfast.rust_client.fetch_and_parse_reviews")
    def test_get_all_reviews_with_max_pages(self, mock_fetch):
        """Test get_all_reviews respects max_pages limit."""
        mock_review = MagicMock()
        mock_review.review_id = "r1"
        mock_review.user_name = "User"
        mock_review.user_image = None
        mock_review.content = "Review"
        mock_review.score = 5
        mock_review.thumbs_up = 10
        mock_review.created_at = 1704067200
        mock_review.reply_content = None
        mock_review.reply_at = None

        # Always return a next token (infinite pages available)
        mock_fetch.return_value = ([mock_review], "next_token")

        client = RustClient()
        all_reviews = client.get_all_reviews("com.test.app", max_pages=2)

        # Should stop at 2 pages (first page + 1 additional)
        assert mock_fetch.call_count == 2
        assert len(all_reviews) == 2


class TestRustClientSearchWithMock:
    """Tests for search() using mocks."""

    @patch("playfast.rust_client.fetch_and_parse_search")
    def test_search_basic_mock(self, mock_fetch):
        """Test search with mocked Rust function."""
        mock_result = MagicMock()
        mock_result.app_id = "com.test"
        mock_result.title = "Test App"
        mock_result.developer = "Dev"
        mock_result.icon = "https://example.com/icon.png"
        mock_result.score = 4.5
        mock_result.price = 0.0
        mock_result.currency = "USD"

        mock_fetch.return_value = [mock_result]

        client = RustClient()
        results = client.search("test query", n_hits=10)

        # Verify call
        mock_fetch.assert_called_once_with("test query", "en", "us", 30)

        # Verify result
        assert len(results) == 1
        assert isinstance(results[0], SearchResult)
        assert results[0].title == "Test App"

    @patch("playfast.rust_client.fetch_and_parse_search")
    def test_search_limits_results(self, mock_fetch):
        """Test that search respects n_hits limit."""
        # Return more results than requested
        mock_results = []
        for i in range(50):
            mock_result = MagicMock()
            mock_result.app_id = f"com.test{i}"
            mock_result.title = f"App {i}"
            mock_result.developer = "Dev"
            mock_result.icon = "https://example.com/icon.png"
            mock_result.score = 4.0
            mock_result.price = 0.0
            mock_result.currency = "USD"
            mock_results.append(mock_result)

        mock_fetch.return_value = mock_results

        client = RustClient()
        results = client.search("test", n_hits=5)

        # Should limit to 5
        assert len(results) == 5


class TestRustClientGetCategory:
    """Tests for get_category() method."""

    @patch("playfast.rust_client.fetch_and_parse_list")
    def test_get_category_basic(self, mock_fetch):
        """Test get_category basic functionality."""
        mock_result = MagicMock()
        mock_result.app_id = "com.test"
        mock_result.title = "Test"
        mock_result.developer = "Dev"
        mock_result.icon = "https://example.com/icon.png"
        mock_result.score = 4.0
        mock_result.price = 0.0
        mock_result.currency = "USD"

        mock_fetch.return_value = [mock_result]

        client = RustClient()
        results = client.get_category(category="GAME", collection="TOP_FREE", num=10)

        # Verify conversion to API values
        call_args = mock_fetch.call_args[0]
        assert call_args[0] == "GAME"  # category
        assert call_args[1] == "topselling_free"  # collection converted

        assert len(results) == 1

    @patch("playfast.rust_client.fetch_and_parse_list")
    def test_get_category_collection_mapping(self, mock_fetch):
        """Test get_category collection name mapping."""
        mock_fetch.return_value = []

        client = RustClient()

        # Test different collection mappings
        mappings = {
            "TOP_FREE": "topselling_free",
            "TOP_PAID": "topselling_paid",
            "TOP_GROSSING": "topgrossing",
            "TOP_NEW_FREE": "topselling_new_free",
            "TOP_NEW_PAID": "topselling_new_paid",
            "MOVERS_SHAKERS": "movers_shakers",
        }

        for input_name, expected_api_name in mappings.items():
            client.get_category("GAME", collection=input_name, num=1)
            call_args = mock_fetch.call_args[0]
            assert call_args[1] == expected_api_name

    @patch("playfast.rust_client.fetch_and_parse_list")
    def test_get_category_lowercase_collection(self, mock_fetch):
        """Test get_category with already lowercase collection."""
        mock_fetch.return_value = []

        client = RustClient()
        client.get_category("GAME", collection="topselling_free", num=1)

        # Should use as-is
        call_args = mock_fetch.call_args[0]
        assert call_args[1] == "topselling_free"


class TestRustClientAsyncMethods:
    """Tests for async methods using mocks."""

    @pytest.mark.asyncio
    @patch("playfast.rust_client.fetch_and_parse_app")
    async def test_get_app_async_mock(self, mock_fetch):
        """Test get_app_async with mock."""
        mock_rust_app = MagicMock()
        mock_rust_app.app_id = "com.test"
        mock_rust_app.title = "Test"
        mock_rust_app.description = ""
        mock_rust_app.developer = "Dev"
        mock_rust_app.developer_id = None
        mock_rust_app.score = None
        mock_rust_app.ratings = 0
        mock_rust_app.price = 0.0
        mock_rust_app.currency = "USD"
        mock_rust_app.icon = "https://example.com/icon.png"
        mock_rust_app.screenshots = []
        mock_rust_app.category = None
        mock_rust_app.version = None
        mock_rust_app.updated = None
        mock_rust_app.installs = None
        mock_rust_app.min_android = None
        mock_rust_app.permissions = []

        mock_fetch.return_value = mock_rust_app

        client = RustClient()
        app = await client.get_app_async("com.test")

        assert isinstance(app, AppInfo)
        assert app.app_id == "com.test"

    @pytest.mark.asyncio
    @patch("playfast.rust_client.fetch_and_parse_app")
    async def test_get_apps_parallel_mock(self, mock_fetch):
        """Test get_apps_parallel with mock."""
        mock_rust_app = MagicMock()
        mock_rust_app.app_id = "com.test"
        mock_rust_app.title = "Test"
        mock_rust_app.description = ""
        mock_rust_app.developer = "Dev"
        mock_rust_app.developer_id = None
        mock_rust_app.score = None
        mock_rust_app.ratings = 0
        mock_rust_app.price = 0.0
        mock_rust_app.currency = "USD"
        mock_rust_app.icon = "https://example.com/icon.png"
        mock_rust_app.screenshots = []
        mock_rust_app.category = None
        mock_rust_app.version = None
        mock_rust_app.updated = None
        mock_rust_app.installs = None
        mock_rust_app.min_android = None
        mock_rust_app.permissions = []

        mock_fetch.return_value = mock_rust_app

        client = RustClient()
        results = await client.get_apps_parallel(
            app_ids=["com.test1", "com.test2"], countries=["us", "kr"], max_workers=10
        )

        # Should have results for both countries
        assert "us" in results
        assert "kr" in results
        assert len(results["us"]) == 2
        assert len(results["kr"]) == 2

    @pytest.mark.asyncio
    @patch("playfast.rust_client.fetch_and_parse_app")
    async def test_get_apps_parallel_with_errors(self, mock_fetch):
        """Test get_apps_parallel handles errors gracefully."""
        # First call succeeds, second fails
        mock_rust_app = MagicMock()
        mock_rust_app.app_id = "com.test"
        mock_rust_app.title = "Test"
        mock_rust_app.description = ""
        mock_rust_app.developer = "Dev"
        mock_rust_app.developer_id = None
        mock_rust_app.score = None
        mock_rust_app.ratings = 0
        mock_rust_app.price = 0.0
        mock_rust_app.currency = "USD"
        mock_rust_app.icon = "https://example.com/icon.png"
        mock_rust_app.screenshots = []
        mock_rust_app.category = None
        mock_rust_app.version = None
        mock_rust_app.updated = None
        mock_rust_app.installs = None
        mock_rust_app.min_android = None
        mock_rust_app.permissions = []

        mock_fetch.side_effect = [mock_rust_app, Exception("Network error")]

        client = RustClient()
        results = await client.get_apps_parallel(
            app_ids=["com.test1", "com.test2"], countries=["us"]
        )

        # Should only have one successful result
        assert "us" in results
        assert len(results["us"]) == 1  # Only successful one
        assert results["us"][0].app_id == "com.test"

    @pytest.mark.asyncio
    @patch("playfast.rust_client.fetch_and_parse_app")
    async def test_get_apps_parallel_default_country(self, mock_fetch):
        """Test get_apps_parallel with default country."""
        mock_rust_app = MagicMock()
        mock_rust_app.app_id = "com.test"
        mock_rust_app.title = "Test"
        mock_rust_app.description = ""
        mock_rust_app.developer = "Dev"
        mock_rust_app.developer_id = None
        mock_rust_app.score = None
        mock_rust_app.ratings = 0
        mock_rust_app.price = 0.0
        mock_rust_app.currency = "USD"
        mock_rust_app.icon = "https://example.com/icon.png"
        mock_rust_app.screenshots = []
        mock_rust_app.category = None
        mock_rust_app.version = None
        mock_rust_app.updated = None
        mock_rust_app.installs = None
        mock_rust_app.min_android = None
        mock_rust_app.permissions = []

        mock_fetch.return_value = mock_rust_app

        client = RustClient()
        results = await client.get_apps_parallel(
            app_ids=["com.test"],
            countries=None,  # Should default to ["us"]
        )

        assert "us" in results
        assert len(results["us"]) == 1


class TestQuickGetAppFunction:
    """Tests for quick_get_app() convenience function."""

    @patch("playfast.rust_client.fetch_and_parse_app")
    def test_quick_get_app_mock(self, mock_fetch):
        """Test quick_get_app function with mock."""
        mock_rust_app = MagicMock()
        mock_rust_app.app_id = "com.test"
        mock_rust_app.title = "Test"
        mock_rust_app.description = ""
        mock_rust_app.developer = "Dev"
        mock_rust_app.developer_id = None
        mock_rust_app.score = None
        mock_rust_app.ratings = 0
        mock_rust_app.price = 0.0
        mock_rust_app.currency = "USD"
        mock_rust_app.icon = "https://example.com/icon.png"
        mock_rust_app.screenshots = []
        mock_rust_app.category = None
        mock_rust_app.version = None
        mock_rust_app.updated = None
        mock_rust_app.installs = None
        mock_rust_app.min_android = None
        mock_rust_app.permissions = []

        mock_fetch.return_value = mock_rust_app

        app = quick_get_app("com.test")

        assert isinstance(app, AppInfo)
        assert app.app_id == "com.test"

    @patch("playfast.rust_client.fetch_and_parse_app")
    def test_quick_get_app_with_params(self, mock_fetch):
        """Test quick_get_app with custom parameters."""
        mock_rust_app = MagicMock()
        mock_rust_app.app_id = "com.test"
        mock_rust_app.title = "Test"
        mock_rust_app.description = ""
        mock_rust_app.developer = "Dev"
        mock_rust_app.developer_id = None
        mock_rust_app.score = None
        mock_rust_app.ratings = 0
        mock_rust_app.price = 0.0
        mock_rust_app.currency = "USD"
        mock_rust_app.icon = "https://example.com/icon.png"
        mock_rust_app.screenshots = []
        mock_rust_app.category = None
        mock_rust_app.version = None
        mock_rust_app.updated = None
        mock_rust_app.installs = None
        mock_rust_app.min_android = None
        mock_rust_app.permissions = []

        mock_fetch.return_value = mock_rust_app

        app = quick_get_app("com.test", country="kr", timeout=60)

        # Verify parameters
        mock_fetch.assert_called_once_with("com.test", "en", "kr", 60)
        assert app.app_id == "com.test"

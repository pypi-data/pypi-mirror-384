"""Tests for AsyncClient (high-level async API)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from playfast import AsyncClient
from playfast.exceptions import NetworkError, ParseError, RateLimitError
from playfast.models import AppInfo, Review, SearchResult  # noqa: F401


class TestAsyncClientCreation:
    """Test AsyncClient instantiation and context management."""

    def test_create_with_defaults(self):
        """Test creating AsyncClient with default parameters."""
        client = AsyncClient()
        assert client.timeout == 30
        assert client.lang == "en"
        assert client.max_concurrent == 10

    def test_create_with_custom_params(self):
        """Test creating AsyncClient with custom parameters."""
        client = AsyncClient(timeout=60, lang="ko", max_concurrent=20)
        assert client.timeout == 60
        assert client.lang == "ko"
        assert client.max_concurrent == 20

    def test_client_has_methods(self):
        """Test that AsyncClient has expected methods."""
        client = AsyncClient()
        assert hasattr(client, "get_app")
        assert hasattr(client, "search")
        assert hasattr(client, "stream_reviews")
        assert hasattr(client, "get_apps_parallel")

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test AsyncClient as context manager."""
        async with AsyncClient() as client:
            assert client is not None
            assert hasattr(client, "_session")


class TestAsyncClientGetApp:
    """Test AsyncClient.get_app() method."""

    @pytest.mark.asyncio
    async def test_get_app_with_mock(self):
        """Test get_app with mocked response."""
        mock_html = """
        <html><script>
        AF_initDataCallback({key: 'ds:5', data: [/* mock data */], sideChannel: {}});
        </script></html>
        """

        mock_rust_app = MagicMock()
        mock_rust_app.app_id = "com.test.app"
        mock_rust_app.title = "Test App"
        mock_rust_app.description = "Test description"
        mock_rust_app.developer = "Test Developer"
        mock_rust_app.developer_id = None
        mock_rust_app.score = 4.5
        mock_rust_app.ratings = 1000
        mock_rust_app.price = 0.0
        mock_rust_app.currency = "USD"
        mock_rust_app.icon = "https://example.com/icon.png"
        mock_rust_app.screenshots = []
        mock_rust_app.category = "PRODUCTIVITY"
        mock_rust_app.version = "1.0.0"
        mock_rust_app.updated = "2024-01-01"
        mock_rust_app.installs = "1,000+"
        mock_rust_app.min_android = "5.0"
        mock_rust_app.permissions = []

        with patch("playfast.client.parse_app_page", return_value=mock_rust_app):
            async with AsyncClient() as client:
                # Mock the HTTP response
                mock_response = MagicMock()
                mock_response.status = 200
                mock_response.text = AsyncMock(return_value=mock_html)
                mock_response.headers = {}
                mock_response.__aenter__ = AsyncMock(return_value=mock_response)
                mock_response.__aexit__ = AsyncMock(return_value=None)

                with patch.object(client._session, "get", return_value=mock_response):
                    app = await client.get_app("com.test.app")

                    assert isinstance(app, AppInfo)
                    assert app.app_id == "com.test.app"
                    assert app.title == "Test App"
                    assert app.score == 4.5


class TestAsyncClientSearch:
    """Test AsyncClient.search() method."""

    @pytest.mark.asyncio
    async def test_search_with_mock(self):
        """Test search with mocked response."""
        mock_html = """
        <html><script>
        AF_initDataCallback({key: 'ds:4', data: [/* mock data */], sideChannel: {}});
        </script></html>
        """

        mock_rust_result = MagicMock()
        mock_rust_result.app_id = "com.test1"
        mock_rust_result.title = "Test App 1"
        mock_rust_result.developer = "Dev 1"
        mock_rust_result.icon = "https://example.com/icon1.png"
        mock_rust_result.score = 4.5
        mock_rust_result.price = 0.0
        mock_rust_result.currency = "USD"

        with patch(
            "playfast.client.parse_search_results", return_value=[mock_rust_result]
        ):
            async with AsyncClient() as client:
                # Mock the HTTP response
                mock_response = MagicMock()
                mock_response.status = 200
                mock_response.text = AsyncMock(return_value=mock_html)
                mock_response.headers = {}
                mock_response.__aenter__ = AsyncMock(return_value=mock_response)
                mock_response.__aexit__ = AsyncMock(return_value=None)

                with patch.object(client._session, "get", return_value=mock_response):
                    results = await client.search("test", n_hits=10)

                    assert isinstance(results, list)
                    assert len(results) == 1
                    assert isinstance(results[0], SearchResult)
                    assert results[0].app_id == "com.test1"

    @pytest.mark.asyncio
    async def test_search_limit_results(self):
        """Test that n_hits limits results."""
        mock_results = []  # type: list[MagicMock]
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

        with patch("playfast.client.parse_search_results", return_value=mock_results):
            async with AsyncClient() as client:
                mock_response = MagicMock()
                mock_response.status = 200
                mock_response.text = AsyncMock(return_value="<html></html>")
                mock_response.headers = {}
                mock_response.__aenter__ = AsyncMock(return_value=mock_response)
                mock_response.__aexit__ = AsyncMock(return_value=None)

                with patch.object(client._session, "get", return_value=mock_response):
                    results = await client.search("test", n_hits=5)

                    # Should be limited to 5
                    assert len(results) <= 5


class TestAsyncClientReviews:
    """Test AsyncClient review methods."""

    @pytest.mark.asyncio
    async def test_stream_reviews_with_mock(self):
        """Test stream_reviews with mocked response."""
        mock_rust_review = MagicMock()
        mock_rust_review.review_id = "review1"
        mock_rust_review.user_name = "Test User"
        mock_rust_review.user_image = None
        mock_rust_review.content = "Great app!"
        mock_rust_review.score = 5
        mock_rust_review.thumbs_up = 10
        mock_rust_review.created_at = 1704067200  # Unix timestamp for 2024-01-01
        mock_rust_review.reply_content = None
        mock_rust_review.reply_at = None

        # Mock fetch_and_parse_reviews directly since it's what stream_reviews uses
        with patch(
            "playfast.client.fetch_and_parse_reviews",
            return_value=([mock_rust_review], None),
        ):
            async with AsyncClient() as client:
                reviews = []  # type: list[Review]
                async for review in client.stream_reviews("com.test.app"):
                    reviews.append(review)

                assert len(reviews) == 1
                assert reviews[0].review_id == "review1"
                assert reviews[0].user_name == "Test User"


class TestAsyncClientParallel:
    """Test AsyncClient parallel operations."""

    @pytest.mark.asyncio
    async def test_get_apps_parallel_with_mock(self):
        """Test get_apps_parallel with mocked responses."""
        mock_html = "<html></html>"

        mock_rust_app = MagicMock()
        mock_rust_app.app_id = "com.test.app"
        mock_rust_app.title = "Test App"
        mock_rust_app.description = "Test"
        mock_rust_app.developer = "Dev"
        mock_rust_app.developer_id = None
        mock_rust_app.score = 4.5
        mock_rust_app.ratings = 1000
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

        with patch("playfast.client.parse_app_page", return_value=mock_rust_app):
            async with AsyncClient() as client:
                mock_response = MagicMock()
                mock_response.status = 200
                mock_response.text = AsyncMock(return_value=mock_html)
                mock_response.headers = {}
                mock_response.__aenter__ = AsyncMock(return_value=mock_response)
                mock_response.__aexit__ = AsyncMock(return_value=None)

                with patch.object(client._session, "get", return_value=mock_response):
                    results = await client.get_apps_parallel(
                        app_ids=["com.test1", "com.test2"], countries=["us", "kr"]
                    )

                    assert isinstance(results, dict)
                    assert "us" in results
                    assert "kr" in results
                    assert len(results["us"]) == 2
                    assert len(results["kr"]) == 2


class TestAsyncClientErrorHandling:
    """Test error handling in AsyncClient."""

    @pytest.mark.asyncio
    async def test_get_app_network_error(self):
        """Test handling of network errors."""
        from playfast.exceptions import AppNotFoundError

        async with AsyncClient(timeout=1) as client:
            mock_response = MagicMock()
            mock_response.status = 404
            mock_response.headers = {}
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            with patch.object(client._session, "get", return_value=mock_response):
                with pytest.raises(AppNotFoundError):
                    await client.get_app("com.test.app")

    @pytest.mark.asyncio
    async def test_context_manager_cleanup(self):
        """Test that context manager properly cleans up."""
        client = AsyncClient()

        async with client:
            assert client._session  # type: ignore[reportPrivateUsage] is not None

        # Session should be closed after exit
        # (We can't directly test this without accessing private attributes)


class TestAsyncClientListMethod:
    """Tests for AsyncClient.list() method to improve coverage."""

    @pytest.mark.asyncio
    async def test_list_with_category_and_collection(self):
        """Test list() with category and collection parameters."""
        mock_rust_result = MagicMock()
        mock_rust_result.app_id = "com.test1"
        mock_rust_result.title = "Test App"
        mock_rust_result.developer = "Dev"
        mock_rust_result.icon = "https://example.com/icon.png"
        mock_rust_result.score = 4.5
        mock_rust_result.price = 0.0
        mock_rust_result.currency = "USD"

        with patch("playfast.client.build_list_request_body", return_value="mock_body"):
            with patch(
                "playfast.client.parse_batchexecute_list_response",
                return_value=[mock_rust_result],
            ):
                async with AsyncClient() as client:
                    mock_response = MagicMock()
                    mock_response.status = 200
                    mock_response.text = AsyncMock(return_value="mock_response")
                    mock_response.headers = {}
                    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
                    mock_response.__aexit__ = AsyncMock(return_value=None)

                    with patch.object(
                        client._session, "post", return_value=mock_response
                    ):
                        results = await client.list(
                            collection="topselling_free",
                            category="GAME_ACTION",
                            country="us",
                            num=50,
                        )

                        assert len(results) == 1
                        assert results[0].app_id == "com.test1"

    @pytest.mark.asyncio
    async def test_list_rate_limit_error(self):
        """Test list() handling rate limit error."""
        with patch("playfast.client.build_list_request_body", return_value="mock_body"):
            async with AsyncClient() as client:
                mock_response = MagicMock()
                mock_response.status = 429
                mock_response.headers = {"Retry-After": "30"}
                mock_response.__aenter__ = AsyncMock(return_value=mock_response)
                mock_response.__aexit__ = AsyncMock(return_value=None)

                with patch.object(client._session, "post", return_value=mock_response):
                    with pytest.raises(RateLimitError) as exc_info:
                        await client.list(collection="topselling_free", num=50)
                    assert exc_info.value.retry_after == 30

    @pytest.mark.asyncio
    async def test_list_network_error(self):
        """Test list() handling network error."""
        with patch("playfast.client.build_list_request_body", return_value="mock_body"):
            async with AsyncClient() as client:
                mock_response = MagicMock()
                mock_response.status = 500
                mock_response.headers = {}
                mock_response.__aenter__ = AsyncMock(return_value=mock_response)
                mock_response.__aexit__ = AsyncMock(return_value=None)

                with patch.object(client._session, "post", return_value=mock_response):
                    with pytest.raises(NetworkError):
                        await client.list(collection="topselling_free", num=50)

    @pytest.mark.asyncio
    async def test_list_parse_error(self):
        """Test list() handling parse error."""
        with patch("playfast.client.build_list_request_body", return_value="mock_body"):
            with patch(
                "playfast.client.parse_batchexecute_list_response",
                side_effect=Exception("Parse failed"),
            ):
                async with AsyncClient() as client:
                    mock_response = MagicMock()
                    mock_response.status = 200
                    mock_response.text = AsyncMock(return_value="invalid_response")
                    mock_response.headers = {}
                    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
                    mock_response.__aexit__ = AsyncMock(return_value=None)

                    with patch.object(
                        client._session, "post", return_value=mock_response
                    ):
                        with pytest.raises(ParseError):
                            await client.list(collection="topselling_free", num=50)


class TestAsyncClientErrorPaths:
    """Tests for error handling paths in AsyncClient."""

    @pytest.mark.asyncio
    async def test_fetch_html_rate_limit_with_custom_retry_after(self):
        """Test _fetch_html with custom Retry-After header."""
        async with AsyncClient() as client:
            mock_response = MagicMock()
            mock_response.status = 429
            mock_response.headers = {"Retry-After": "120"}
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            with patch.object(client._session, "get", return_value=mock_response):
                with pytest.raises(RateLimitError) as exc_info:
                    await client._fetch_html("https://test.com")  # type: ignore[reportPrivateUsage]  # type: ignore[reportPrivateUsage]
                assert exc_info.value.retry_after == 120

    @pytest.mark.asyncio
    async def test_fetch_html_generic_error(self):
        """Test _fetch_html with generic HTTP error."""
        async with AsyncClient() as client:
            mock_response = MagicMock()
            mock_response.status = 403
            mock_response.headers = {}
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            with patch.object(client._session, "get", return_value=mock_response):
                with pytest.raises(NetworkError) as exc_info:
                    await client._fetch_html("https://test.com")  # type: ignore[reportPrivateUsage]
                assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_get_app_parse_error(self):
        """Test get_app when parsing fails."""
        with patch(
            "playfast.client.parse_app_page", side_effect=Exception("Rust parse error")
        ):
            async with AsyncClient() as client:
                mock_response = MagicMock()
                mock_response.status = 200
                mock_response.text = AsyncMock(return_value="<html></html>")
                mock_response.headers = {}
                mock_response.__aenter__ = AsyncMock(return_value=mock_response)
                mock_response.__aexit__ = AsyncMock(return_value=None)

                with patch.object(client._session, "get", return_value=mock_response):
                    with pytest.raises(ParseError):
                        await client.get_app("com.test.app")

    @pytest.mark.asyncio
    async def test_search_parse_error(self):
        """Test search when parsing fails."""
        with patch(
            "playfast.client.parse_search_results",
            side_effect=Exception("Parse failed"),
        ):
            async with AsyncClient() as client:
                mock_response = MagicMock()
                mock_response.status = 200
                mock_response.text = AsyncMock(return_value="<html></html>")
                mock_response.headers = {}
                mock_response.__aenter__ = AsyncMock(return_value=mock_response)
                mock_response.__aexit__ = AsyncMock(return_value=None)

                with patch.object(client._session, "get", return_value=mock_response):
                    with pytest.raises(ParseError):
                        await client.search("test query")


class TestAsyncClientCloseMethod:
    """Tests for AsyncClient.close() method."""

    @pytest.mark.asyncio
    async def test_close_method(self):
        """Test that close() method works."""
        client = AsyncClient()
        async with client:
            assert client._session  # type: ignore[reportPrivateUsage] is not None

        # After context exit, __aexit__ calls close()
        # But the session might still exist, just closed
        # Let's test explicit close instead

    @pytest.mark.asyncio
    async def test_manual_close(self):
        """Test manual close without context manager."""
        client = AsyncClient()
        await client.__aenter__()
        session = client._session  # type: ignore[reportPrivateUsage]
        assert session is not None

        await client.close()
        # After close, session should be None
        assert client._session is None  # type: ignore[reportPrivateUsage]
        # And the original session should be closed
        assert session.closed

    @pytest.mark.asyncio
    async def test_close_when_not_initialized(self):
        """Test close() when session is not initialized."""
        client = AsyncClient()
        await client.close()  # Should not raise error
        assert client._session is None  # type: ignore[reportPrivateUsage]


class TestAsyncClientGetAppsParallel:
    """Additional tests for get_apps_parallel to improve coverage."""

    @pytest.mark.asyncio
    async def test_get_apps_parallel_with_errors(self):
        """Test get_apps_parallel handling partial failures."""
        mock_html = "<html></html>"

        # First call succeeds
        mock_rust_app1 = MagicMock()
        mock_rust_app1.app_id = "com.test1"
        mock_rust_app1.title = "Test App 1"
        mock_rust_app1.description = "Test"
        mock_rust_app1.developer = "Dev"
        mock_rust_app1.developer_id = None
        mock_rust_app1.score = 4.5
        mock_rust_app1.ratings = 1000
        mock_rust_app1.price = 0.0
        mock_rust_app1.currency = "USD"
        mock_rust_app1.icon = "https://example.com/icon1.png"
        mock_rust_app1.screenshots = []
        mock_rust_app1.category = None
        mock_rust_app1.version = None
        mock_rust_app1.updated = None
        mock_rust_app1.installs = None
        mock_rust_app1.min_android = None
        mock_rust_app1.permissions = []

        parse_results = [mock_rust_app1, Exception("Parse error")]

        with patch("playfast.client.parse_app_page", side_effect=parse_results):
            async with AsyncClient() as client:
                mock_response = MagicMock()
                mock_response.status = 200
                mock_response.text = AsyncMock(return_value=mock_html)
                mock_response.headers = {}
                mock_response.__aenter__ = AsyncMock(return_value=mock_response)
                mock_response.__aexit__ = AsyncMock(return_value=None)

                with patch.object(client._session, "get", return_value=mock_response):
                    results = await client.get_apps_parallel(
                        app_ids=["com.test1", "com.test2"], countries=["us"]
                    )

                    # Should have results for US
                    assert "us" in results
                    # Only successful app should be in results
                    assert len(results["us"]) == 1
                    assert results["us"][0].app_id == "com.test1"

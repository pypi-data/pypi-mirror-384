"""Pytest configuration and shared fixtures."""

import json
from pathlib import Path

import pytest

from playfast import Category, Collection, RustClient
from playfast.models import AppInfo, Review, SearchResult


@pytest.fixture
def rust_client() -> RustClient:
    """Create a RustClient instance for testing."""
    return RustClient(timeout=30, lang="en")


@pytest.fixture
def mock_app_info() -> AppInfo:
    """Create a mock AppInfo for testing."""
    from pydantic import HttpUrl

    return AppInfo(
        app_id="com.test.app",
        title="Test App",
        description="This is a test app",
        developer="Test Developer",
        developer_id="test_dev",
        score=4.5,
        ratings=1000,
        price=0.0,
        currency="USD",
        icon=HttpUrl("https://example.com/icon.png"),
        screenshots=[HttpUrl("https://example.com/screen1.png")],
        category="PRODUCTIVITY",
        version="1.0.0",
        updated="2024-01-01",
        installs="1,000+",
        min_android="5.0",
        permissions=[],
    )


@pytest.fixture
def mock_review() -> Review:
    """Create a mock Review for testing."""
    from datetime import datetime

    from pydantic import HttpUrl

    return Review(
        review_id="review123",
        user_name="Test User",
        user_image=HttpUrl("https://example.com/avatar.jpg"),
        content="Great app! Highly recommended.",
        score=5,
        thumbs_up=42,
        created_at=datetime(2024, 1, 15),
        reply_content="Thank you!",
        reply_at=datetime(2024, 1, 16),
    )


@pytest.fixture
def mock_search_result() -> SearchResult:
    """Create a mock SearchResult for testing."""
    from pydantic import HttpUrl

    return SearchResult(
        app_id="com.test.app",
        title="Test App",
        developer="Test Developer",
        icon=HttpUrl("https://example.com/icon.png"),
        score=4.5,
        price=0.0,
        currency="USD",
    )


@pytest.fixture
def sample_html_with_json() -> str:
    """Sample HTML with embedded JSON data for testing parsers."""
    return """
    <html>
        <script>
            AF_initDataCallback({
                key: 'ds:5',
                data: [[
                    [
                        null, null, null, null, null, null, null,
                        [[null, null, null, [null, null, [["$4.99"], null, ["USD"]]]]],
                        null, null, null, null,
                        [
                            null,
                            [null, null, [null, null, "https://example.com/icon.png"]],
                            null, null, null, null,
                            [null, [null, [null, 4.5, 1000]]],
                            null, null, null,
                            ["Test App Description"],
                            null,
                            [
                                null,
                                [[null, null, [null, null, "https://example.com/screen1.png"]]],
                                null, null, null,
                                ["Test Developer", null, null, null, null, ["test_dev"]],
                                ["PRODUCTIVITY"],
                                null,
                                ["2024-01-01"],
                                ["1,000+"]
                            ]
                        ]
                    ]
                ]],
                sideChannel: {}
            });
        </script>
    </html>
    """


@pytest.fixture
def all_categories() -> list[Category]:
    """List of all available categories."""
    return [
        Category.GAME_ACTION,
        Category.GAME_PUZZLE,
        Category.PRODUCTIVITY,
        Category.SOCIAL,
        Category.ENTERTAINMENT,
    ]


@pytest.fixture
def all_collections() -> list[Collection]:
    """List of all available collections."""
    return [
        Collection.TOP_FREE,
        Collection.TOP_PAID,
        Collection.TOP_GROSSING,
        Collection.TOP_NEW_FREE,
        Collection.TOP_NEW_PAID,
    ]


# ==============================================================================
# Doctest Support: Mock Client for Documentation Testing
# ==============================================================================


class MockRustClient:
    """Mock RustClient that returns sample data without network calls.

    This mock client is injected into doctest namespace to enable
    documentation examples to run without actual network requests.
    """

    def __init__(self, timeout: int = 30, lang: str = "en") -> None:
        """Initialize mock client with sample data from fixtures.

        Args:
            timeout: Request timeout (ignored in mock)
            lang: Language code (ignored in mock)

        """
        self.timeout = timeout
        self.lang = lang

        fixtures_dir = Path(__file__).parent.parent / "fixtures"

        # Load sample data
        with (fixtures_dir / "sample_app.json").open() as f:
            app_data = json.load(f)
            from pydantic import HttpUrl

            self._sample_app = AppInfo(
                **{
                    **app_data,
                    "icon": HttpUrl(app_data["icon"]),
                    "screenshots": [HttpUrl(url) for url in app_data["screenshots"]],
                    "permissions": [
                        {"group": p["group"], "permissions": p["permissions"]}
                        for p in app_data["permissions"]
                    ],
                }
            )

        with (fixtures_dir / "sample_reviews.json").open() as f:
            reviews_data = json.load(f)
            from datetime import datetime

            from pydantic import HttpUrl

            self._sample_reviews = [
                Review(
                    **{
                        **r,
                        "user_image": HttpUrl(r["user_image"])
                        if r["user_image"]
                        else None,
                        "created_at": datetime.fromtimestamp(r["created_at"]),
                        "reply_at": datetime.fromtimestamp(r["reply_at"])
                        if r["reply_at"]
                        else None,
                    }
                )
                for r in reviews_data
            ]

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, *args):
        """Context manager exit."""

    def get_app(self, app_id: str, lang: str = "en", country: str = "us") -> AppInfo:
        """Return sample app data."""
        return self._sample_app

    def get_reviews(
        self,
        app_id: str,
        lang: str = "en",
        country: str = "us",
        sort: int = 1,
        continuation_token: str | None = None,
    ) -> tuple[list[Review], str | None]:
        """Return sample reviews."""
        return self._sample_reviews, None

    def search(
        self, query: str, lang: str = "en", country: str = "us", n_hits: int = 30
    ) -> list[SearchResult]:
        """Return sample search results."""
        from pydantic import HttpUrl

        return [
            SearchResult(
                app_id="com.spotify.music",
                title="Spotify: Music and Podcasts",
                developer="Spotify AB",
                icon=HttpUrl("https://play-lh.googleusercontent.com/example.png"),
                score=4.5,
                price=0.0,
                currency="USD",
            )
        ]

    def list(
        self,
        collection: str,
        category: str | None = None,
        lang: str = "en",
        country: str = "us",
        num: int = 100,
    ) -> list[SearchResult]:
        """Return sample category/collection list."""
        return self.search("", lang, country, num)

    # Async methods
    async def get_app_async(
        self, app_id: str, lang: str | None = None, country: str = "us"
    ) -> AppInfo:
        """Return sample app data (async version)."""
        return self._sample_app

    async def get_apps_parallel(
        self,
        app_ids: list[str],
        countries: list[str] | None = None,
        lang: str | None = None,
        max_workers: int = 50,
    ) -> dict[str, list[AppInfo]]:
        """Return sample apps grouped by country."""
        countries_list = countries if countries is not None else ["us"]
        return {country: [self._sample_app] for country in countries_list}


class MockAsyncClient:
    """Mock AsyncClient that returns sample data without network calls."""

    def __init__(self, **kwargs) -> None:
        """Initialize mock async client with sample data from fixtures."""
        fixtures_dir = Path(__file__).parent.parent / "fixtures"

        # Load sample data
        with (fixtures_dir / "sample_app.json").open() as f:
            app_data = json.load(f)
            from pydantic import HttpUrl

            self._sample_app = AppInfo(
                **{
                    **app_data,
                    "icon": HttpUrl(app_data["icon"]),
                    "screenshots": [HttpUrl(url) for url in app_data["screenshots"]],
                    "permissions": [
                        {"group": p["group"], "permissions": p["permissions"]}
                        for p in app_data["permissions"]
                    ],
                }
            )

        with (fixtures_dir / "sample_reviews.json").open() as f:
            reviews_data = json.load(f)
            from datetime import datetime

            from pydantic import HttpUrl

            self._sample_reviews = [
                Review(
                    **{
                        **r,
                        "user_image": HttpUrl(r["user_image"])
                        if r["user_image"]
                        else None,
                        "created_at": datetime.fromtimestamp(r["created_at"]),
                        "reply_at": datetime.fromtimestamp(r["reply_at"])
                        if r["reply_at"]
                        else None,
                    }
                )
                for r in reviews_data
            ]

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args):
        """Async context manager exit."""

    async def get_app(
        self, app_id: str, lang: str = "en", country: str = "us"
    ) -> AppInfo:
        """Return sample app data (async)."""
        return self._sample_app

    async def get_apps_parallel(
        self,
        app_ids: list[str],
        countries: list[str] | None = None,
        lang: str | None = None,
    ) -> dict[str, list[AppInfo]]:
        """Return sample apps grouped by country."""
        countries_list = countries or ["us"]
        return {
            country: [self._sample_app for _ in app_ids] for country in countries_list
        }

    async def stream_reviews(
        self,
        app_id: str,
        lang: str | None = None,
        country: str = "us",
        sort: int = 1,
        max_pages: int | None = None,
    ):
        """Yield sample reviews (async generator)."""
        # Yield reviews only once (simulating single page)
        for review in self._sample_reviews:
            yield review
        # Don't continue - single page only

    async def search(
        self,
        query: str,
        lang: str | None = None,
        country: str = "us",
        n_hits: int = 30,
    ) -> list[SearchResult]:
        """Return sample search results."""
        from pydantic import HttpUrl

        return [
            SearchResult(
                app_id="com.spotify.music",
                title="Spotify: Music and Podcasts",
                developer="Spotify AB",
                icon=HttpUrl("https://play-lh.googleusercontent.com/example.png"),
                score=4.5,
                price=0.0,
                currency="USD",
            )
        ]

    async def list(
        self,
        collection: str,
        category: str | None = None,
        lang: str | None = None,
        country: str = "us",
        num: int = 100,
    ) -> list[SearchResult]:
        """Return sample category/collection list."""
        return await self.search("", lang, country, num)


@pytest.fixture(autouse=True)
def add_doctest_namespace(doctest_namespace: dict) -> None:
    """Monkey-patch clients with mock versions for documentation testing.

    This fixture replaces the RustClient and AsyncClient classes with mock
    versions during doctest execution, allowing documentation examples to run
    without network calls while keeping the docstrings showing real usage patterns.
    """
    # Monkey-patch: Replace clients with mocks
    # This makes docstrings show real usage (RustClient(), AsyncClient()) but use mocks during tests
    doctest_namespace["RustClient"] = MockRustClient
    doctest_namespace["AsyncClient"] = MockAsyncClient

    # Also provide direct access for convenience
    doctest_namespace["mock_client"] = MockRustClient()

    # Add helper modules
    import asyncio

    doctest_namespace["asyncio"] = asyncio

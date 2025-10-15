"""Pytest configuration and shared fixtures."""

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

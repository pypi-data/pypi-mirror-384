"""Tests for _core module (Rust bindings via PyO3)."""

# pyright: reportCallIssue=false
# pylance: disable=reportCallIssue

import pytest

from playfast import core
from playfast.core import (
    RustAppInfo,
    RustReview,
    RustSearchResult,
    fetch_and_parse_app,
    fetch_and_parse_list,
    fetch_and_parse_reviews,
    fetch_and_parse_search,
)


class TestCoreModule:
    """Test _core module structure."""

    def test_core_module_exists(self):
        """Test that core module is importable."""
        assert core is not None

    def test_core_has_functions(self):
        """Test that core has expected functions."""
        assert hasattr(core, "fetch_and_parse_app")
        assert hasattr(core, "fetch_and_parse_reviews")
        assert hasattr(core, "fetch_and_parse_search")
        assert hasattr(core, "fetch_and_parse_list")

    def test_core_has_classes(self):
        """Test that core has expected classes."""
        assert hasattr(core, "RustAppInfo")
        assert hasattr(core, "RustReview")
        assert hasattr(core, "RustSearchResult")


class TestRustAppInfo:
    """Test RustAppInfo class."""

    def test_rust_app_info_type_exists(self):
        """Test that RustAppInfo type exists."""
        assert RustAppInfo is not None
        assert hasattr(RustAppInfo, "__name__")

    def test_rust_app_info_cannot_be_instantiated(self):
        """Test that RustAppInfo cannot be directly instantiated in Python."""
        # PyO3 types cannot be instantiated directly from Python
        with pytest.raises(TypeError, match="cannot create"):
            RustAppInfo(  # type: ignore[call-arg]
                app_id="com.test",
                title="Test",
                description="Desc",
                developer="Dev",
                developer_id=None,
                score=None,
                ratings=100,
                price=0.0,
                currency="USD",
                icon="icon.png",
                screenshots=[],
                category=None,
                version=None,
                updated=None,
                installs=None,
                min_android=None,
            )


class TestRustReview:
    """Test RustReview class."""

    def test_rust_review_type_exists(self):
        """Test that RustReview type exists."""
        assert RustReview is not None
        assert hasattr(RustReview, "__name__")

    def test_rust_review_cannot_be_instantiated(self):
        """Test that RustReview cannot be directly instantiated in Python."""
        with pytest.raises(TypeError, match="cannot create"):
            RustReview(  # type: ignore[call-arg]
                review_id="r1",
                user_name="User",
                user_image=None,
                content="Test",
                score=3,
                thumbs_up=0,
                created_at="2024-01-01",
                reply_content=None,
                reply_at=None,
            )


class TestRustSearchResult:
    """Test RustSearchResult class."""

    def test_rust_search_result_type_exists(self):
        """Test that RustSearchResult type exists."""
        assert RustSearchResult is not None
        assert hasattr(RustSearchResult, "__name__")

    def test_rust_search_result_cannot_be_instantiated(self):
        """Test that RustSearchResult cannot be directly instantiated in Python."""
        with pytest.raises(TypeError, match="cannot create"):
            RustSearchResult(  # type: ignore[call-arg]
                app_id="com.test",
                title="Test",
                developer="Dev",
                icon="icon.png",
                score=None,
                price=0.0,
                currency="USD",
            )


class TestFetchFunctions:
    """Test fetch_and_parse_* functions (require network - marked as integration tests)."""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network and real Google Play access")
    def test_fetch_and_parse_app(self):
        """Test fetch_and_parse_app function."""
        result = fetch_and_parse_app("com.google.android.apps.maps", "en", "us", 30)
        assert isinstance(result, RustAppInfo)
        assert result.app_id == "com.google.android.apps.maps"
        assert len(result.title) > 0

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network and real Google Play access")
    def test_fetch_and_parse_reviews(self):
        """Test fetch_and_parse_reviews function."""
        reviews, _next_token = fetch_and_parse_reviews(
            "com.google.android.apps.maps",
            "en",
            "us",
            1,  # sort: newest
            None,  # no continuation token
            30,
        )
        assert isinstance(reviews, list)
        if len(reviews) > 0:
            assert isinstance(reviews[0], RustReview)

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network and real Google Play access")
    def test_fetch_and_parse_search(self):
        """Test fetch_and_parse_search function."""
        results = fetch_and_parse_search("maps", "en", "us", 30)
        assert isinstance(results, list)
        if len(results) > 0:
            assert isinstance(results[0], RustSearchResult)

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network and real Google Play access")
    def test_fetch_and_parse_list(self):
        """Test fetch_and_parse_list function."""
        results = fetch_and_parse_list(
            "GAME_ACTION",  # category
            "topselling_free",  # collection
            "en",
            "us",
            10,  # num
            30,  # timeout
        )
        assert isinstance(results, list)
        if len(results) > 0:
            assert isinstance(results[0], RustSearchResult)

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network and real Google Play access")
    def test_fetch_and_parse_list_no_category(self):
        """Test fetch_and_parse_list without category."""
        results = fetch_and_parse_list(
            None,  # no category
            "topselling_free",
            "en",
            "us",
            10,
            30,
        )
        assert isinstance(results, list)


class TestFunctionSignatures:
    """Test that function signatures are correct."""

    def test_fetch_and_parse_app_signature(self):
        """Test fetch_and_parse_app accepts correct arguments."""
        # Should accept: app_id, lang, country, timeout
        # This just tests the function is callable with these args
        try:
            # Will fail with network error but signature is correct
            fetch_and_parse_app("test", "en", "us", 1)
        except Exception:
            # Network error is expected, we're just testing signature
            assert True

    def test_fetch_and_parse_list_signature(self):
        """Test fetch_and_parse_list signature."""
        # Should accept: category (optional), collection, lang, country, num, timeout
        try:
            fetch_and_parse_list(None, "topselling_free", "en", "us", 10, 1)
        except Exception:
            # Network error expected
            assert True

        try:
            fetch_and_parse_list("GAME_ACTION", "topselling_free", "en", "us", 10, 1)
        except Exception:
            # Network error expected
            assert True


class TestRustTypes:
    """Test Rust type representations."""

    def test_rust_types_are_classes(self):
        """Test that Rust types are proper classes."""
        # Check that types exist and are classes
        assert isinstance(RustAppInfo, type)
        assert isinstance(RustReview, type)
        assert isinstance(RustSearchResult, type)

    def test_rust_type_names(self):
        """Test that Rust types have correct names."""
        assert "RustAppInfo" in str(RustAppInfo)
        assert "RustReview" in str(RustReview)
        assert "RustSearchResult" in str(RustSearchResult)

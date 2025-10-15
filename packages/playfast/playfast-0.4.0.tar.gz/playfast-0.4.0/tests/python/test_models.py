"""Tests for Pydantic models (AppInfo, Review, SearchResult)."""

from datetime import datetime

from pydantic import HttpUrl, ValidationError
import pytest

from playfast.models import AppInfo, Permission, Review, SearchResult


class TestAppInfo:
    """Tests for AppInfo Pydantic model."""

    def test_app_info_creation(self, mock_app_info: AppInfo) -> None:
        """Test creating AppInfo instance."""
        app = mock_app_info
        assert app.app_id == "com.test.app"
        assert app.title == "Test App"
        assert app.score == 4.5
        assert app.is_free is True

    def test_app_info_is_free(self) -> None:
        """Test is_free computed property."""
        free_app = AppInfo(
            app_id="com.free",
            title="Free App",
            description="",
            developer="Dev",
            developer_id=None,
            score=None,
            ratings=0,
            price=0.0,
            currency="USD",
            icon=HttpUrl("https://example.com/icon.png"),
            screenshots=[],
            category=None,
            version=None,
            updated=None,
            installs=None,
            min_android=None,
            permissions=[],
        )
        assert free_app.is_free is True

        paid_app = AppInfo(
            app_id="com.paid",
            title="Paid App",
            description="",
            developer="Dev",
            developer_id=None,
            score=None,
            ratings=0,
            price=4.99,
            currency="USD",
            icon=HttpUrl("https://example.com/icon.png"),
            screenshots=[],
            category=None,
            version=None,
            updated=None,
            installs=None,
            min_android=None,
            permissions=[],
        )
        assert paid_app.is_free is False

    def test_app_info_validation_required_fields(self) -> None:
        """Test that required fields are validated."""
        with pytest.raises(ValidationError):
            AppInfo()  # type: ignore[call-arg]

    def test_app_info_optional_fields(self) -> None:
        """Test that optional fields can be None."""
        app = AppInfo(
            app_id="com.test",
            title="Test",
            description="",
            developer="Dev",
            developer_id=None,
            score=None,
            ratings=0,
            price=0.0,
            currency="USD",
            icon=HttpUrl("https://example.com/icon.png"),
            screenshots=[],
            category=None,
            version=None,
            updated=None,
            installs=None,
            min_android=None,
            permissions=[],
        )
        assert app.developer_id is None
        assert app.score is None
        assert app.category is None

    def test_app_info_from_rust_method_exists(self) -> None:
        """Test that from_rust method exists on AppInfo."""
        assert hasattr(AppInfo, "from_rust")
        assert callable(AppInfo.from_rust)


class TestReview:
    """Tests for Review Pydantic model."""

    def test_review_creation(self, mock_review: Review) -> None:
        """Test creating Review instance."""
        review = mock_review
        assert review.review_id == "review123"
        assert review.user_name == "Test User"
        assert review.score == 5
        assert review.thumbs_up == 42

    def test_review_is_positive(self) -> None:
        """Test is_positive helper method."""
        positive = Review(
            review_id="r1",
            user_name="User",
            user_image=None,
            content="Great!",
            score=5,
            thumbs_up=10,
            created_at=datetime(2024, 1, 1),
            reply_content=None,
            reply_at=None,
        )
        assert positive.is_positive() is True

        negative = Review(
            review_id="r2",
            user_name="User",
            user_image=None,
            content="Bad",
            score=2,
            thumbs_up=0,
            created_at=datetime(2024, 1, 1),
            reply_content=None,
            reply_at=None,
        )
        assert negative.is_positive() is False

    def test_review_validation(self) -> None:
        """Test review validation."""
        with pytest.raises(ValidationError):
            Review()  # type: ignore[call-arg]

    def test_review_from_rust_method_exists(self) -> None:
        """Test that from_rust method exists on Review."""
        assert hasattr(Review, "from_rust")
        assert callable(Review.from_rust)


class TestSearchResult:
    """Tests for SearchResult Pydantic model."""

    def test_search_result_creation(self, mock_search_result: SearchResult) -> None:
        """Test creating SearchResult instance."""
        result = mock_search_result
        assert result.app_id == "com.test.app"
        assert result.title == "Test App"
        assert result.developer == "Test Developer"

    def test_search_result_validation(self) -> None:
        """Test search result validation."""
        with pytest.raises(ValidationError):
            SearchResult()  # type: ignore[call-arg]

    def test_search_result_optional_score(self) -> None:
        """Test that score is optional."""
        result = SearchResult(
            app_id="com.test",
            title="Test",
            developer="Dev",
            icon=HttpUrl("https://example.com/icon.png"),
            score=None,
            price=0.0,
            currency="USD",
        )
        assert result.score is None

    def test_search_result_from_rust_method_exists(self) -> None:
        """Test that from_rust method exists on SearchResult."""
        assert hasattr(SearchResult, "from_rust")
        assert callable(SearchResult.from_rust)


class TestPermissionModel:
    """Tests for Permission model."""

    def test_permission_creation(self) -> None:
        """Test creating Permission instance."""
        perm = Permission(group="Location", permissions=["GPS", "Network"])
        assert perm.group == "Location"
        assert len(perm.permissions) == 2

    def test_permission_len(self) -> None:
        """Test __len__ method on Permission."""
        perm = Permission(group="Location", permissions=["GPS", "Network", "WiFi"])
        assert len(perm) == 3

    def test_permission_validation_empty_list(self) -> None:
        """Test that empty permissions list is rejected."""
        with pytest.raises(ValidationError):
            Permission(group="Test", permissions=[])


class TestModelInteroperability:
    """Test interoperability between Python and Rust models."""

    def test_from_rust_methods_exist(self) -> None:
        """Test that all models have from_rust methods."""
        assert hasattr(AppInfo, "from_rust")
        assert hasattr(Review, "from_rust")
        assert hasattr(SearchResult, "from_rust")

    def test_model_conversion_concept(self) -> None:
        """Test that conversion from Rust types is conceptually supported."""
        assert callable(AppInfo.from_rust)
        assert callable(Review.from_rust)
        assert callable(SearchResult.from_rust)

"""Tests for __init__.py module exports and main function."""

from __future__ import annotations

from typing import TYPE_CHECKING

import playfast


if TYPE_CHECKING:
    import pytest


class TestModuleMetadata:
    """Tests for module metadata."""

    def test_version_exists(self):
        """Test that __version__ is defined and follows semver format."""
        assert hasattr(playfast, "__version__")
        assert isinstance(playfast.__version__, str)
        # Check version follows semantic versioning (X.Y.Z)
        parts = playfast.__version__.split(".")
        assert len(parts) == 3, "Version should be in X.Y.Z format"
        assert all(part.isdigit() for part in parts), "Version parts should be numeric"

    def test_author_exists(self):
        """Test that __author__ is defined."""
        assert hasattr(playfast, "__author__")
        assert isinstance(playfast.__author__, str)
        assert len(playfast.__author__) > 0

    def test_license_exists(self):
        """Test that __license__ is defined."""
        assert hasattr(playfast, "__license__")
        assert playfast.__license__ == "MIT"


class TestModuleExports:
    """Tests for module-level exports."""

    def test_clients_exported(self):
        """Test that client classes are exported."""
        assert hasattr(playfast, "AsyncClient")
        assert hasattr(playfast, "RustClient")
        assert hasattr(playfast, "quick_get_app")

    def test_models_exported(self):
        """Test that model classes are exported."""
        assert hasattr(playfast, "AppInfo")
        assert hasattr(playfast, "Review")
        assert hasattr(playfast, "SearchResult")
        assert hasattr(playfast, "Permission")

    def test_exceptions_exported(self):
        """Test that exception classes are exported."""
        assert hasattr(playfast, "PlayfastError")
        assert hasattr(playfast, "AppNotFoundError")
        assert hasattr(playfast, "RateLimitError")
        assert hasattr(playfast, "ParseError")
        assert hasattr(playfast, "NetworkError")
        assert hasattr(playfast, "ValidationError")
        assert hasattr(playfast, "TimeoutError")

    def test_constants_exported(self):
        """Test that constant enums are exported."""
        assert hasattr(playfast, "Category")
        assert hasattr(playfast, "Collection")
        assert hasattr(playfast, "Age")
        assert hasattr(playfast, "Country")

    def test_country_functions_exported(self):
        """Test that country helper functions are exported."""
        assert hasattr(playfast, "get_countries")
        assert hasattr(playfast, "get_country_by_code")
        assert hasattr(playfast, "get_unique_countries")
        assert hasattr(playfast, "get_representative_country")
        assert hasattr(playfast, "is_unique_region")
        assert hasattr(playfast, "get_countries_in_region")

    def test_core_module_exported(self):
        """Test that core module is exported."""
        assert hasattr(playfast, "core")


class TestAllExports:
    """Tests for __all__ definition."""

    def test_all_defined(self):
        """Test that __all__ is defined."""
        assert hasattr(playfast, "__all__")
        assert isinstance(playfast.__all__, list)

    def test_all_exports_are_accessible(self):
        """Test that all items in __all__ are actually accessible."""
        for name in playfast.__all__:
            assert hasattr(playfast, name), f"{name} in __all__ but not accessible"

    def test_key_items_in_all(self):
        """Test that key items are in __all__."""
        required_exports = [
            "AsyncClient",
            "RustClient",
            "AppInfo",
            "Review",
            "SearchResult",
            "Category",
            "Collection",
            "PlayfastError",
        ]
        for item in required_exports:
            assert item in playfast.__all__, f"{item} should be in __all__"


class TestMainFunction:
    """Tests for main() CLI entry point."""

    def test_main_exists(self):
        """Test that main function exists."""
        assert hasattr(playfast, "main")
        assert callable(playfast.main)

    def test_main_runs_without_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that main() runs without error."""
        playfast.main()
        captured = capsys.readouterr()
        assert "Playfast" in captured.out
        assert f"v{playfast.__version__}" in captured.out

    def test_main_shows_client_options(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that main() shows client options."""
        playfast.main()
        captured = capsys.readouterr()
        assert "RustClient" in captured.out
        assert "AsyncClient" in captured.out

    def test_main_shows_version(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that main() shows version."""
        playfast.main()
        captured = capsys.readouterr()
        assert f"v{playfast.__version__}" in captured.out


class TestImportStructure:
    """Tests for import structure integrity."""

    def test_can_import_from_submodules(self):
        """Test that imports from submodules work."""
        from playfast.client import AsyncClient
        from playfast.constants import Category
        from playfast.exceptions import PlayfastError
        from playfast.models import AppInfo

        assert AsyncClient is not None
        assert AppInfo is not None
        assert PlayfastError is not None
        assert Category is not None

    def test_top_level_imports_match_submodule_imports(self):
        """Test that top-level imports are same objects as submodule imports."""
        from playfast.client import AsyncClient as DirectAsyncClient
        from playfast.models import AppInfo as DirectAppInfo

        assert playfast.AsyncClient is DirectAsyncClient
        assert playfast.AppInfo is DirectAppInfo

    def test_circular_import_safe(self):
        """Test that circular imports don't occur."""
        # If this test runs, circular imports are not present
        import playfast.client
        import playfast.constants
        import playfast.exceptions
        import playfast.models

        assert playfast.client is not None
        assert playfast.models is not None
        assert playfast.exceptions is not None
        assert playfast.constants is not None

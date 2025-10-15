"""Tests for playfast.constants module (Category, Collection, Age enums)."""

from playfast.constants import Age, Category, Collection, age, category, collection


class TestCategory:
    """Tests for Category enum."""

    def test_category_game_values(self):
        """Test game category values."""
        assert Category.GAME == "GAME"
        assert Category.GAME_ACTION == "GAME_ACTION"
        assert Category.GAME_PUZZLE == "GAME_PUZZLE"
        assert Category.GAME_RACING == "GAME_RACING"

    def test_category_app_values(self):
        """Test app category values."""
        assert Category.PRODUCTIVITY == "PRODUCTIVITY"
        assert Category.SOCIAL == "SOCIAL"
        assert Category.ENTERTAINMENT == "ENTERTAINMENT"
        assert Category.BUSINESS == "BUSINESS"

    def test_category_is_string_enum(self):
        """Test that Category values are strings."""
        assert isinstance(Category.GAME_ACTION.value, str)
        assert isinstance(Category.PRODUCTIVITY.value, str)

    def test_category_equality(self):
        """Test Category equality comparisons."""
        assert Category.GAME_ACTION == "GAME_ACTION"
        assert Category.GAME_ACTION != "GAME_PUZZLE"

    def test_category_all_members(self):
        """Test that all expected categories exist."""
        expected_categories = [
            "GAME",
            "GAME_ACTION",
            "GAME_ADVENTURE",
            "GAME_ARCADE",
            "PRODUCTIVITY",
            "SOCIAL",
            "ENTERTAINMENT",
            "BUSINESS",
            "TOOLS",
            "FINANCE",
            "HEALTH_AND_FITNESS",
        ]

        for cat in expected_categories:
            assert hasattr(Category, cat), f"Category.{cat} should exist"

    def test_category_backward_compatibility(self):
        """Test backward compatibility with lowercase alias."""
        assert category == Category
        assert category.GAME_ACTION == Category.GAME_ACTION


class TestCollection:
    """Tests for Collection enum."""

    def test_collection_values(self):
        """Test collection values match expected strings."""
        assert Collection.TOP_FREE == "topselling_free"
        assert Collection.TOP_PAID == "topselling_paid"
        assert Collection.TOP_GROSSING == "topgrossing"
        assert Collection.TOP_NEW_FREE == "topselling_new_free"
        assert Collection.TOP_NEW_PAID == "topselling_new_paid"

    def test_collection_is_string_enum(self):
        """Test that Collection values are strings."""
        assert isinstance(Collection.TOP_FREE.value, str)
        assert isinstance(Collection.TOP_PAID.value, str)

    def test_collection_all_members(self):
        """Test that all expected collections exist."""
        expected_collections = [
            "TOP_FREE",
            "TOP_PAID",
            "TOP_GROSSING",
            "TOP_NEW_FREE",
            "TOP_NEW_PAID",
            "MOVERS_SHAKERS",
        ]

        for coll in expected_collections:
            assert hasattr(Collection, coll), f"Collection.{coll} should exist"

    def test_collection_backward_compatibility(self):
        """Test backward compatibility with lowercase alias."""
        assert collection == Collection
        assert collection.TOP_FREE == Collection.TOP_FREE


class TestAge:
    """Tests for Age enum."""

    def test_age_values(self):
        """Test age range values."""
        assert Age.FIVE_UNDER == "AGE_RANGE1"
        assert Age.SIX_EIGHT == "AGE_RANGE2"
        assert Age.NINE_UP == "AGE_RANGE3"

    def test_age_is_string_enum(self):
        """Test that Age values are strings."""
        assert isinstance(Age.FIVE_UNDER.value, str)

    def test_age_backward_compatibility(self):
        """Test backward compatibility with lowercase alias."""
        assert age == Age
        assert age.FIVE_UNDER == Age.FIVE_UNDER


class TestEnumUsage:
    """Test practical usage of enums."""

    def test_category_in_string_context(self):
        """Test that categories work as strings."""
        cat = Category.GAME_ACTION
        url = f"/store/apps/category/{cat}"
        assert url == "/store/apps/category/GAME_ACTION"

    def test_collection_in_string_context(self):
        """Test that collections work as strings."""
        coll = Collection.TOP_FREE
        url = f"/store/apps/collection/{coll}"
        assert url == "/store/apps/collection/topselling_free"

    def test_enum_comparison(self):
        """Test enum comparisons."""
        assert Category.GAME_ACTION == Category.GAME_ACTION
        assert Category.GAME_ACTION != Category.GAME_PUZZLE
        assert Collection.TOP_FREE != Collection.TOP_PAID

    def test_enum_iteration(self):
        """Test that we can iterate over enum members."""
        categories = list(Category)
        assert len(categories) > 0
        assert Category.GAME_ACTION in categories

        collections = list(Collection)
        assert len(collections) == 6  # Should have exactly 6 collections
        assert Collection.TOP_FREE in collections

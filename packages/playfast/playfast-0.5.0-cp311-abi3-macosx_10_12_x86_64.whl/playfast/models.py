"""Pydantic models for Playfast - Rich validation and type safety.

These models provide comprehensive validation, serialization, and documentation
for Google Play Store data. They convert Rust DTOs into fully-validated Python objects.
"""

from datetime import datetime
from enum import Enum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class AppCategory(str, Enum):
    """Google Play app categories."""

    GAME = "GAME"
    SOCIAL = "SOCIAL"
    PRODUCTIVITY = "PRODUCTIVITY"
    ENTERTAINMENT = "ENTERTAINMENT"
    COMMUNICATION = "COMMUNICATION"
    TOOLS = "TOOLS"
    EDUCATION = "EDUCATION"
    LIFESTYLE = "LIFESTYLE"
    FINANCE = "FINANCE"
    HEALTH = "HEALTH"
    SHOPPING = "SHOPPING"
    NEWS = "NEWS"
    TRAVEL = "TRAVEL"
    PHOTOGRAPHY = "PHOTOGRAPHY"
    MUSIC = "MUSIC"
    VIDEO = "VIDEO"
    SPORTS = "SPORTS"
    WEATHER = "WEATHER"
    OTHER = "OTHER"


class Permission(BaseModel):
    """App permission group.

    Represents a group of related permissions (e.g., Location, Camera)
    with the specific permissions requested by the app.

    Examples:
        >>> perm = Permission(
        ...     group="Location",
        ...     permissions=[
        ...         "approximate location (network-based)",
        ...         "precise location (GPS and network-based)",
        ...     ],
        ... )
        >>> perm.group
        'Location'
        >>> len(perm.permissions)
        2

    """

    group: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Permission group name (e.g., 'Location', 'Camera')",
    )

    permissions: list[str] = Field(
        default_factory=list,
        max_length=50,
        description="List of specific permissions in this group",
    )

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, v: list[str]) -> list[str]:
        """Ensure permissions list is not empty and items are valid."""
        if not v:
            msg = "Permissions list cannot be empty"
            raise ValueError(msg)
        # Strip whitespace from each permission
        return [p.strip() for p in v if p.strip()]

    def __len__(self) -> int:
        """Return number of permissions in this group."""
        return len(self.permissions)

    @classmethod
    def from_rust(cls, rust_obj: Any) -> "Permission":
        """Create Permission from Rust DTO.

        Args:
            rust_obj: RustPermission object from the Rust core

        Returns:
            Permission: Validated Pydantic model

        Raises:
            ValidationError: If data doesn't meet validation requirements

        """
        return cls(group=rust_obj.group, permissions=list(rust_obj.permissions))


class AppInfo(BaseModel):
    """Google Play app information with full validation.

    All fields are automatically validated by Pydantic. This model is
    created from Rust DTOs and provides rich Python-side functionality.

    Examples:
        >>> app = AppInfo(
        ...     app_id="com.spotify.music",
        ...     title="Spotify",
        ...     developer="Spotify Ltd.",
        ...     score=4.5,
        ...     ratings=1000000,
        ...     price=0.0,
        ...     currency="USD",
        ...     icon="https://example.com/icon.png",
        ...     description="Music streaming",
        ...     screenshots=[],
        ... )
        >>> app.is_free
        True
        >>> app.rating_category()
        'Excellent'

    """

    app_id: str = Field(
        ...,
        description="App package ID (e.g., com.spotify.music)",
        pattern=r"^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)+$",
        examples=["com.spotify.music", "com.netflix.mediaclient"],
    )

    title: str = Field(..., min_length=1, max_length=200, description="App name/title")

    description: str = Field(
        default="", max_length=50000, description="Full app description"
    )

    developer: str = Field(
        ..., min_length=1, max_length=200, description="Developer name"
    )

    developer_id: str | None = Field(None, description="Developer ID on Google Play")

    score: float | None = Field(
        None, ge=0, le=5, description="Average rating (0-5 stars)"
    )

    ratings: int = Field(ge=0, description="Total number of ratings")

    price: float = Field(ge=0, description="Price in specified currency")

    currency: str = Field(default="USD", min_length=3, max_length=3)

    icon: HttpUrl = Field(..., description="App icon URL")

    screenshots: Annotated[
        list[HttpUrl],
        Field(default_factory=list, max_length=20, description="Screenshot URLs"),
    ]

    category: str | None = Field(None, description="App category")

    version: str | None = Field(None, max_length=50, description="Current version")

    updated: str | None = Field(None, description="Last update date")

    installs: str | None = Field(None, description="Install count range")

    min_android: str | None = Field(
        None, description="Minimum Android version required"
    )

    permissions: Annotated[
        list[Permission],
        Field(
            default_factory=list,
            max_length=50,
            description="App permissions grouped by category",
        ),
    ]

    model_config = ConfigDict(
        frozen=True,  # Make immutable
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "app_id": "com.spotify.music",
                "title": "Spotify",
                "description": "Music streaming service",
                "developer": "Spotify Ltd.",
                "developer_id": "1234567890",
                "score": 4.5,
                "ratings": 5000000,
                "price": 0.0,
                "currency": "USD",
                "icon": "https://example.com/icon.png",
                "screenshots": ["https://example.com/screen1.png"],
                "category": "MUSIC",
                "version": "8.8.0",
                "updated": "2024-01-15",
                "installs": "1,000,000,000+",
                "min_android": "6.0",
                "permissions": [
                    {
                        "group": "Location",
                        "permissions": ["approximate location", "precise location"],
                    }
                ],
            }
        },
    )

    @field_validator("title", "developer")
    @classmethod
    def clean_text(cls, v: str) -> str:
        """Clean and normalize text fields."""
        return v.strip()

    @field_validator("price")
    @classmethod
    def round_price(cls, v: float) -> float:
        """Round price to 2 decimal places."""
        return round(v, 2)

    @property
    def is_free(self) -> bool:
        """Check if app is free."""
        return self.price == 0.0

    def is_highly_rated(self) -> bool:
        """Check if app has high rating (4.0+)."""
        return self.score is not None and self.score >= 4.0

    def rating_category(self) -> str:
        """Get rating category.

        Returns:
            str: "Excellent", "Good", "Average", "Poor", or "No rating"

        """
        if self.score is None:
            return "No rating"
        if self.score >= 4.5:
            return "Excellent"
        if self.score >= 4.0:
            return "Good"
        if self.score >= 3.0:
            return "Average"
        return "Poor"

    def has_permissions(self) -> bool:
        """Check if app has any permissions."""
        return len(self.permissions) > 0

    def get_permission_groups(self) -> list[str]:
        """Get list of permission group names."""
        return [p.group for p in self.permissions]

    def get_all_permissions(self) -> list[str]:
        """Get flat list of all permissions across all groups."""
        result: list[str] = []
        for perm_group in self.permissions:
            result.extend(perm_group.permissions)
        return result

    @classmethod
    def from_rust(cls, rust_obj: Any) -> "AppInfo":
        """Create AppInfo from Rust DTO.

        This method converts the simple Rust data transfer object into
        a fully-validated Pydantic model. Validation happens automatically.

        Args:
            rust_obj: RustAppInfo object from the Rust core

        Returns:
            AppInfo: Validated Pydantic model

        Raises:
            ValidationError: If data doesn't meet validation requirements

        """
        return cls(
            app_id=rust_obj.app_id,
            title=rust_obj.title,
            description=rust_obj.description,
            developer=rust_obj.developer,
            developer_id=rust_obj.developer_id,
            score=rust_obj.score,
            ratings=rust_obj.ratings,
            price=rust_obj.price,
            currency=rust_obj.currency,
            icon=rust_obj.icon,
            screenshots=list(rust_obj.screenshots),
            category=rust_obj.category,
            version=rust_obj.version,
            updated=rust_obj.updated,
            installs=rust_obj.installs,
            min_android=rust_obj.min_android,
            permissions=[Permission.from_rust(p) for p in rust_obj.permissions],
        )


class Review(BaseModel):
    """Google Play app review with validation.

    Examples:
        >>> review = Review(
        ...     review_id="abc123",
        ...     user_name="John Doe",
        ...     content="Great app!",
        ...     score=5,
        ...     thumbs_up=10,
        ...     created_at=datetime.now(),
        ... )
        >>> review.is_positive()
        True

    """

    review_id: str = Field(..., min_length=1, description="Unique review ID")

    user_name: str = Field(
        ..., min_length=1, max_length=100, description="Reviewer name"
    )

    user_image: HttpUrl | None = Field(None, description="Reviewer profile image URL")

    content: str = Field(..., max_length=50000, description="Review text content")

    score: int = Field(..., ge=1, le=5, description="Review score (1-5 stars)")

    thumbs_up: int = Field(ge=0, description="Number of helpful votes")

    created_at: datetime = Field(..., description="Review creation timestamp")

    reply_content: str | None = Field(
        None, max_length=10000, description="Developer reply text"
    )

    reply_at: datetime | None = Field(None, description="Developer reply timestamp")

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    @field_validator("content", "reply_content")
    @classmethod
    def clean_content(cls, v: str | None) -> str | None:
        """Clean review content."""
        if v is None:
            return None
        return v.strip()

    def is_positive(self) -> bool:
        """Check if review is positive (4+ stars)."""
        return self.score >= 4

    def has_reply(self) -> bool:
        """Check if developer has replied."""
        return self.reply_content is not None

    @classmethod
    def from_rust(cls, rust_obj: Any) -> "Review":
        """Create Review from Rust DTO.

        Args:
            rust_obj: RustReview object from the Rust core

        Returns:
            Review: Validated Pydantic model

        Raises:
            ValidationError: If data doesn't meet validation requirements

        """
        # Convert Unix timestamp to datetime
        # Rust returns Option<i64> (Unix timestamp in seconds)
        if rust_obj.created_at is not None:
            created_at = datetime.fromtimestamp(rust_obj.created_at)
        else:
            # Default to epoch time if timestamp is missing
            created_at = datetime.fromtimestamp(0)

        reply_at = None
        if rust_obj.reply_at is not None:
            reply_at = datetime.fromtimestamp(rust_obj.reply_at)

        return cls(
            review_id=rust_obj.review_id,
            user_name=rust_obj.user_name,
            user_image=rust_obj.user_image,
            content=rust_obj.content,
            score=rust_obj.score,
            thumbs_up=rust_obj.thumbs_up,
            created_at=created_at,
            reply_content=rust_obj.reply_content,
            reply_at=reply_at,
        )


class SearchResult(BaseModel):
    """Google Play search result with validation.

    Examples:
        >>> result = SearchResult(
        ...     app_id="com.spotify.music",
        ...     title="Spotify",
        ...     developer="Spotify Ltd.",
        ...     icon="https://example.com/icon.png",
        ...     score=4.5,
        ...     price=0.0,
        ...     currency="USD",
        ... )

    """

    app_id: str = Field(
        ...,
        pattern=r"^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)+$",
        description="App package ID",
    )

    title: str = Field(..., min_length=1, max_length=200)

    developer: str = Field(..., min_length=1, max_length=200)

    icon: HttpUrl = Field(..., description="App icon URL")

    score: float | None = Field(None, ge=0, le=5)

    price: float = Field(ge=0)

    currency: str = Field(default="USD", min_length=3, max_length=3)

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    @property
    def is_free(self) -> bool:
        """Check if app is free."""
        return self.price == 0.0

    def __str__(self) -> str:
        """Return human-readable string representation."""
        score_str = f"{self.score:.1f} stars" if self.score else "No rating"
        price_str = "Free" if self.is_free else f"{self.currency} {self.price:.2f}"
        return f"{self.title} by {self.developer} - {score_str} - {price_str}"

    def __repr__(self) -> str:
        """Return detailed representation for debugging."""
        score_str = f"{self.score:.1f}" if self.score else "None"
        return (
            f"SearchResult(app_id='{self.app_id}', title='{self.title}', "
            f"developer='{self.developer}', score={score_str}, "
            f"price={self.price:.2f}, currency='{self.currency}')"
        )

    @classmethod
    def from_rust(cls, rust_obj: Any) -> "SearchResult":
        """Create SearchResult from Rust DTO.

        Args:
            rust_obj: RustSearchResult object from the Rust core

        Returns:
            SearchResult: Validated Pydantic model

        """
        return cls(
            app_id=rust_obj.app_id,
            title=rust_obj.title,
            developer=rust_obj.developer,
            icon=rust_obj.icon,
            score=rust_obj.score,
            price=rust_obj.price,
            currency=rust_obj.currency,
        )

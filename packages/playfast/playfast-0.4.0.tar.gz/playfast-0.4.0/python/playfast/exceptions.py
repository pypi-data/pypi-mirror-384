"""Exception classes for Playfast.

Provides structured error handling for Google Play Store scraping operations.
"""


class PlayfastError(Exception):
    """Base exception for all Playfast errors."""


class AppNotFoundError(PlayfastError):
    """Raised when an app cannot be found on Google Play.

    Args:
        app_id: The app ID that was not found
        message: Optional custom error message

    """

    def __init__(self, app_id: str, message: str | None = None) -> None:
        self.app_id = app_id
        if message is None:
            message = f"App not found: {app_id}"
        super().__init__(message)


class RateLimitError(PlayfastError):
    """Raised when rate limit is exceeded.

    Args:
        retry_after: Seconds to wait before retrying
        message: Optional custom error message

    """

    def __init__(self, retry_after: int = 60, message: str | None = None) -> None:
        self.retry_after = retry_after
        if message is None:
            message = f"Rate limit exceeded. Retry after {retry_after} seconds."
        super().__init__(message)


class ParseError(PlayfastError):
    """Raised when HTML parsing fails.

    This typically indicates that Google Play's page structure has changed
    or the response is not in the expected format.

    Args:
        message: Description of what failed to parse
        html_snippet: Optional snippet of the problematic HTML

    """

    def __init__(self, message: str, html_snippet: str | None = None) -> None:
        self.html_snippet = html_snippet
        super().__init__(message)


class NetworkError(PlayfastError):
    """Raised when network requests fail.

    Args:
        url: The URL that failed
        status_code: HTTP status code (if available)
        message: Optional custom error message

    """

    def __init__(
        self,
        url: str,
        status_code: int | None = None,
        message: str | None = None,
    ) -> None:
        self.url = url
        self.status_code = status_code
        if message is None:
            if status_code:
                message = f"Network error {status_code} for URL: {url}"
            else:
                message = f"Network error for URL: {url}"
        super().__init__(message)


class ValidationError(PlayfastError):
    """Raised when data validation fails.

    This is different from Pydantic's ValidationError - it's for
    business logic validation that happens before or after Pydantic.

    Args:
        field: The field that failed validation
        value: The invalid value
        message: Optional custom error message

    """

    def __init__(self, field: str, value: object, message: str | None = None) -> None:
        self.field = field
        self.value = value
        if message is None:
            message = f"Validation failed for field '{field}': {value}"
        super().__init__(message)


class TimeoutError(PlayfastError):
    """Raised when an operation times out.

    Args:
        operation: Description of the operation that timed out
        timeout: The timeout value in seconds

    """

    def __init__(self, operation: str, timeout: float) -> None:
        self.operation = operation
        self.timeout = timeout
        message = f"Operation '{operation}' timed out after {timeout} seconds"
        super().__init__(message)

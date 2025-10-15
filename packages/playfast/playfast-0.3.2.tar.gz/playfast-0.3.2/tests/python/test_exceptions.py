"""Tests for exception classes.

This module tests all custom exception classes to ensure they:
1. Initialize correctly with various parameters
2. Store attributes properly
3. Generate appropriate error messages
"""

import pytest

from playfast.exceptions import (
    AppNotFoundError,
    NetworkError,
    ParseError,
    PlayfastError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)


class TestPlayfastError:
    """Tests for base PlayfastError exception."""

    def test_base_exception_creation(self):
        """Test that PlayfastError can be created and raised."""
        error = PlayfastError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"

    def test_base_exception_can_be_raised(self):
        """Test that PlayfastError can be raised and caught."""
        msg = "Test error"
        with pytest.raises(PlayfastError) as exc_info:
            raise PlayfastError(msg)
        assert "Test error" in str(exc_info.value)


class TestAppNotFoundError:
    """Tests for AppNotFoundError exception."""

    def test_default_message(self):
        """Test AppNotFoundError with default message."""
        error = AppNotFoundError("com.test.app")
        assert error.app_id == "com.test.app"
        assert "com.test.app" in str(error)
        assert "not found" in str(error).lower()

    def test_custom_message(self):
        """Test AppNotFoundError with custom message."""
        error = AppNotFoundError("com.test.app", "Custom error message")
        assert error.app_id == "com.test.app"
        assert str(error) == "Custom error message"

    def test_inherits_from_playfast_error(self):
        """Test that AppNotFoundError inherits from PlayfastError."""
        error = AppNotFoundError("com.test.app")
        assert isinstance(error, PlayfastError)
        assert isinstance(error, Exception)

    def test_can_be_raised_and_caught(self):
        """Test that AppNotFoundError can be raised and caught."""
        msg = "com.missing.app"
        with pytest.raises(AppNotFoundError) as exc_info:
            raise AppNotFoundError(msg)
        assert exc_info.value.app_id == "com.missing.app"


class TestRateLimitError:
    """Tests for RateLimitError exception."""

    def test_default_message_and_retry_after(self):
        """Test RateLimitError with default parameters."""
        error = RateLimitError()
        assert error.retry_after == 60
        assert "60" in str(error)
        assert "Rate limit" in str(error)

    def test_custom_retry_after(self):
        """Test RateLimitError with custom retry_after."""
        error = RateLimitError(retry_after=120)
        assert error.retry_after == 120
        assert "120" in str(error)

    def test_custom_message(self):
        """Test RateLimitError with custom message."""
        error = RateLimitError(retry_after=30, message="Custom rate limit message")
        assert error.retry_after == 30
        assert str(error) == "Custom rate limit message"

    def test_inherits_from_playfast_error(self):
        """Test that RateLimitError inherits from PlayfastError."""
        error = RateLimitError()
        assert isinstance(error, PlayfastError)

    def test_can_be_raised_and_caught(self):
        """Test that RateLimitError can be raised and caught."""
        with pytest.raises(RateLimitError) as exc_info:
            raise RateLimitError(retry_after=90)
        assert exc_info.value.retry_after == 90


class TestParseError:
    """Tests for ParseError exception."""

    def test_basic_parse_error(self):
        """Test ParseError with just a message."""
        error = ParseError("Failed to parse HTML")
        assert str(error) == "Failed to parse HTML"
        assert error.html_snippet is None

    def test_parse_error_with_snippet(self):
        """Test ParseError with HTML snippet."""
        html = "<div>broken html"
        error = ParseError("Failed to parse", html_snippet=html)
        assert str(error) == "Failed to parse"
        assert error.html_snippet == html

    def test_inherits_from_playfast_error(self):
        """Test that ParseError inherits from PlayfastError."""
        error = ParseError("Parse failed")
        assert isinstance(error, PlayfastError)

    def test_can_be_raised_and_caught(self):
        """Test that ParseError can be raised and caught."""
        msg = "Invalid JSON"
        with pytest.raises(ParseError) as exc_info:
            raise ParseError(msg)
        assert "Invalid JSON" in str(exc_info.value)


class TestNetworkError:
    """Tests for NetworkError exception."""

    def test_network_error_without_status_code(self):
        """Test NetworkError without status code."""
        error = NetworkError("https://example.com")
        assert error.url == "https://example.com"
        assert error.status_code is None
        assert "https://example.com" in str(error)
        assert "Network error" in str(error)

    def test_network_error_with_status_code(self):
        """Test NetworkError with status code."""
        error = NetworkError("https://example.com", status_code=404)
        assert error.url == "https://example.com"
        assert error.status_code == 404
        assert "404" in str(error)
        assert "https://example.com" in str(error)

    def test_network_error_with_custom_message(self):
        """Test NetworkError with custom message."""
        error = NetworkError(
            "https://example.com", status_code=500, message="Server is down"
        )
        assert error.url == "https://example.com"
        assert error.status_code == 500
        assert str(error) == "Server is down"

    def test_inherits_from_playfast_error(self):
        """Test that NetworkError inherits from PlayfastError."""
        error = NetworkError("https://example.com")
        assert isinstance(error, PlayfastError)

    def test_can_be_raised_and_caught(self):
        """Test that NetworkError can be raised and caught."""
        msg = "https://fail.com"
        with pytest.raises(NetworkError) as exc_info:
            raise NetworkError(msg, status_code=503)
        assert exc_info.value.status_code == 503


class TestValidationError:
    """Tests for ValidationError exception."""

    def test_validation_error_default_message(self):
        """Test ValidationError with default message."""
        error = ValidationError("price", -1)
        assert error.field == "price"
        assert error.value == -1
        assert "price" in str(error)
        assert "-1" in str(error)

    def test_validation_error_custom_message(self):
        """Test ValidationError with custom message."""
        error = ValidationError("email", "invalid", "Email format is incorrect")
        assert error.field == "email"
        assert error.value == "invalid"
        assert str(error) == "Email format is incorrect"

    def test_validation_error_with_complex_value(self):
        """Test ValidationError with complex value."""
        value = {"nested": "dict"}
        error = ValidationError("data", value)
        assert error.field == "data"
        assert error.value == value

    def test_inherits_from_playfast_error(self):
        """Test that ValidationError inherits from PlayfastError."""
        error = ValidationError("field", "value")
        assert isinstance(error, PlayfastError)

    def test_can_be_raised_and_caught(self):
        """Test that ValidationError can be raised and caught."""
        msg = "score"
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError(msg, 10)
        assert exc_info.value.field == "score"
        assert exc_info.value.value == 10


class TestTimeoutError:
    """Tests for TimeoutError exception."""

    def test_timeout_error_creation(self):
        """Test TimeoutError initialization."""
        error = TimeoutError("HTTP request", 30.0)
        assert error.operation == "HTTP request"
        assert error.timeout == 30.0
        assert "HTTP request" in str(error)
        assert "30" in str(error)

    def test_timeout_error_with_decimal_timeout(self):
        """Test TimeoutError with decimal timeout."""
        error = TimeoutError("Database query", 5.5)
        assert error.timeout == 5.5
        assert "5.5" in str(error)

    def test_inherits_from_playfast_error(self):
        """Test that TimeoutError inherits from PlayfastError."""
        error = TimeoutError("operation", 10.0)
        assert isinstance(error, PlayfastError)

    def test_can_be_raised_and_caught(self):
        """Test that TimeoutError can be raised and caught."""
        msg = "API call"
        with pytest.raises(TimeoutError) as exc_info:
            raise TimeoutError(msg, 60.0)
        assert exc_info.value.operation == "API call"
        assert exc_info.value.timeout == 60.0


class TestExceptionHierarchy:
    """Tests for exception inheritance hierarchy."""

    def test_all_exceptions_inherit_from_base(self):
        """Test that all custom exceptions inherit from PlayfastError."""
        exceptions = [
            AppNotFoundError("test"),
            RateLimitError(),
            ParseError("test"),
            NetworkError("test"),
            ValidationError("test", "test"),
            TimeoutError("test", 1.0),
        ]
        for exc in exceptions:
            assert isinstance(exc, PlayfastError)
            assert isinstance(exc, Exception)

    def test_exceptions_can_be_caught_as_base_type(self):
        """Test that specific exceptions can be caught as PlayfastError."""
        msg = "com.test.app"
        with pytest.raises(PlayfastError):
            raise AppNotFoundError(msg)

        with pytest.raises(PlayfastError):
            raise RateLimitError()

        msg2 = "test"
        with pytest.raises(PlayfastError):
            raise ParseError(msg2)

    def test_exceptions_have_distinct_types(self):
        """Test that exception types are distinct."""
        app_error = AppNotFoundError("test")
        rate_error = RateLimitError()
        parse_error = ParseError("test")

        assert type(app_error) is not type(rate_error)
        assert type(rate_error) is not type(parse_error)
        assert type(parse_error) is not type(app_error)


class TestExceptionUsagePatterns:
    """Tests for common exception usage patterns."""

    def test_exception_chaining(self):
        """Test that exceptions can be chained with 'from'."""
        original = ValueError("Original error")
        msg = "Wrapped error"

        with pytest.raises(ParseError) as exc_info:
            try:
                raise original
            except ValueError as e:
                raise ParseError(msg) from e

        assert exc_info.value.__cause__ is original

    def test_exception_context_preservation(self):
        """Test that exception context is preserved."""
        msg = "https://example.com"

        with pytest.raises(NetworkError) as exc_info:
            try:
                _ = 1 / 0
            except ZeroDivisionError as e:
                raise NetworkError(msg, 500) from e

        # Should have explicit cause
        assert exc_info.value.__cause__ is not None

    def test_multiple_exceptions_can_coexist(self):
        """Test handling multiple exception types."""
        errors: list[PlayfastError] = []

        try:
            msg = "com.app1"
            raise AppNotFoundError(msg)
        except PlayfastError as e:
            errors.append(e)

        try:
            raise RateLimitError(30)
        except PlayfastError as e:
            errors.append(e)

        assert len(errors) == 2
        assert isinstance(errors[0], AppNotFoundError)
        assert isinstance(errors[1], RateLimitError)

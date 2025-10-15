use pyo3::exceptions::PyException;
use pyo3::prelude::*;
use thiserror::Error;

/// Rust errors for the playfast library
#[derive(Error, Debug)]
pub enum PlayfastError {
    #[error("HTTP request failed: {0}")]
    HttpError(#[from] reqwest::Error),

    #[error("Failed to parse HTML: {0}")]
    ParseError(String),

    #[error("App not found: {0}")]
    AppNotFound(String),

    #[error("Invalid app ID: {0}")]
    InvalidAppId(String),

    #[error("Rate limit exceeded")]
    RateLimitError,

    #[error("JSON parsing failed: {0}")]
    JsonError(#[from] serde_json::Error),

    #[error("Regex error: {0}")]
    RegexError(#[from] regex::Error),

    #[error("Unknown error: {0}")]
    Other(String),
}

/// Convert Rust errors to Python exceptions
impl From<PlayfastError> for PyErr {
    fn from(err: PlayfastError) -> PyErr {
        PyException::new_err(err.to_string())
    }
}

pub type Result<T> = std::result::Result<T, PlayfastError>;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_error() {
        let error = PlayfastError::ParseError("Test error".to_string());
        assert_eq!(error.to_string(), "Failed to parse HTML: Test error");
    }

    #[test]
    fn test_app_not_found() {
        let error = PlayfastError::AppNotFound("com.test.app".to_string());
        assert_eq!(error.to_string(), "App not found: com.test.app");
    }

    #[test]
    fn test_invalid_app_id() {
        let error = PlayfastError::InvalidAppId("invalid-id".to_string());
        assert_eq!(error.to_string(), "Invalid app ID: invalid-id");
    }

    #[test]
    fn test_rate_limit_error() {
        let error = PlayfastError::RateLimitError;
        assert_eq!(error.to_string(), "Rate limit exceeded");
    }

    #[test]
    fn test_other_error() {
        let error = PlayfastError::Other("Something went wrong".to_string());
        assert_eq!(error.to_string(), "Unknown error: Something went wrong");
    }

    #[test]
    fn test_error_from_json() {
        let json_err = serde_json::from_str::<serde_json::Value>("invalid json");
        assert!(json_err.is_err());

        let error: PlayfastError = json_err.unwrap_err().into();
        assert!(matches!(error, PlayfastError::JsonError(_)));
    }

    #[test]
    fn test_error_from_regex() {
        let regex_err = regex::Regex::new("[invalid");
        assert!(regex_err.is_err());

        let error: PlayfastError = regex_err.unwrap_err().into();
        assert!(matches!(error, PlayfastError::RegexError(_)));
    }

    #[test]
    fn test_result_type_ok() {
        let result: Result<i32> = Ok(42);
        assert_eq!(result.unwrap(), 42);
    }

    #[test]
    fn test_result_type_err() {
        let result: Result<i32> = Err(PlayfastError::ParseError("Error".to_string()));
        assert!(result.is_err());

        match result {
            Err(PlayfastError::ParseError(msg)) => assert_eq!(msg, "Error"),
            _ => panic!("Expected ParseError"),
        }
    }

    #[test]
    fn test_error_debug() {
        let error = PlayfastError::AppNotFound("com.test".to_string());
        let debug_str = format!("{:?}", error);
        assert!(debug_str.contains("AppNotFound"));
        assert!(debug_str.contains("com.test"));
    }

    #[test]
    fn test_error_display() {
        let error = PlayfastError::InvalidAppId("bad-id".to_string());
        let display_str = format!("{}", error);
        assert_eq!(display_str, "Invalid app ID: bad-id");
    }

    #[test]
    fn test_error_chain() {
        // Test that errors can be converted and chained
        let json_err = serde_json::from_str::<serde_json::Value>("{invalid}").unwrap_err();
        let playfast_err: PlayfastError = json_err.into();

        match playfast_err {
            PlayfastError::JsonError(_) => {
                // Success - error was properly converted
            }
            _ => panic!("Expected JsonError"),
        }
    }

    #[test]
    fn test_multiple_error_types() {
        let errors = vec![
            PlayfastError::ParseError("Parse".to_string()),
            PlayfastError::AppNotFound("app".to_string()),
            PlayfastError::InvalidAppId("id".to_string()),
            PlayfastError::RateLimitError,
            PlayfastError::Other("other".to_string()),
        ];

        assert_eq!(errors.len(), 5);

        // Verify each error can be matched
        for error in errors {
            match error {
                PlayfastError::ParseError(_) |
                PlayfastError::AppNotFound(_) |
                PlayfastError::InvalidAppId(_) |
                PlayfastError::RateLimitError |
                PlayfastError::JsonError(_) |
                PlayfastError::HttpError(_) |
                PlayfastError::RegexError(_) |
                PlayfastError::Other(_) => {
                    // All error types are covered
                }
            }
        }
    }

    #[test]
    #[ignore] // Ignore this test as it requires Python interpreter initialization
    fn test_error_to_pyerr() {
        // Test conversion to Python error
        // Note: This test is ignored because PyErr requires Python interpreter to be initialized
        // In actual usage, Python will be initialized by the time this code runs
        let error = PlayfastError::ParseError("Test".to_string());
        // Test that the conversion compiles (actual runtime test requires Python init)
        let _py_err: PyErr = error.into();
    }
}

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyDictMethods};
use serde::{Deserialize, Serialize};

/// Permission group data transfer object
#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RustPermission {
    #[pyo3(get)]
    pub group: String,

    #[pyo3(get)]
    pub permissions: Vec<String>,
}

#[pymethods]
impl RustPermission {
    fn to_dict(&self, py: Python) -> PyResult<Py<PyAny>> {
        let dict = PyDict::new(py);
        dict.set_item("group", &self.group)?;
        dict.set_item("permissions", &self.permissions)?;
        Ok(dict.into())
    }

    fn __repr__(&self) -> String {
        format!(
            "RustPermission(group='{}', permissions={})",
            self.group,
            self.permissions.len()
        )
    }
}

/// Simple Data Transfer Object for app information
/// No validation here - validation happens in Python with Pydantic
#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RustAppInfo {
    #[pyo3(get)]
    pub app_id: String,

    #[pyo3(get)]
    pub title: String,

    #[pyo3(get)]
    pub description: String,

    #[pyo3(get)]
    pub developer: String,

    #[pyo3(get)]
    pub developer_id: Option<String>,

    #[pyo3(get)]
    pub score: Option<f32>,

    #[pyo3(get)]
    pub ratings: i64,

    #[pyo3(get)]
    pub price: f32,

    #[pyo3(get)]
    pub currency: String,

    #[pyo3(get)]
    pub icon: String,

    #[pyo3(get)]
    pub screenshots: Vec<String>,

    #[pyo3(get)]
    pub category: Option<String>,

    #[pyo3(get)]
    pub version: Option<String>,

    #[pyo3(get)]
    pub updated: Option<String>,

    #[pyo3(get)]
    pub installs: Option<String>,

    #[pyo3(get)]
    pub min_android: Option<String>,

    #[pyo3(get)]
    pub permissions: Vec<RustPermission>,
}

#[pymethods]
impl RustAppInfo {
    /// Convert to Python dict (for easier Pydantic conversion)
    fn to_dict(&self, py: Python) -> PyResult<Py<PyAny>> {
        let dict = PyDict::new(py);
        dict.set_item("app_id", &self.app_id)?;
        dict.set_item("title", &self.title)?;
        dict.set_item("description", &self.description)?;
        dict.set_item("developer", &self.developer)?;
        dict.set_item("developer_id", &self.developer_id)?;
        dict.set_item("score", self.score)?;
        dict.set_item("ratings", self.ratings)?;
        dict.set_item("price", self.price)?;
        dict.set_item("currency", &self.currency)?;
        dict.set_item("icon", &self.icon)?;
        dict.set_item("screenshots", &self.screenshots)?;
        dict.set_item("category", &self.category)?;
        dict.set_item("version", &self.version)?;
        dict.set_item("updated", &self.updated)?;
        dict.set_item("installs", &self.installs)?;
        dict.set_item("min_android", &self.min_android)?;

        // Convert permissions Vec to Python list of dicts
        let perm_dicts: Vec<Py<PyAny>> = self.permissions.iter()
            .map(|p| p.to_dict(py))
            .collect::<PyResult<Vec<_>>>()?;
        dict.set_item("permissions", perm_dicts)?;

        Ok(dict.into())
    }

    fn __repr__(&self) -> String {
        format!(
            "RustAppInfo(app_id='{}', title='{}', score={:?})",
            self.app_id, self.title, self.score
        )
    }

    fn __str__(&self) -> String {
        self.__repr__()
    }
}

/// Simple Data Transfer Object for reviews
#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RustReview {
    #[pyo3(get)]
    pub review_id: String,

    #[pyo3(get)]
    pub user_name: String,

    #[pyo3(get)]
    pub user_image: Option<String>,

    #[pyo3(get)]
    pub content: String,

    #[pyo3(get)]
    pub score: i32,

    #[pyo3(get)]
    pub thumbs_up: i32,

    /// Unix timestamp (seconds since epoch), None if not available
    #[pyo3(get)]
    pub created_at: Option<i64>,

    #[pyo3(get)]
    pub reply_content: Option<String>,

    /// Unix timestamp (seconds since epoch), None if not available
    #[pyo3(get)]
    pub reply_at: Option<i64>,
}

#[pymethods]
impl RustReview {
    fn to_dict(&self, py: Python) -> PyResult<Py<PyAny>> {
        let dict = PyDict::new(py);
        dict.set_item("review_id", &self.review_id)?;
        dict.set_item("user_name", &self.user_name)?;
        dict.set_item("user_image", &self.user_image)?;
        dict.set_item("content", &self.content)?;
        dict.set_item("score", self.score)?;
        dict.set_item("thumbs_up", self.thumbs_up)?;
        dict.set_item("created_at", self.created_at)?;
        dict.set_item("reply_content", &self.reply_content)?;
        dict.set_item("reply_at", self.reply_at)?;
        Ok(dict.into())
    }

    fn __repr__(&self) -> String {
        format!(
            "RustReview(user='{}', score={}, content='{}')",
            self.user_name,
            self.score,
            if self.content.len() > 50 {
                format!("{}...", &self.content[..50])
            } else {
                self.content.clone()
            }
        )
    }
}

/// Search result data transfer object
#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RustSearchResult {
    #[pyo3(get)]
    pub app_id: String,

    #[pyo3(get)]
    pub title: String,

    #[pyo3(get)]
    pub developer: String,

    #[pyo3(get)]
    pub icon: String,

    #[pyo3(get)]
    pub score: Option<f32>,

    #[pyo3(get)]
    pub price: f32,

    #[pyo3(get)]
    pub currency: String,
}

#[pymethods]
impl RustSearchResult {
    fn to_dict(&self, py: Python) -> PyResult<Py<PyAny>> {
        let dict = PyDict::new(py);
        dict.set_item("app_id", &self.app_id)?;
        dict.set_item("title", &self.title)?;
        dict.set_item("developer", &self.developer)?;
        dict.set_item("icon", &self.icon)?;
        dict.set_item("score", self.score)?;
        dict.set_item("price", self.price)?;
        dict.set_item("currency", &self.currency)?;
        Ok(dict.into())
    }

    fn __repr__(&self) -> String {
        format!(
            "RustSearchResult(app_id='{}', title='{}')",
            self.app_id, self.title
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rust_app_info_creation() {
        let app = RustAppInfo {
            app_id: "com.test.app".to_string(),
            title: "Test App".to_string(),
            description: "A test application".to_string(),
            developer: "Test Developer".to_string(),
            developer_id: Some("dev123".to_string()),
            score: Some(4.5),
            ratings: 1000,
            price: 0.0,
            currency: "USD".to_string(),
            icon: "https://example.com/icon.png".to_string(),
            screenshots: vec!["https://example.com/screen1.png".to_string()],
            category: Some("GAME_CASUAL".to_string()),
            version: Some("1.0.0".to_string()),
            updated: Some("2024-01-15".to_string()),
            installs: Some("1,000+".to_string()),
            min_android: Some("5.0".to_string()),
            permissions: vec![],
        };

        assert_eq!(app.app_id, "com.test.app");
        assert_eq!(app.title, "Test App");
        assert_eq!(app.score, Some(4.5));
        assert_eq!(app.ratings, 1000);
    }

    #[test]
    fn test_rust_app_info_repr() {
        let app = RustAppInfo {
            app_id: "com.test.app".to_string(),
            title: "Test App".to_string(),
            description: "A test application".to_string(),
            developer: "Test Developer".to_string(),
            developer_id: None,
            score: Some(4.5),
            ratings: 100,
            price: 0.0,
            currency: "USD".to_string(),
            icon: "icon.png".to_string(),
            screenshots: vec![],
            category: None,
            version: None,
            updated: None,
            installs: None,
            min_android: None,
            permissions: vec![],
        };

        let repr = app.__repr__();
        assert!(repr.contains("com.test.app"));
        assert!(repr.contains("Test App"));
        assert!(repr.contains("4.5"));
    }

    #[test]
    fn test_rust_app_info_serialization() {
        let app = RustAppInfo {
            app_id: "com.test.app".to_string(),
            title: "Test App".to_string(),
            description: "Test".to_string(),
            developer: "Dev".to_string(),
            developer_id: None,
            score: Some(4.0),
            ratings: 100,
            price: 0.0,
            currency: "USD".to_string(),
            icon: "icon.png".to_string(),
            screenshots: vec![],
            category: None,
            version: None,
            updated: None,
            installs: None,
            min_android: None,
            permissions: vec![],
        };

        // Test serde serialization
        let json = serde_json::to_string(&app).unwrap();
        assert!(json.contains("com.test.app"));
        assert!(json.contains("Test App"));

        // Test deserialization
        let deserialized: RustAppInfo = serde_json::from_str(&json).unwrap();
        assert_eq!(deserialized.app_id, app.app_id);
        assert_eq!(deserialized.title, app.title);
    }

    #[test]
    fn test_rust_review_creation() {
        let review = RustReview {
            review_id: "review123".to_string(),
            user_name: "John Doe".to_string(),
            user_image: Some("avatar.jpg".to_string()),
            content: "Great app!".to_string(),
            score: 5,
            thumbs_up: 42,
            created_at: Some(1705334400), // 2024-01-15 timestamp
            reply_content: Some("Thanks!".to_string()),
            reply_at: Some(1705420800), // 2024-01-16 timestamp
        };

        assert_eq!(review.review_id, "review123");
        assert_eq!(review.user_name, "John Doe");
        assert_eq!(review.score, 5);
        assert_eq!(review.thumbs_up, 42);
        assert_eq!(review.created_at, Some(1705334400));
    }

    #[test]
    fn test_rust_review_repr() {
        let review = RustReview {
            review_id: "review123".to_string(),
            user_name: "John Doe".to_string(),
            user_image: None,
            content: "This is a test review".to_string(),
            score: 4,
            thumbs_up: 10,
            created_at: Some(1705334400),
            reply_content: None,
            reply_at: None,
        };

        let repr = review.__repr__();
        assert!(repr.contains("John Doe"));
        assert!(repr.contains("4"));
        assert!(repr.contains("This is a test review"));
    }

    #[test]
    fn test_rust_review_repr_long_content() {
        let long_content = "a".repeat(100);
        let review = RustReview {
            review_id: "review123".to_string(),
            user_name: "John Doe".to_string(),
            user_image: None,
            content: long_content.clone(),
            score: 5,
            thumbs_up: 0,
            created_at: Some(1705334400),
            reply_content: None,
            reply_at: None,
        };

        let repr = review.__repr__();
        // Should truncate long content (note: repr includes other parts too)
        assert!(repr.contains("..."));
        // Check that content is truncated, not the whole repr
        let truncated_content = if long_content.len() > 50 {
            format!("{}...", &long_content[..50])
        } else {
            long_content.clone()
        };
        assert!(repr.contains(&truncated_content[..30])); // Check first 30 chars
    }

    #[test]
    fn test_rust_review_serialization() {
        let review = RustReview {
            review_id: "review123".to_string(),
            user_name: "John Doe".to_string(),
            user_image: None,
            content: "Great!".to_string(),
            score: 5,
            thumbs_up: 10,
            created_at: Some(1705334400),
            reply_content: None,
            reply_at: None,
        };

        let json = serde_json::to_string(&review).unwrap();
        assert!(json.contains("review123"));
        assert!(json.contains("John Doe"));

        let deserialized: RustReview = serde_json::from_str(&json).unwrap();
        assert_eq!(deserialized.review_id, review.review_id);
        assert_eq!(deserialized.content, review.content);
    }

    #[test]
    fn test_rust_search_result_creation() {
        let result = RustSearchResult {
            app_id: "com.test.app".to_string(),
            title: "Test App".to_string(),
            developer: "Test Dev".to_string(),
            icon: "icon.png".to_string(),
            score: Some(4.5),
            price: 4.99,
            currency: "USD".to_string(),
        };

        assert_eq!(result.app_id, "com.test.app");
        assert_eq!(result.title, "Test App");
        assert_eq!(result.score, Some(4.5));
        assert_eq!(result.price, 4.99);
    }

    #[test]
    fn test_rust_search_result_free_app() {
        let result = RustSearchResult {
            app_id: "com.free.app".to_string(),
            title: "Free App".to_string(),
            developer: "Dev".to_string(),
            icon: "icon.png".to_string(),
            score: None,
            price: 0.0,
            currency: "USD".to_string(),
        };

        assert_eq!(result.price, 0.0);
        assert_eq!(result.score, None);
    }

    #[test]
    fn test_rust_search_result_repr() {
        let result = RustSearchResult {
            app_id: "com.test.app".to_string(),
            title: "Test App".to_string(),
            developer: "Dev".to_string(),
            icon: "icon.png".to_string(),
            score: Some(4.0),
            price: 0.0,
            currency: "USD".to_string(),
        };

        let repr = result.__repr__();
        assert!(repr.contains("com.test.app"));
        assert!(repr.contains("Test App"));
    }

    #[test]
    fn test_rust_search_result_serialization() {
        let result = RustSearchResult {
            app_id: "com.test.app".to_string(),
            title: "Test".to_string(),
            developer: "Dev".to_string(),
            icon: "icon.png".to_string(),
            score: Some(4.5),
            price: 0.0,
            currency: "USD".to_string(),
        };

        let json = serde_json::to_string(&result).unwrap();
        assert!(json.contains("com.test.app"));

        let deserialized: RustSearchResult = serde_json::from_str(&json).unwrap();
        assert_eq!(deserialized.app_id, result.app_id);
        assert_eq!(deserialized.score, result.score);
    }

    #[test]
    fn test_all_models_clone() {
        // Test that all models implement Clone correctly
        let app = RustAppInfo {
            app_id: "com.test".to_string(),
            title: "Test".to_string(),
            description: "Test".to_string(),
            developer: "Dev".to_string(),
            developer_id: None,
            score: Some(4.0),
            ratings: 100,
            price: 0.0,
            currency: "USD".to_string(),
            icon: "icon.png".to_string(),
            screenshots: vec![],
            category: None,
            version: None,
            updated: None,
            installs: None,
            min_android: None,
            permissions: vec![],
        };

        let app_clone = app.clone();
        assert_eq!(app.app_id, app_clone.app_id);

        let review = RustReview {
            review_id: "r1".to_string(),
            user_name: "User".to_string(),
            user_image: None,
            content: "Content".to_string(),
            score: 5,
            thumbs_up: 0,
            created_at: Some(1705334400),
            reply_content: None,
            reply_at: None,
        };

        let review_clone = review.clone();
        assert_eq!(review.review_id, review_clone.review_id);

        let search = RustSearchResult {
            app_id: "com.test".to_string(),
            title: "Test".to_string(),
            developer: "Dev".to_string(),
            icon: "icon.png".to_string(),
            score: Some(4.0),
            price: 0.0,
            currency: "USD".to_string(),
        };

        let search_clone = search.clone();
        assert_eq!(search.app_id, search_clone.app_id);
    }
}

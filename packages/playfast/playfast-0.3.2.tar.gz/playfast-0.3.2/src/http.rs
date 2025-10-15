use crate::error::{PlayfastError, Result};
use crate::models::{RustAppInfo, RustReview, RustSearchResult};
use crate::parser::{parse_app_page, parse_search_results, parse_batchexecute_list_response, parse_batchexecute_reviews_response};
use std::time::Duration;

/// Build request body for batchexecute list API (optimized for minimal allocations)
/// This is a standalone function that can be used by Python for async HTTP + Rust parsing
pub fn build_list_request_body(category: Option<&str>, collection: &str, num: u32) -> String {
    let template = include_str!("freq_template.txt");

    // Pre-convert values once to avoid multiple conversions
    let num_str = num.to_string();
    let category_str = category.unwrap_or("APPLICATION");

    // Pre-allocate with extra capacity for replaced values
    let mut result = String::with_capacity(template.len() + 32);

    // Single-pass replacement: scan once and replace all placeholders
    let mut remaining = template;

    while let Some(pos) = remaining.find("${") {
        // Append text before placeholder
        result.push_str(&remaining[..pos]);

        // Find closing brace
        if let Some(end) = remaining[pos..].find('}') {
            let placeholder = &remaining[pos + 2..pos + end];

            // Replace based on placeholder name
            match placeholder {
                "num" => result.push_str(&num_str),
                "collection" => result.push_str(collection),
                "category" => result.push_str(category_str),
                _ => {
                    // Unknown placeholder, keep original
                    result.push_str(&remaining[pos..pos + end + 1]);
                }
            }

            // Move past this placeholder
            remaining = &remaining[pos + end + 1..];
        } else {
            // No closing brace found, append rest and break
            result.push_str(&remaining[pos..]);
            break;
        }
    }

    // Append any remaining text
    result.push_str(remaining);

    result
}

/// Build request body for batchexecute reviews API (optimized for minimal allocations)
/// This is a standalone function that can be used by Python for async HTTP + Rust parsing
pub fn build_reviews_request_body(
    app_id: &str,
    sort: u8,
    continuation_token: Option<&str>,
    lang: &str,
    country: &str,
) -> String {
    let template = include_str!("freq_reviews_template.txt");

    // Pre-convert values once
    let sort_str = sort.to_string();
    let token_value = match continuation_token {
        Some(t) => format!("\\\"{}\\\"", t),
        None => "null".to_string(),
    };

    // Pre-allocate with extra capacity
    let mut result = String::with_capacity(template.len() + 64);

    // Single-pass replacement
    let mut remaining = template;

    while let Some(pos) = remaining.find("${") {
        result.push_str(&remaining[..pos]);

        if let Some(end) = remaining[pos..].find('}') {
            let placeholder = &remaining[pos + 2..pos + end];

            match placeholder {
                "appId" => result.push_str(app_id),
                "sort" => result.push_str(&sort_str),
                "num" => result.push_str("40"),
                "token" => result.push_str(&token_value),
                "lang" => result.push_str(lang),
                "country" => result.push_str(country),
                _ => result.push_str(&remaining[pos..pos + end + 1]),
            }

            remaining = &remaining[pos + end + 1..];
        } else {
            result.push_str(&remaining[pos..]);
            break;
        }
    }

    result.push_str(remaining);
    result
}

/// HTTP client for Google Play Store (async)
pub struct PlayStoreClient {
    client: reqwest::Client,  // Changed from blocking::Client
    base_url: String,
}

impl PlayStoreClient {
    /// Create a new PlayStore HTTP client with optimized connection settings
    pub fn new(timeout_secs: u64) -> Result<Self> {
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(timeout_secs))
            .user_agent(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                 AppleWebKit/537.36 (KHTML, like Gecko) \
                 Chrome/131.0.0.0 Safari/537.36"
            )
            // Connection pooling optimizations
            .pool_max_idle_per_host(10)  // Keep 10 idle connections per host
            .pool_idle_timeout(Duration::from_secs(90))  // Keep connections alive for 90s
            .tcp_keepalive(Duration::from_secs(60))  // TCP keepalive
            .build()?;

        Ok(Self {
            client,
            base_url: "https://play.google.com".to_string(),
        })
    }

    /// Fetch HTML from URL with query parameters (async)
    async fn fetch_html(&self, path: &str, params: &[(&str, &str)]) -> Result<String> {
        let url = format!("{}{}", self.base_url, path);

        let response = self.client
            .get(&url)
            .query(params)
            .send()
            .await?;  // Added .await

        // Check status code
        let status = response.status();
        let final_url = response.url().to_string();

        if status == reqwest::StatusCode::TOO_MANY_REQUESTS {
            return Err(PlayfastError::RateLimitError);
        }

        if status == reqwest::StatusCode::NOT_FOUND {
            let error_info = params.iter()
                .find(|(k, _)| *k == "id")
                .map(|(_, v)| v.to_string())
                .unwrap_or_else(|| format!("URL: {}", final_url));

            return Err(PlayfastError::AppNotFound(error_info));
        }

        if !status.is_success() {
            return Err(PlayfastError::Other(
                format!("HTTP error: {} for URL: {}", status, final_url)
            ));
        }

        Ok(response.text().await?)  // Added .await
    }

    /// Fetch and parse app information (async, GIL-free)
    pub async fn fetch_and_parse_app(
        &self,
        app_id: &str,
        lang: &str,
        country: &str,
    ) -> Result<RustAppInfo> {
        let params = [
            ("id", app_id),
            ("hl", lang),
            ("gl", country),
        ];

        let html = self.fetch_html("/store/apps/details", &params).await?;  // Added .await
        parse_app_page(&html, app_id)
    }

    /// Fetch and parse reviews (async, GIL-free)
    pub async fn fetch_and_parse_reviews(
        &self,
        app_id: &str,
        lang: &str,
        country: &str,
        sort: u8,
        continuation_token: Option<&str>,
    ) -> Result<(Vec<RustReview>, Option<String>)> {
        let body = build_reviews_request_body(app_id, sort, continuation_token, lang, country);

        let url = format!(
            "{}/_/PlayStoreUi/data/batchexecute?\
             rpcids=oCPfdb&\
             source-path=%2Fstore%2Fapps%2Fdetails&\
             f.sid=-697906427155521722&\
             bl=boq_playuiserver_20190903.08_p0&\
             hl={}&\
             gl={}&\
             authuser=0&\
             soc-app=121&\
             soc-platform=1&\
             soc-device=1&\
             _reqid=1065213&\
             rt=c",
            self.base_url, lang, country
        );

        let response = self.client
            .post(&url)
            .header("Content-Type", "application/x-www-form-urlencoded;charset=UTF-8")
            .body(body)
            .send()
            .await?;  // Added .await

        if !response.status().is_success() {
            return Err(PlayfastError::Other(
                format!("batchexecute reviews failed: {}", response.status())
            ));
        }

        let text = response.text().await?;  // Added .await

        parse_batchexecute_reviews_response(&text)
    }

    /// Fetch and parse search results (async, GIL-free)
    pub async fn fetch_and_parse_search(
        &self,
        query: &str,
        lang: &str,
        country: &str,
    ) -> Result<Vec<RustSearchResult>> {
        let params = [
            ("q", query),
            ("c", "apps"),
            ("hl", lang),
            ("gl", country),
        ];

        let html = self.fetch_html("/store/search", &params).await?;  // Added .await

        parse_search_results(&html)
    }

    /// Fetch and parse list results (async, GIL-free)
    pub async fn fetch_and_parse_list(
        &self,
        category: Option<&str>,
        collection: &str,
        lang: &str,
        country: &str,
        num: u32,
    ) -> Result<Vec<RustSearchResult>> {
        let body = build_list_request_body(category, collection, num);

        let url = format!(
            "{}/_/PlayStoreUi/data/batchexecute?\
             rpcids=vyAe2&\
             source-path=%2Fstore%2Fapps&\
             f.sid=-4178618388443751758&\
             bl=boq_playuiserver_20220612.08_p0&\
             authuser=0&\
             soc-app=121&\
             soc-platform=1&\
             soc-device=1&\
             _reqid=82003&\
             rt=c&\
             hl={}&\
             gl={}",
            self.base_url, lang, country
        );

        let response = self.client
            .post(&url)
            .header("Content-Type", "application/x-www-form-urlencoded;charset=UTF-8")
            .body(body)
            .send()
            .await?;  // Added .await

        if !response.status().is_success() {
            return Err(PlayfastError::Other(
                format!("batchexecute failed: {}", response.status())
            ));
        }

        let text = response.text().await?;  // Added .await

        parse_batchexecute_list_response(&text)
    }
}

impl Default for PlayStoreClient {
    fn default() -> Self {
        Self::new(30).expect("Failed to create default client")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_client_creation() {
        let client = PlayStoreClient::new(30);
        assert!(client.is_ok());
    }

    #[test]
    fn test_default_client() {
        let _client = PlayStoreClient::default();
    }

    #[tokio::test]
    #[ignore] // Requires network
    async fn test_fetch_real_app() {
        let client = PlayStoreClient::new(30).unwrap();
        let result = client.fetch_and_parse_app(
            "com.google.android.apps.maps",
            "en",
            "us"
        ).await;

        if result.is_ok() {
            let app = result.unwrap();
            assert_eq!(app.app_id, "com.google.android.apps.maps");
            assert!(!app.title.is_empty());
        }
    }

    #[tokio::test]
    #[ignore] // Requires network
    async fn test_fetch_nonexistent_app() {
        let client = PlayStoreClient::new(30).unwrap();
        let result = client.fetch_and_parse_app(
            "com.nonexistent.app.that.does.not.exist",
            "en",
            "us"
        ).await;

        assert!(result.is_err());
        match result {
            Err(PlayfastError::AppNotFound(_)) => {
                // Expected
            }
            _ => panic!("Expected AppNotFound error"),
        }
    }

    #[tokio::test]
    #[ignore] // Requires network
    async fn test_search() {
        let client = PlayStoreClient::new(30).unwrap();
        let results = client.fetch_and_parse_search(
            "maps",
            "en",
            "us"
        ).await;

        if results.is_ok() {
            let search_results = results.unwrap();
            assert!(!search_results.is_empty());
            assert!(search_results.iter().any(|r| r.title.to_lowercase().contains("maps")));
        }
    }
}

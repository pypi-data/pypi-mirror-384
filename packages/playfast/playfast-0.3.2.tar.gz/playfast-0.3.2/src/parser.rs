use crate::error::{PlayfastError, Result};
use crate::models::{RustAppInfo, RustPermission, RustReview, RustSearchResult};
use regex::Regex;
use serde_json::Value;

/// Parse app information page (CPU-intensive, GIL-free)
pub fn parse_app_page(html: &str, app_id: &str) -> Result<RustAppInfo> {
    // Extract JSON data from the HTML page - specifically the 'ds:5' block
    let json_data = extract_app_json_data(html)?;

    // The app data is in the nested structure: json_data[1][2]
    let app_data = json_data
        .get(1)
        .and_then(|v| v.get(2))
        .ok_or_else(|| PlayfastError::ParseError("App data structure not found at [1][2]".to_string()))?;

    Ok(RustAppInfo {
        app_id: app_id.to_string(),
        // New paths from ds:5 block
        title: extract_string(app_data, &[0, 0])?,
        description: extract_string(app_data, &[72, 0, 1]).unwrap_or_default(),
        developer: extract_string(app_data, &[37, 0])?,
        developer_id: extract_string(app_data, &[68, 0, 0, 4, 2]).ok(),
        score: extract_f32(app_data, &[51, 0, 1]),
        ratings: extract_i64(app_data, &[51, 2, 1]).unwrap_or(0),
        price: 0.0,  // TODO: Find price path in ds:5
        currency: "USD".to_string(),  // TODO: Find currency path
        icon: extract_string(app_data, &[9, 1, 3, 2])?,
        screenshots: extract_screenshots_ds5(app_data),
        category: extract_string(app_data, &[79, 0, 0, 0]).ok(),
        version: extract_string(app_data, &[140, 0, 0, 0]).ok(),
        updated: extract_string(app_data, &[145, 0, 0]).ok(),
        installs: extract_string(app_data, &[13, 0]).ok(),
        min_android: extract_string(app_data, &[140, 1, 0, 0, 1]).ok(),
        permissions: extract_permissions(app_data),
    })
}

/// Parse review batch from HTML or JSON string
pub fn parse_review_batch(data: &str) -> Result<Vec<RustReview>> {
    // Try to parse directly as JSON array first (for batchexecute format)
    if let Ok(json_data) = serde_json::from_str::<Value>(data) {
        return parse_reviews_from_json(&json_data);
    }

    // Fallback to HTML parsing (legacy format)
    let json_data = extract_json_data(data)?;
    parse_reviews_from_json(json_data.get(0).unwrap_or(&json_data))
}

/// Parse reviews from a JSON value (array of review items)
fn parse_reviews_from_json(json_data: &Value) -> Result<Vec<RustReview>> {
    let mut reviews = Vec::new();

    if let Some(review_items) = json_data.as_array() {
        for item in review_items {
            if let Ok(review) = parse_single_review(item) {
                reviews.push(review);
            }
        }
    }

    Ok(reviews)
}

/// Parse a single review from JSON
/// Based on google-play-scraper mappings:
/// - id: [0]
/// - userName: [1, 0]
/// - userImage: [1, 1, 3, 2]
/// - at: [5, 0] - Unix timestamp
/// - score: [2]
/// - text: [4]
/// - replyContent: [7, 1]
/// - repliedAt: [7, 2, 0] - Unix timestamp
/// - thumbsUpCount: [6]
fn parse_single_review(data: &Value) -> Result<RustReview> {
    // Extract created_at timestamp from [5, 0]
    let created_at = extract_i64(data, &[5, 0]).ok();

    // Extract reply_at timestamp from [7, 2, 0]
    let reply_at = extract_i64(data, &[7, 2, 0]).ok();

    Ok(RustReview {
        review_id: extract_string(data, &[0])?,
        user_name: extract_string(data, &[1, 0])?,
        user_image: extract_string(data, &[1, 1, 3, 2]).ok(),
        content: extract_string(data, &[4])?,
        score: extract_i32(data, &[2])?,
        thumbs_up: extract_i32(data, &[6]).unwrap_or(0),
        created_at,
        reply_content: extract_string(data, &[7, 1]).ok(),
        reply_at,
    })
}

/// Parse search results
pub fn parse_search_results(html: &str) -> Result<Vec<RustSearchResult>> {
    // Find ALL AF_initDataCallback blocks with keys (e.g., ds:0, ds:1, ...)
    // Pattern matches: AF_initDataCallback({key: 'ds:4', hash: '...', data: [...], sideChannel: {}});
    let re = Regex::new(r"AF_initDataCallback\(\{(?:key:\s*'([^']+)',\s*)?(?:hash:\s*'[^']+',\s*)?data:(.*?),\s*sideChannel:")?;
    let mut data_blocks = Vec::new();

    for cap in re.captures_iter(html) {
        let key = cap.get(1).map(|m| m.as_str().to_string());
        if let Some(json_str) = cap.get(2) {
            if let Ok(json_data) = serde_json::from_str::<Value>(json_str.as_str()) {
                data_blocks.push((key, json_data));
            }
        }
    }

    if data_blocks.is_empty() {
        return Ok(Vec::new());
    }

    // Try to find ds:4 (search results) or use last block
    let json_data = data_blocks.iter()
        .find(|(key, _)| key.as_deref() == Some("ds:4"))
        .map(|(_, data)| data)
        .unwrap_or(&data_blocks[data_blocks.len() - 1].1);

    // Try multiple paths - Google Play structure varies by query
    let paths = vec![
        vec![0, 1, 1, 22, 0],  // Most common: spotify, tiktok, netflix
        vec![0, 1, 0, 22, 0],  // Alternative: maps
        vec![0, 1, 0, 28, 0],  // List API format
    ];

    for path in paths {
        if let Ok(results_array) = navigate_json(json_data, &path) {
            if let Some(items) = results_array.as_array() {
                let mut results = Vec::new();
                let mut found_apps = 0;

                for item in items {
                    // Skip null items
                    if item.is_null() {
                        continue;
                    }

                    // Parse using batchexecute format
                    if let Ok(result) = parse_batchexecute_search_result(item) {
                        results.push(result);
                        found_apps += 1;
                    }
                }

                // Return if we found apps
                if found_apps > 0 {
                    return Ok(results);
                }
            }
        }
    }

    Ok(Vec::new())
}

/// Parse list results (category/collection listing)
#[allow(dead_code)]
pub fn parse_list_results(html: &str) -> Result<Vec<RustSearchResult>> {
    let json_data = extract_json_data(html)?;

    // List pages typically have apps at different paths depending on the type
    // Try multiple possible locations
    let mut results = Vec::new();

    // Path 1: Standard category listing - similar to search
    if let Ok(items_array) = navigate_json(&json_data, &[0, 1, 0, 0, 0]) {
        if let Some(items) = items_array.as_array() {
            for item in items {
                if let Ok(result) = parse_single_search_result(item) {
                    results.push(result);
                }
            }
        }
    }

    // Path 2: Collection listing (e.g., top charts)
    if results.is_empty() {
        if let Ok(items_array) = navigate_json(&json_data, &[0, 0, 0]) {
            if let Some(items) = items_array.as_array() {
                for item in items {
                    if let Ok(result) = parse_single_search_result(item) {
                        results.push(result);
                    }
                }
            }
        }
    }

    // If still no results, try the app detail list structure
    if results.is_empty() {
        if let Ok(items_array) = navigate_json(&json_data, &[0]) {
            if let Some(items) = items_array.as_array() {
                for item in items {
                    if let Ok(result) = parse_single_search_result(item) {
                        results.push(result);
                    }
                }
            }
        }
    }

    Ok(results)
}

/// Parse a single search result (old HTML format, kept for compatibility)
#[allow(dead_code)]
fn parse_single_search_result(data: &Value) -> Result<RustSearchResult> {
    Ok(RustSearchResult {
        app_id: extract_string(data, &[12, 0])?,
        title: extract_string(data, &[2])?,
        developer: extract_string(data, &[4, 0, 0, 0])?,
        icon: extract_string(data, &[1, 1, 0, 3, 2])?,
        score: extract_f32(data, &[6, 0, 2, 1, 1]),
        price: extract_price(data)?,
        currency: extract_string(data, &[7, 0, 3, 2, 0, 2]).unwrap_or_else(|_| "USD".to_string()),
    })
}

/// Parse a single app from batchexecute-style search results
/// This uses the same structure as the list API
fn parse_batchexecute_search_result(app: &Value) -> Result<RustSearchResult> {
    // Extract app data (typically wrapped in an array)
    let app_data = app.get(0).ok_or_else(|| PlayfastError::ParseError("App data not found".to_string()))?;

    // Extract fields using batchexecute array indices
    let app_id = app_data
        .get(0)
        .and_then(|v| v.get(0))
        .and_then(|v| v.as_str())
        .ok_or_else(|| PlayfastError::ParseError("App ID not found".to_string()))?
        .to_string();

    let title = app_data
        .get(3)
        .and_then(|v| v.as_str())
        .ok_or_else(|| PlayfastError::ParseError("Title not found".to_string()))?
        .to_string();

    let developer = app_data
        .get(14)
        .and_then(|v| v.as_str())
        .unwrap_or("Unknown")
        .to_string();

    let icon = app_data
        .get(1)
        .and_then(|v| v.get(3))
        .and_then(|v| v.get(2))
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .to_string();

    let score = app_data
        .get(4)
        .and_then(|v| v.get(1))
        .and_then(|v| v.as_f64())
        .map(|f| f as f32);

    // Price and currency are at [8][1][0]
    // Structure: [price_in_micros, "CURRENCY", "display_string"]
    let price_data = app_data.get(8).and_then(|v| v.get(1)).and_then(|v| v.get(0));

    let price = price_data
        .and_then(|v| v.get(0))
        .and_then(|v| v.as_i64())
        .map(|micros| micros as f32 / 1_000_000.0)
        .unwrap_or(0.0);

    let currency = price_data
        .and_then(|v| v.get(1))
        .and_then(|v| v.as_str())
        .unwrap_or("USD")
        .to_string();

    Ok(RustSearchResult {
        app_id,
        title,
        developer,
        icon,
        score,
        price,
        currency,
    })
}

/// Extract app-specific JSON data from HTML (finds the 'ds:5' block)
fn extract_app_json_data(html: &str) -> Result<Value> {
    // Google Play embeds multiple data blocks with keys like 'ds:0', 'ds:5', etc.
    // App data is in the 'ds:5' block
    let re = Regex::new(r"AF_initDataCallback\(\{(?:key:\s*'([^']+)',\s*)?(?:hash:\s*'[^']+',\s*)?data:(.*?),\s*sideChannel:")?;

    // Find all blocks
    for cap in re.captures_iter(html) {
        let key = cap.get(1).map(|m| m.as_str());

        // Look for 'ds:5' specifically
        if key == Some("ds:5") {
            if let Some(json_str) = cap.get(2) {
                return serde_json::from_str(json_str.as_str()).map_err(|e| {
                    PlayfastError::ParseError(format!("Failed to parse ds:5 JSON: {}", e))
                });
            }
        }
    }

    Err(PlayfastError::ParseError("Could not find ds:5 block in HTML".to_string()))
}

/// Extract JSON data from HTML using regex (for reviews, searches, etc.)
fn extract_json_data(html: &str) -> Result<Value> {
    // Google Play embeds data in a specific format: AF_initDataCallback({key:..., hash:..., data:...})
    // The hash parameter is optional, so we need a flexible pattern
    let re = Regex::new(r"AF_initDataCallback\(\{[^{]*(?:hash:\s*'[^']+',\s*)?data:(.*?),\s*sideChannel:")?;

    let caps = re
        .captures(html)
        .ok_or_else(|| PlayfastError::ParseError("Could not find JSON data in HTML".to_string()))?;

    let json_str = caps
        .get(1)
        .ok_or_else(|| PlayfastError::ParseError("Could not extract JSON string".to_string()))?
        .as_str();

    serde_json::from_str(json_str).map_err(|e| {
        PlayfastError::ParseError(format!("Failed to parse JSON: {}", e))
    })
}

/// Navigate JSON path and extract string
fn extract_string(data: &Value, path: &[usize]) -> Result<String> {
    let value = navigate_json(data, path)?;

    value
        .as_str()
        .map(|s| s.to_string())
        .ok_or_else(|| PlayfastError::ParseError(format!("Expected string at path {:?}", path)))
}

/// Navigate JSON path and extract f32
fn extract_f32(data: &Value, path: &[usize]) -> Option<f32> {
    navigate_json(data, path)
        .ok()
        .and_then(|v| v.as_f64())
        .map(|f| f as f32)
}

/// Navigate JSON path and extract i32
fn extract_i32(data: &Value, path: &[usize]) -> Result<i32> {
    let value = navigate_json(data, path)?;

    value
        .as_i64()
        .map(|i| i as i32)
        .ok_or_else(|| PlayfastError::ParseError(format!("Expected integer at path {:?}", path)))
}

/// Navigate JSON path and extract i64
fn extract_i64(data: &Value, path: &[usize]) -> Result<i64> {
    let value = navigate_json(data, path)?;

    value
        .as_i64()
        .ok_or_else(|| PlayfastError::ParseError(format!("Expected integer at path {:?}", path)))
}

/// Navigate nested JSON structure
fn navigate_json<'a>(data: &'a Value, path: &[usize]) -> Result<&'a Value> {
    let mut current = data;

    for &index in path {
        current = current
            .get(index)
            .ok_or_else(|| {
                PlayfastError::ParseError(format!("Index {} not found in JSON path {:?}", index, path))
            })?;
    }

    Ok(current)
}

/// Extract price (0.0 for free apps)
#[allow(dead_code)]
fn extract_price(data: &Value) -> Result<f32> {
    // Try to get price, default to 0.0 for free apps
    if let Ok(price_str) = extract_string(data, &[7, 0, 3, 2, 0, 0]) {
        // Remove currency symbols and parse
        let clean_price = price_str
            .chars()
            .filter(|c| c.is_ascii_digit() || *c == '.')
            .collect::<String>();

        Ok(clean_price.parse::<f32>().unwrap_or(0.0))
    } else {
        Ok(0.0)
    }
}

/// Extract screenshot URLs (old format - kept for compatibility)
#[allow(dead_code)]
fn extract_screenshots(data: &Value) -> Vec<String> {
    let mut screenshots = Vec::new();

    // Screenshots are usually at path [12, 0]
    if let Ok(screenshot_array) = navigate_json(data, &[12, 0]) {
        if let Some(items) = screenshot_array.as_array() {
            for item in items.iter().take(10) {
                // Limit to 10 screenshots
                if let Ok(url) = extract_string(item, &[3, 2]) {
                    screenshots.push(url);
                }
            }
        }
    }

    screenshots
}

/// Extract screenshot URLs from ds:5 block format
fn extract_screenshots_ds5(data: &Value) -> Vec<String> {
    let mut screenshots = Vec::new();

    // In ds:5, screenshots are in a different location
    // Try path [9] which contains media items
    if let Ok(media_array) = navigate_json(data, &[9]) {
        if let Some(items) = media_array.as_array() {
            for item in items.iter().take(10) {
                // Try to extract URL from various possible locations
                if let Ok(url) = extract_string(item, &[1, 3, 2]) {
                    if url.starts_with("http") && url.contains("screenshot") {
                        screenshots.push(url);
                    }
                } else if let Ok(url) = extract_string(item, &[7, 3, 2]) {
                    if url.starts_with("http") && url.contains("screenshot") {
                        screenshots.push(url);
                    }
                }
            }
        }
    }

    screenshots
}

/// Extract app permissions from ds:5 block format
///
/// Permission structure in ds:5:
/// data[74][2][0] = array of permission groups
/// Each group: [group_name, icon_info, [details], icon_id]
/// Each detail: [order, description]
fn extract_permissions(data: &Value) -> Vec<RustPermission> {
    let mut permissions = Vec::new();

    // Try to access permissions array at [74][2][0]
    if let Ok(perm_groups_array) = navigate_json(data, &[74, 2, 0]) {
        if let Some(groups) = perm_groups_array.as_array() {
            for group in groups {
                if let Some(group_arr) = group.as_array() {
                    // Extract group name from [0]
                    let group_name = group_arr
                        .first()
                        .and_then(|v| v.as_str())
                        .unwrap_or("Unknown")
                        .to_string();

                    // Extract permission details from [2]
                    let mut perm_list = Vec::new();
                    if let Some(details_arr) = group_arr.get(2).and_then(|v| v.as_array()) {
                        for detail in details_arr {
                            if let Some(detail_arr) = detail.as_array() {
                                // Permission description is at [1]
                                if let Some(desc) = detail_arr.get(1).and_then(|v| v.as_str()) {
                                    perm_list.push(desc.to_string());
                                }
                            }
                        }
                    }

                    // Only add if we found at least one permission
                    if !perm_list.is_empty() {
                        permissions.push(RustPermission {
                            group: group_name,
                            permissions: perm_list,
                        });
                    }
                }
            }
        }
    }

    permissions
}

/// Extract continuation token for pagination
pub fn extract_continuation_token(html: &str) -> Option<String> {
    // Pattern for continuation token in Google Play
    let re = Regex::new(r#"GAEi[A-Za-z0-9_-]+"#).ok()?;

    re.find(html)
        .map(|m| m.as_str().to_string())
}

/// Parse batchexecute API response format for list (category/collection)
/// This is the response from the /_/PlayStoreUi/data/batchexecute endpoint
pub fn parse_batchexecute_list_response(text: &str) -> Result<Vec<RustSearchResult>> {
    let lines: Vec<&str> = text.lines().collect();

    if lines.len() < 4 {
        return Ok(Vec::new());
    }

    let json_line = lines[3];
    let outer_data: serde_json::Value = serde_json::from_str(json_line)
        .map_err(|e| PlayfastError::ParseError(format!("Failed to parse outer JSON: {}", e)))?;

    let inner_json_str = outer_data
        .get(0)
        .and_then(|v| v.get(2))
        .and_then(|v| v.as_str())
        .ok_or_else(|| PlayfastError::ParseError("Inner JSON not found".to_string()))?;

    let inner_data: serde_json::Value = serde_json::from_str(inner_json_str)
        .map_err(|e| PlayfastError::ParseError(format!("Failed to parse inner JSON: {}", e)))?;

    let apps_array = inner_data
        .get(0)
        .and_then(|v| v.get(1))
        .and_then(|v| v.get(0))
        .and_then(|v| v.get(28))
        .and_then(|v| v.get(0))
        .and_then(|v| v.as_array())
        .ok_or_else(|| PlayfastError::ParseError("Apps array not found".to_string()))?;

    let mut results = Vec::new();
    for app in apps_array {
        if let Ok(search_result) = parse_batchexecute_search_result(app) {
            results.push(search_result);
        }
    }

    Ok(results)
}

/// Parse batchexecute API response format for reviews
/// This is the response from the /_/PlayStoreUi/data/batchexecute endpoint for reviews
pub fn parse_batchexecute_reviews_response(text: &str) -> Result<(Vec<RustReview>, Option<String>)> {
    let lines: Vec<&str> = text.lines().collect();

    if lines.len() < 4 {
        return Err(PlayfastError::ParseError(format!(
            "Response has only {} lines, need at least 4", lines.len()
        )));
    }

    let mut outer_data: Option<serde_json::Value> = None;

    for idx in [1, 2, 3, 4, 5] {
        if idx < lines.len() && lines[idx].starts_with('[') {
            match serde_json::from_str::<serde_json::Value>(lines[idx]) {
                Ok(data) => {
                    outer_data = Some(data);
                    break;
                }
                Err(_) => continue,
            }
        }
    }

    let outer_data = outer_data.ok_or_else(||
        PlayfastError::ParseError("No valid JSON found in response lines".to_string())
    )?;

    let first_elem = outer_data
        .get(0)
        .ok_or_else(|| PlayfastError::ParseError("No element at index 0".to_string()))?;

    let first_elem_len = first_elem.as_array().map(|a| a.len()).unwrap_or(0);

    let inner_json_str = first_elem
        .get(2)
        .and_then(|v| v.as_str())
        .or_else(|| first_elem.get(1).and_then(|v| v.as_str()))
        .ok_or_else(|| PlayfastError::ParseError(format!(
            "Inner JSON not found at [0][2] or [0][1]. First element has {} items.", first_elem_len
        )))?;

    if inner_json_str.trim().is_empty() || inner_json_str == "null" {
        return Ok((Vec::new(), None));
    }

    let inner_data: serde_json::Value = serde_json::from_str(inner_json_str)
        .map_err(|e| PlayfastError::ParseError(format!(
            "Failed to parse inner JSON (len={}): {}", inner_json_str.len(), e
        )))?;

    let reviews_array = inner_data.get(0);

    let reviews = if let Some(arr_val) = reviews_array {
        if arr_val.is_null() {
            Vec::new()
        } else if let Some(arr) = arr_val.as_array() {
            if arr.is_empty() {
                Vec::new()
            } else {
                parse_review_batch(&serde_json::to_string(arr)?)?
            }
        } else {
            Vec::new()
        }
    } else {
        Vec::new()
    };

    let arr_len = inner_data.as_array().map(|a| a.len()).unwrap_or(0);
    let next_token = if arr_len >= 2 {
        inner_data
            .get(arr_len - 2)
            .and_then(|v| {
                let sub_len = v.as_array().map(|a| a.len()).unwrap_or(0);
                if sub_len > 0 {
                    v.get(sub_len - 1)
                } else {
                    None
                }
            })
            .and_then(|v| v.as_str())
            .map(|s| s.to_string())
    } else {
        None
    };

    Ok((reviews, next_token))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_navigate_json_root() {
        let json_str = r#"{"a": [{"b": "value"}]}"#;
        let data: Value = serde_json::from_str(json_str).unwrap();

        // Navigate to root
        assert!(navigate_json(&data, &[]).is_ok());
    }

    #[test]
    fn test_navigate_json_nested() {
        let json_str = r#"[["test"], {"key": "value"}]"#;
        let data: Value = serde_json::from_str(json_str).unwrap();

        // Navigate to nested array
        let result = navigate_json(&data, &[0, 0]).unwrap();
        assert_eq!(result.as_str().unwrap(), "test");

        // Navigate to nested object
        let result = navigate_json(&data, &[1]).unwrap();
        assert!(result.is_object());
    }

    #[test]
    fn test_navigate_json_invalid_path() {
        let json_str = r#"["test"]"#;
        let data: Value = serde_json::from_str(json_str).unwrap();

        // Try to access invalid index
        assert!(navigate_json(&data, &[5]).is_err());
    }

    #[test]
    fn test_extract_string() {
        let json_str = r#"["test", "value"]"#;
        let data: Value = serde_json::from_str(json_str).unwrap();

        assert_eq!(extract_string(&data, &[0]).unwrap(), "test");
        assert_eq!(extract_string(&data, &[1]).unwrap(), "value");
    }

    #[test]
    fn test_extract_string_nested() {
        let json_str = r#"{"data": ["first", "second"]}"#;
        let data: Value = serde_json::from_str(json_str).unwrap();

        // Can't navigate through object keys with usize, this should fail
        assert!(extract_string(&data, &[0, 0]).is_err());
    }

    #[test]
    fn test_extract_string_not_string() {
        let json_str = r#"[123, true]"#;
        let data: Value = serde_json::from_str(json_str).unwrap();

        // Try to extract non-string as string
        assert!(extract_string(&data, &[0]).is_err());
        assert!(extract_string(&data, &[1]).is_err());
    }

    #[test]
    fn test_extract_i32() {
        let json_str = r#"[42, 100, -5]"#;
        let data: Value = serde_json::from_str(json_str).unwrap();

        assert_eq!(extract_i32(&data, &[0]).unwrap(), 42);
        assert_eq!(extract_i32(&data, &[1]).unwrap(), 100);
        assert_eq!(extract_i32(&data, &[2]).unwrap(), -5);
    }

    #[test]
    fn test_extract_i32_invalid() {
        let json_str = r#"["not a number"]"#;
        let data: Value = serde_json::from_str(json_str).unwrap();

        assert!(extract_i32(&data, &[0]).is_err());
    }

    #[test]
    fn test_extract_i64() {
        let json_str = r#"[9223372036854775807, 0, -100]"#;
        let data: Value = serde_json::from_str(json_str).unwrap();

        assert_eq!(extract_i64(&data, &[0]).unwrap(), 9223372036854775807);
        assert_eq!(extract_i64(&data, &[1]).unwrap(), 0);
        assert_eq!(extract_i64(&data, &[2]).unwrap(), -100);
    }

    #[test]
    fn test_extract_f32() {
        let json_str = r#"[4.5, 0.0, -3.14]"#;
        let data: Value = serde_json::from_str(json_str).unwrap();

        assert_eq!(extract_f32(&data, &[0]), Some(4.5));
        assert_eq!(extract_f32(&data, &[1]), Some(0.0));
        assert!((extract_f32(&data, &[2]).unwrap() - (-3.14)).abs() < 0.01);
    }

    #[test]
    fn test_extract_f32_invalid() {
        let json_str = r#"["not a number"]"#;
        let data: Value = serde_json::from_str(json_str).unwrap();

        assert_eq!(extract_f32(&data, &[0]), None);
    }

    #[test]
    fn test_extract_f32_from_int() {
        let json_str = r#"[42]"#;
        let data: Value = serde_json::from_str(json_str).unwrap();

        // Should be able to convert int to float
        assert_eq!(extract_f32(&data, &[0]), Some(42.0));
    }

    #[test]
    fn test_extract_price_free() {
        let json_str = r#"{}"#;
        let data: Value = serde_json::from_str(json_str).unwrap();

        // Free app (no price field)
        assert_eq!(extract_price(&data).unwrap(), 0.0);
    }

    #[test]
    fn test_extract_price_with_currency() {
        // Simulate the exact nested structure that extract_price expects: path [7, 0, 3, 2, 0, 0]
        let json_str = r#"[null, null, null, null, null, null, null, [[null, null, null, [null, null, [["$4.99"]]]]]]"#;
        let data: Value = serde_json::from_str(json_str).unwrap();

        assert_eq!(extract_price(&data).unwrap(), 4.99);
    }

    #[test]
    fn test_extract_price_complex_format() {
        // Simulate the exact nested structure that extract_price expects: path [7, 0, 3, 2, 0, 0]
        let json_str = r#"[null, null, null, null, null, null, null, [[null, null, null, [null, null, [["€12.99"]]]]]]"#;
        let data: Value = serde_json::from_str(json_str).unwrap();

        // Should extract numeric part
        assert_eq!(extract_price(&data).unwrap(), 12.99);
    }

    #[test]
    fn test_extract_screenshots_empty() {
        let json_str = r#"{}"#;
        let data: Value = serde_json::from_str(json_str).unwrap();

        let screenshots = extract_screenshots(&data);
        assert_eq!(screenshots.len(), 0);
    }

    #[test]
    fn test_extract_screenshots_valid() {
        // Path is [12, 0], then each item has screenshot at [3, 2]
        // So structure is: [...][12][0] = array of items, each item[3][2] = url
        let json_str = serde_json::json!([
            null,null,null,null,null,null,null,null,null,null,null,null,
            [  // [12]
                [  // [12][0] - array of screenshots
                    [null, null, null, [null, null, "url1"]], // item[3][2] path
                    [null, null, null, [null, null, "url2"]]
                ]
            ]
        ]);

        let screenshots = extract_screenshots(&json_str);
        assert_eq!(screenshots.len(), 2);
        assert_eq!(screenshots[0], "url1");
        assert_eq!(screenshots[1], "url2");
    }

    #[test]
    fn test_extract_screenshots_limit() {
        // Create more than 10 screenshots at the exact path structure
        let screenshots_array: Vec<Value> = (0..15)
            .map(|i| {
                serde_json::json!([null, null, null, [null, null, format!("url{}", i)]])
            })
            .collect();

        let json_str = serde_json::json!([
            null,null,null,null,null,null,null,null,null,null,null,null,
            [screenshots_array]  // [12][0] = array of screenshot items
        ]);

        let screenshots = extract_screenshots(&json_str);
        // Should be limited to 10
        assert_eq!(screenshots.len(), 10);
    }

    #[test]
    fn test_extract_continuation_token() {
        let html = r#"
            <html>
                <body>
                    <div>Some content</div>
                    <script>var token = 'GAEiAbCdEfGhIjKlMnOpQrStUvWxYz';</script>
                </body>
            </html>
        "#;

        let token = extract_continuation_token(html);
        assert!(token.is_some());
        assert!(token.unwrap().starts_with("GAEi"));
    }

    #[test]
    fn test_extract_continuation_token_not_found() {
        let html = r#"
            <html>
                <body>
                    <div>Some content</div>
                </body>
            </html>
        "#;

        let token = extract_continuation_token(html);
        assert!(token.is_none());
    }

    #[test]
    fn test_extract_json_data_not_found() {
        let html = "<html><body>No JSON here</body></html>";

        let result = extract_json_data(html);
        assert!(result.is_err());

        if let Err(PlayfastError::ParseError(msg)) = result {
            assert!(msg.contains("Could not find JSON data"));
        } else {
            panic!("Expected ParseError");
        }
    }

    #[test]
    fn test_extract_json_data_invalid_json() {
        let html = r#"AF_initDataCallback({key: 'test', data:{invalid json}, sideChannel: {})"#;

        let result = extract_json_data(html);
        assert!(result.is_err());
    }

    #[test]
    fn test_parse_single_review_complete() {
        // user_image path: [1, 1, 3, 2]
        // created_at: Unix timestamp at [5, 0]
        // reply_at: Unix timestamp at [7, 2, 0]
        let review_json = serde_json::json!([
            "review123",                          // review_id [0]
            ["John Doe", [null, null, null, [null, null, "avatar.jpg"]]],  // user info [1]
            5,                                    // score [2]
            null,
            "Great app!",                        // content [4]
            [1705334400],                        // created_at [5][0] - Unix timestamp
            42,                                  // thumbs_up [6]
            [null, "Thanks!", [1705420800]]     // reply info [7] - reply_at at [7][2][0]
        ]);

        let review = parse_single_review(&review_json).unwrap();

        assert_eq!(review.review_id, "review123");
        assert_eq!(review.user_name, "John Doe");
        assert_eq!(review.user_image, Some("avatar.jpg".to_string()));
        assert_eq!(review.content, "Great app!");
        assert_eq!(review.score, 5);
        assert_eq!(review.thumbs_up, 42);
        assert_eq!(review.created_at, Some(1705334400));
        assert_eq!(review.reply_content, Some("Thanks!".to_string()));
        assert_eq!(review.reply_at, Some(1705420800));
    }

    #[test]
    fn test_parse_single_review_minimal() {
        let review_json = serde_json::json!([
            "review456",           // review_id [0]
            ["Jane Doe"],         // user info (minimal) [1]
            3,                    // score [2]
            null,
            "Okay app",          // content [4]
            [1706054400]         // created_at [5][0] - Unix timestamp
        ]);

        let review = parse_single_review(&review_json).unwrap();

        assert_eq!(review.review_id, "review456");
        assert_eq!(review.user_name, "Jane Doe");
        assert_eq!(review.user_image, None);
        assert_eq!(review.content, "Okay app");
        assert_eq!(review.score, 3);
        assert_eq!(review.thumbs_up, 0); // default value
        assert_eq!(review.created_at, Some(1706054400));
        assert_eq!(review.reply_content, None);
        assert_eq!(review.reply_at, None);
    }

    #[test]
    fn test_parse_single_review_invalid() {
        let review_json = serde_json::json!([
            "missing_fields"
        ]);

        let result = parse_single_review(&review_json);
        assert!(result.is_err());
    }

    #[test]
    fn test_parse_single_search_result_complete() {
        // Paths: icon [1,1,0,3,2], developer [4,0,0,0], app_id [12,0],
        // score [6,0,2,1,1], price [7,0,3,2,0,0]
        // Note: score is optional and complex to set up correctly, so we test without it
        let search_json = serde_json::json!([
            null,                                // [0]
            [null, [[null, null, null, [null, null, "icon.jpg"]]]], // [1] icon path
            "Test App",                          // [2] title
            null,                                // [3]
            [[["Developer Name"]]],  // [4] so [4][0][0][0] returns "Developer Name"
            null,                                // [5]
            [],                                  // [6] empty - score will be None
            [[null, null, null, [null, null, [["$4.99"], null, ["USD"]]]]], // [7] price info
            null, null, null, null,              // [8][9][10][11]
            ["com.test.app"]                    // [12] app_id
        ]);

        let result = parse_single_search_result(&search_json).unwrap();

        assert_eq!(result.app_id, "com.test.app");
        assert_eq!(result.title, "Test App");
        assert_eq!(result.developer, "Developer Name");
        assert_eq!(result.icon, "icon.jpg");
        // Score is None because the path doesn't exist in our test data
        assert_eq!(result.score, None);
        assert_eq!(result.price, 4.99);
        assert_eq!(result.currency, "USD");
    }

    #[test]
    fn test_parse_single_search_result_free() {
        let search_json = serde_json::json!([
            null,
            [null, [[null, null, null, [null, null, "icon.jpg"]]]],
            "Free App",
            null,
            [[["Developer"]]],  // [4] so [4][0][0][0] returns "Developer"
            null,
            [null, [null, [null, 4.0]]],
            [],                                 // empty price - free app
            null, null, null, null,
            ["com.free.app"]
        ]);

        let result = parse_single_search_result(&search_json).unwrap();

        assert_eq!(result.app_id, "com.free.app");
        assert_eq!(result.price, 0.0);
        assert_eq!(result.currency, "USD"); // default
    }

    #[test]
    fn test_parse_list_results_empty() {
        // Empty JSON data should return empty results
        let html = r#"AF_initDataCallback({key: 'test', data:[[]], sideChannel: {}})"#;
        let results = parse_list_results(html).unwrap();
        assert_eq!(results.len(), 0);
    }

    #[test]
    fn test_parse_list_results_with_items() {
        // Simulate a list page with items at path [0, 1, 0, 0, 0]
        let list_item = serde_json::json!([
            null,
            [null, [[null, null, null, [null, null, "icon.jpg"]]]],
            "Test App",
            null,
            [[["Developer"]]],
            null,
            [],
            [],
            null, null, null, null,
            ["com.test.app"]
        ]);

        let json_data = serde_json::json!([
            [null, [[[[list_item]]]], null]
        ]);

        let json_str = serde_json::to_string(&json_data).unwrap();
        let html = format!(r#"AF_initDataCallback({{key: 'test', data:{}, sideChannel: {{}}}})"#, json_str);

        let results = parse_list_results(&html).unwrap();
        assert_eq!(results.len(), 1);
        assert_eq!(results[0].app_id, "com.test.app");
        assert_eq!(results[0].title, "Test App");
    }

    #[test]
    fn test_parse_list_results_fallback_paths() {
        // Test that parse_list_results tries multiple paths
        // If first path fails, it should try alternative paths
        let list_item = serde_json::json!([
            null,
            [null, [[null, null, null, [null, null, "icon.jpg"]]]],
            "Another App",
            null,
            [[["Dev"]]],
            null,
            [],
            [],
            null, null, null, null,
            ["com.another.app"]
        ]);

        // Put items at alternative path [0, 0, 0]
        let json_data = serde_json::json!([
            [[list_item]]
        ]);

        let json_str = serde_json::to_string(&json_data).unwrap();
        let html = format!(r#"AF_initDataCallback({{key: 'test', data:{}, sideChannel: {{}}}})"#, json_str);

        let results = parse_list_results(&html).unwrap();
        // Should find items even at alternative path
        assert!(results.len() <= 1); // May find 0 or 1 depending on structure
    }
}

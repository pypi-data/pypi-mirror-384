# Rust Core API

Low-level Rust functions exposed to Python via PyO3.

!!! warning
These are low-level APIs. Most users should use the high-level `AsyncClient` instead.

::: playfast.core
options:
show_source: false
show_root_heading: true
show_if_no_docstring: false
filters:
\- "!^\_"
\- "!^\_\_"
members:
\- parse_app_page
\- parse_review_batch
\- parse_search_results
\- parse_batchexecute_list_response
\- parse_batchexecute_reviews_response
\- fetch_and_parse_app
\- fetch_and_parse_reviews
\- fetch_and_parse_search
\- fetch_and_parse_list
\- build_list_request_body
\- build_reviews_request_body
\- extract_continuation_token
\- RustAppInfo
\- RustReview
\- RustSearchResult
\- RustPermission

class RustAppInfo:
    app_id: str
    title: str
    developer: str
    icon: str
    score: float
    ratings: int
    price: float
    currency: str
    free: bool
    description: str | None
    summary: str | None
    installs: str | None
    min_installs: int | None
    score_text: str | None
    released: str | None
    updated: str | None
    version: str | None
    required_android_version: str | None
    content_rating: str | None
    content_rating_description: str | None
    ad_supported: bool | None
    contains_ads: bool | None
    in_app_purchases: bool | None
    editors_choice: bool | None
    developer_id: str | None
    developer_email: str | None
    developer_website: str | None
    developer_address: str | None
    privacy_policy: str | None
    genre: str | None
    genre_id: str | None
    category: str | None
    video: str | None
    video_image: str | None
    screenshots: list[str]
    similar: list[str]
    permissions: list[RustPermission]

class RustReview:
    review_id: str
    user_name: str
    user_image: str
    content: str
    score: int
    thumbs_up: int
    created_at: int
    reply_content: str | None
    reply_at: int | None

class RustSearchResult:
    app_id: str
    title: str
    developer: str
    icon: str
    score: float | None
    price: float
    currency: str

class RustPermission:
    group: str
    permissions: list[str]
    def __len__(self) -> int: ...

def parse_app_page(html: str, app_id: str) -> RustAppInfo: ...
def parse_review_batch(html: str) -> list[RustReview]: ...
def parse_search_results(html: str) -> list[RustSearchResult]: ...
def extract_continuation_token(html: str) -> str | None: ...
def parse_batchexecute_list_response(response_text: str) -> list[RustSearchResult]: ...
def build_list_request_body(
    category: str | None, collection: str, num: int = 100
) -> str: ...
def build_reviews_request_body(
    app_id: str, sort: int, continuation_token: str | None, lang: str, country: str
) -> str: ...
def parse_batchexecute_reviews_response(
    response_text: str,
) -> tuple[list[RustReview], str | None]: ...

# Single request functions (HTTP + parsing)
def fetch_and_parse_app(
    app_id: str, lang: str, country: str, _timeout: int = 30
) -> RustAppInfo: ...
def fetch_and_parse_reviews(
    app_id: str,
    lang: str,
    country: str,
    sort: int = 1,
    continuation_token: str | None = None,
    _timeout: int = 30,
) -> tuple[list[RustReview], str | None]: ...
def fetch_and_parse_search(
    query: str, lang: str, country: str, _timeout: int = 30
) -> list[RustSearchResult]: ...
def fetch_and_parse_list(
    category: str | None,
    collection: str,
    lang: str,
    country: str,
    num: int = 100,
    _timeout: int = 30,
) -> list[RustSearchResult]: ...

# Batch functions for parallel processing (recommended for multiple requests)
def fetch_and_parse_apps_batch(
    requests: list[tuple[str, str, str]],
) -> list[RustAppInfo]: ...
def fetch_and_parse_list_batch(
    requests: list[tuple[str | None, str, str, str, int]],
) -> list[list[RustSearchResult]]: ...
def fetch_and_parse_search_batch(
    requests: list[tuple[str, str, str]],
) -> list[list[RustSearchResult]]: ...
def fetch_and_parse_reviews_batch(
    requests: list[tuple[str, str, str, int, str | None]],
) -> list[tuple[list[RustReview], str | None]]: ...

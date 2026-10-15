"""Generic HTTP transport with retries and JSON response handling."""

from typing import Any, TypeAlias, Union

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.config import Settings

JsonValue: TypeAlias = Union[
    None,
    bool,
    int,
    float,
    str,
    list["JsonValue"],
    dict[str, "JsonValue"],
]

RETRY_STATUS_CODES = (429, 500, 502, 503, 504)


class APIClient:
    """Reusable HTTP client configured with explicit application settings."""

    def __init__(
        self,
        settings: Settings | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.settings = settings or Settings.from_environment()
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "WorldOfWazeerDataIngestion/1.0",
                "Accept": "application/json",
            }
        )
        if self.settings.api_key:
            self.session.headers["X-API-Key"] = self.settings.api_key

        retry = Retry(
            total=self.settings.max_retries,
            backoff_factor=self.settings.backoff_factor,
            status_forcelist=RETRY_STATUS_CODES,
            allowed_methods=frozenset({"GET", "HEAD"}),
            respect_retry_after_header=True,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get(self, endpoint: str, **kwargs: Any) -> JsonValue:
        """GET an endpoint, checking HTTP status and returning parsed JSON."""
        url = f"{self.settings.base_url}/{endpoint.lstrip('/')}"
        timeout = kwargs.pop("timeout", self.settings.timeout)
        response = self.session.get(url, timeout=timeout, **kwargs)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        media_type = content_type.split(";", maxsplit=1)[0].strip().lower()
        main_type, separator, subtype = media_type.partition("/")
        is_json = separator and main_type == "application" and (
            subtype == "json" or (subtype.endswith("+json") and len(subtype) > len("+json"))
        )
        if not is_json:
            raise ValueError(f"Expected a JSON response, got {content_type or 'no content type'}")

        try:
            return response.json()
        except ValueError as exc:
            raise ValueError(f"Response from {endpoint} contained invalid JSON") from exc

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self.session.close()

    def __enter__(self) -> "APIClient":
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.close()

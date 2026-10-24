"""Generic HTTP transport with retries and JSON response handling."""

from typing import Any, TypeAlias

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.config import Settings

JsonValue: TypeAlias = (
    None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
)

RETRY_STATUS_CODES = (429, 500, 502, 503, 504)


class APIClientError(Exception):
    """Base class for safe, user-facing HTTP client failures."""


class APIConnectionError(APIClientError):
    """A connection could not be established or completed."""


class APITimeoutError(APIConnectionError):
    """The HTTP request exceeded its configured timeout."""


class APIHTTPError(APIClientError):
    """The server returned an unsuccessful HTTP status after retries."""

    def __init__(self, endpoint: str, status_code: int) -> None:
        self.endpoint = endpoint
        self.status_code = status_code
        super().__init__(f"GET {endpoint} returned HTTP {status_code}")


class APIResponseError(APIClientError):
    """The successful HTTP response was not usable JSON."""


class UnexpectedMediaTypeError(APIResponseError):
    """The server did not label its response as a supported JSON media type."""


class MalformedJSONError(APIResponseError):
    """The server labeled its response as JSON, but the body could not be parsed."""


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
        safe_endpoint = endpoint.split("?", maxsplit=1)[0]
        url = f"{self.settings.base_url}/{endpoint.lstrip('/')}"
        timeout = kwargs.pop("timeout", self.settings.timeout)
        try:
            response = self.session.get(url, timeout=timeout, **kwargs)
        except requests.Timeout as exc:
            raise APITimeoutError(f"GET {safe_endpoint} timed out") from exc
        except requests.ConnectionError as exc:
            raise APIConnectionError(f"GET {safe_endpoint} could not connect") from exc

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            status_code = response.status_code
            raise APIHTTPError(safe_endpoint, status_code) from exc

        content_type = response.headers.get("Content-Type", "")
        media_type = content_type.split(";", maxsplit=1)[0].strip().lower()
        main_type, separator, subtype = media_type.partition("/")
        is_json = (
            separator
            and main_type == "application"
            and (
                subtype == "json"
                or (subtype.endswith("+json") and len(subtype) > len("+json"))
            )
        )
        if not is_json:
            raise UnexpectedMediaTypeError(
                f"GET {safe_endpoint} returned an unsupported response media type"
            )

        try:
            return response.json()
        except ValueError as exc:
            raise MalformedJSONError(
                f"GET {safe_endpoint} returned malformed JSON"
            ) from exc

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self.session.close()

    def __enter__(self) -> "APIClient":
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.close()

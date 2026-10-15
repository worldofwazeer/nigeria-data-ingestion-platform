from unittest.mock import Mock

import pytest
import requests

from app.api_client import (
    APIClient,
    APIConnectionError,
    APIHTTPError,
    APITimeoutError,
    MalformedJSONError,
    UnexpectedMediaTypeError,
)
from app.config import Settings


def make_client() -> tuple[APIClient, Mock]:
    session = Mock(spec=requests.Session)
    session.headers = {}
    return APIClient(Settings(base_url="https://example.test"), session=session), session


def test_get_returns_json_and_uses_timeout() -> None:
    client, session = make_client()
    response = Mock()
    response.headers = {"Content-Type": "application/json; charset=utf-8"}
    response.json.return_value = {"ok": True}
    session.get.return_value = response

    assert client.get("/prices") == {"ok": True}
    session.get.assert_called_once_with("https://example.test/prices", timeout=15.0)
    response.raise_for_status.assert_called_once_with()


def test_get_propagates_http_error() -> None:
    client, session = make_client()
    response = Mock()
    response.status_code = 503
    response.raise_for_status.side_effect = requests.HTTPError(
        "upstream failed: https://example.test/prices?api_key=private-token",
        response=response,
    )
    session.get.return_value = response

    with pytest.raises(APIHTTPError) as error:
        client.get("/prices?api_key=private-token")

    assert error.value.status_code == 503
    assert str(error.value) == "GET /prices returned HTTP 503"
    assert isinstance(error.value.__cause__, requests.HTTPError)
    assert "private-token" not in str(error.value)


def test_get_rejects_non_json_and_malformed_json() -> None:
    client, session = make_client()
    response = Mock()
    response.headers = {"Content-Type": "text/plain"}
    session.get.return_value = response
    with pytest.raises(UnexpectedMediaTypeError, match="unsupported response media type"):
        client.get("prices")

    response.headers = {"Content-Type": "application/json"}
    parse_error = ValueError("invalid secret=private-token raw-body={...}")
    response.json.side_effect = parse_error
    with pytest.raises(MalformedJSONError, match="returned malformed JSON") as error:
        client.get("prices")
    assert error.value.__cause__ is parse_error
    assert "private-token" not in str(error.value)


@pytest.mark.parametrize(
    ("request_error", "expected_error"),
    [
        (requests.Timeout("timed out with api_key=private-token"), APITimeoutError),
        (requests.ConnectionError("failed URL has api_key=private-token"), APIConnectionError),
    ],
)
def test_get_wraps_connection_failures_without_leaking_request_details(
    request_error: requests.RequestException,
    expected_error: type[APIConnectionError],
) -> None:
    client, session = make_client()
    session.get.side_effect = request_error

    with pytest.raises(expected_error) as error:
        client.get("/prices?api_key=private-token")

    assert error.value.__cause__ is request_error
    assert "private-token" not in str(error.value)
    assert "api_key" not in str(error.value)


@pytest.mark.parametrize(
    "content_type",
    [
        "application/json",
        "Application/JSON; charset=utf-8",
        "application/problem+json; charset=utf-8",
        "application/vnd.example.record+json",
    ],
)
def test_get_accepts_json_media_types(content_type: str) -> None:
    client, session = make_client()
    response = Mock()
    response.headers = {"Content-Type": content_type}
    response.json.return_value = {"ok": True}
    session.get.return_value = response

    assert client.get("prices") == {"ok": True}


@pytest.mark.parametrize(
    "content_type",
    ["text/json", "application/notjson", "application/jsonp", "text/plain; note=json", ""],
)
def test_get_rejects_unrelated_json_looking_media_types(content_type: str) -> None:
    client, session = make_client()
    response = Mock()
    response.headers = {"Content-Type": content_type}
    session.get.return_value = response

    with pytest.raises(UnexpectedMediaTypeError, match="unsupported response media type"):
        client.get("prices")


def test_http_adapters_use_bounded_retry_policy() -> None:
    settings = Settings(
        base_url="https://example.test",
        max_retries=2,
        backoff_factor=0.25,
    )
    client = APIClient(settings)
    adapter = client.session.get_adapter("https://")
    retry = adapter.max_retries

    assert retry.total == 2
    assert retry.connect is None
    assert retry.read is None
    assert retry.status is None
    assert retry.status_forcelist == (429, 500, 502, 503, 504)
    assert retry.allowed_methods == frozenset({"GET", "HEAD"})
    assert retry.backoff_factor == 0.25
    assert retry.respect_retry_after_header is True
    assert retry.raise_on_status is False
    client.close()

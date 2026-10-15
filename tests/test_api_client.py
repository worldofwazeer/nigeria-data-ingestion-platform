from unittest.mock import Mock

import pytest
import requests

from app.api_client import APIClient
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
    response.raise_for_status.side_effect = requests.HTTPError("bad status")
    session.get.return_value = response

    with pytest.raises(requests.HTTPError):
        client.get("prices")


def test_get_rejects_non_json_and_malformed_json() -> None:
    client, session = make_client()
    response = Mock()
    response.headers = {"Content-Type": "text/plain"}
    session.get.return_value = response
    with pytest.raises(ValueError, match="Expected a JSON response"):
        client.get("prices")

    response.headers = {"Content-Type": "application/json"}
    response.json.side_effect = ValueError("invalid")
    with pytest.raises(ValueError, match="contained invalid JSON"):
        client.get("prices")


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

    with pytest.raises(ValueError, match="Expected a JSON response"):
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

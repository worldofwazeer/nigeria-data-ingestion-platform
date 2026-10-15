from contextlib import nullcontext

import pytest
from pydantic import ValidationError

from app import main
from app.api_client import (
    APIConnectionError,
    APIHTTPError,
    APITimeoutError,
    MalformedJSONError,
    UnexpectedMediaTypeError,
)


@pytest.mark.parametrize(
    ("failure", "expected_message"),
    [
        (APITimeoutError("timeout api_key=private-token"), "request timed out"),
        (APIConnectionError("failed api_key=private-token"), "could not connect"),
        (APIHTTPError("/prices?api_key=private-token", 503), "HTTP 503"),
        (UnexpectedMediaTypeError("unsafe?api_key=private-token"), "unsupported response media type"),
        (MalformedJSONError("unsafe?api_key=private-token raw body"), "malformed JSON"),
        (ValidationError.from_exception_data("OpaIndexResponse", []), "did not match the expected schema"),
        (ValueError("BASE_URL is required"), "configuration error"),
        (RuntimeError("https://host.test/prices?api_key=private-token raw body"), "unexpected RuntimeError"),
    ],
)
def test_main_reports_safe_failure_and_returns_nonzero(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    failure: Exception,
    expected_message: str,
) -> None:
    monkeypatch.setattr(main, "APIClient", lambda: nullcontext(object()))

    def fail_ingestion(client: object) -> object:
        raise failure

    monkeypatch.setattr(main, "ingest_opaindex_prices", fail_ingestion)

    assert main.main() == 1
    captured = capsys.readouterr()
    assert expected_message in captured.err
    assert "private-token" not in captured.err
    assert "raw body" not in captured.err
    assert captured.out == ""

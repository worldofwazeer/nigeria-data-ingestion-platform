from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from app import pipeline


def valid_response() -> dict:
    return {
        "prices": [
            {
                "slug": "palm-oil-lagos",
                "name": "Palm Oil",
                "category": "food-staples",
                "market": "Lagos",
                "unit": "25 litres",
                "price": 48000,
                "currency": "NGN",
                "dayChangePercent": -0.8,
                "weekChangePercent": 1.7,
                "source": "market survey",
                "asOf": "2026-06-23T08:00:00Z",
                "confidence": "medium",
            }
        ],
        "count": 1,
        "source": "seed",
        "asOf": "2026-06-23T08:00:00Z",
    }


class FakeConnector:
    def __init__(self, payload: object = None, error: Exception | None = None) -> None:
        self.payload = payload
        self.error = error

    def fetch_prices(self) -> object:
        if self.error:
            raise self.error
        return self.payload


def test_pipeline_fetches_and_validates(monkeypatch: pytest.MonkeyPatch) -> None:
    connector = FakeConnector(payload=valid_response())
    monkeypatch.setattr(pipeline, "OpaIndexConnector", lambda client: connector)

    result = pipeline.ingest_opaindex_prices(Mock())

    assert result.count == 1
    assert result.prices[0].name == "Palm Oil"


def test_pipeline_propagates_validation_error(monkeypatch: pytest.MonkeyPatch) -> None:
    connector = FakeConnector(payload=[])
    monkeypatch.setattr(pipeline, "OpaIndexConnector", lambda client: connector)

    with pytest.raises(ValidationError):
        pipeline.ingest_opaindex_prices(Mock())


def test_pipeline_does_not_swallow_connector_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    failure = RuntimeError("transport failed")
    connector = FakeConnector(error=failure)
    monkeypatch.setattr(pipeline, "OpaIndexConnector", lambda client: connector)

    with pytest.raises(RuntimeError) as error:
        pipeline.ingest_opaindex_prices(Mock())
    assert error.value is failure

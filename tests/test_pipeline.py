from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from app.pipeline import ingest_opaindex_prices


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


def test_pipeline_fetches_and_validates() -> None:
    client = Mock()
    client.get.return_value = valid_response()

    result = ingest_opaindex_prices(client)

    assert result.count == 1
    assert result.prices[0].name == "Palm Oil"
    client.get.assert_called_once_with("/prices")


def test_pipeline_propagates_validation_error() -> None:
    client = Mock()
    client.get.return_value = {"prices": []}

    with pytest.raises(ValidationError):
        ingest_opaindex_prices(client)


def test_pipeline_propagates_transport_error() -> None:
    client = Mock()
    client.get.side_effect = RuntimeError("transport failed")

    with pytest.raises(RuntimeError, match="transport failed"):
        ingest_opaindex_prices(client)

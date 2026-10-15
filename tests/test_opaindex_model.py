from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.opaindex import OpaIndexResponse


def test_opaindex_response_validation() -> None:
    raw_response = {
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
                "source": "Mile 12 & Daleko market survey",
                "asOf": "2026-06-23T08:00:00Z",
                "confidence": "medium",
            }
        ],
        "count": 1,
        "source": "seed",
        "asOf": "2026-06-23T08:00:00Z",
    }

    result = OpaIndexResponse.model_validate(raw_response)

    assert len(result.prices) == 1

    price = result.prices[0]

    assert price.name == "Palm Oil"
    assert price.currency == "NGN"
    assert price.day_change_percent == Decimal("-0.8")
    assert price.week_change_percent == Decimal("1.7")
    assert price.confidence == "medium"
    assert price.as_of == datetime(
        2026,
        6,
        23,
        8,
        0,
        tzinfo=timezone.utc,
    )


def test_opaindex_response_rejects_missing_required_fields() -> None:
    with pytest.raises(ValidationError):
        OpaIndexResponse.model_validate({"prices": [], "count": 0})


def test_opaindex_response_rejects_negative_price() -> None:
    raw = {
        "prices": [
            {
                "slug": "test",
                "name": "Test",
                "category": "food",
                "market": "Lagos",
                "unit": "kg",
                "price": -1,
                "currency": "NGN",
                "dayChangePercent": 0,
                "weekChangePercent": 0,
                "source": "survey",
                "asOf": "2026-06-23T08:00:00Z",
                "confidence": "medium",
            }
        ],
        "count": 1,
        "source": "seed",
        "asOf": "2026-06-23T08:00:00Z",
    }
    with pytest.raises(ValidationError):
        OpaIndexResponse.model_validate(raw)

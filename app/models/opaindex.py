from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PricePoint(BaseModel):
    """Validated OpaIndex price record."""

    model_config = ConfigDict(populate_by_name=True)

    slug: str = Field(min_length=1)
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    market: str = Field(min_length=1)
    unit: str = Field(min_length=1)

    price: Decimal = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)

    day_change_percent: Decimal = Field(
        validation_alias="dayChangePercent",
    )

    week_change_percent: Decimal = Field(
        validation_alias="weekChangePercent",
    )

    source: str = Field(min_length=1)

    as_of: datetime = Field(
        validation_alias="asOf",
    )

    confidence: Literal["high", "medium", "low"]


class OpaIndexResponse(BaseModel):
    """Validated response returned by the OpaIndex /prices endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    prices: list[PricePoint]
    count: int = Field(ge=0)
    source: Literal["db", "seed"]

    as_of: datetime = Field(
        validation_alias="asOf",
    )

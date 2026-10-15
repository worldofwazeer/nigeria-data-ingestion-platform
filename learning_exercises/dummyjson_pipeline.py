import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, ValidationError
from pydantic.alias_generators import to_camel

from api_client import APIClient

# SETUP: LOGGING & PYDANTIC MODELS
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
logger = logging.getLogger("ETL_PRACTICE")


class BaseSchema(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class Dimensions(BaseSchema):
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    depth: float = Field(gt=0)


class Review(BaseSchema):
    rating: float = Field(ge=0)
    comment: str = Field(min_length=1)
    date: datetime
    reviewer_email: EmailStr
    reviewer_name: str = Field(min_length=1)


class Meta(BaseSchema):
    created_at: datetime
    updated_at: datetime
    barcode: str = Field(min_length=1)
    qr_code: HttpUrl


class Product(BaseSchema):
    id: int = Field(gt=0)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    category: str = Field(min_length=1)
    price: float = Field(gt=0)
    discount_percentage: float = Field(ge=0)
    rating: float = Field(ge=0)
    stock: int = Field(ge=0)
    tags: list[str]
    brand: str | None = None
    sku: str = Field(min_length=1)
    weight: float = Field(gt=0)
    warranty_information: str = Field(min_length=1)
    shipping_information: str = Field(min_length=1)
    availability_status: str = Field(min_length=1)
    return_policy: str = Field(min_length=1)
    minimum_order_quantity: int = Field(gt=0)

    images: list[HttpUrl]
    thumbnail: HttpUrl
    dimensions: Dimensions
    meta: Meta
    reviews: list[Review] = Field(default_factory=list)


def extract_page(client: APIClient, skip: int, limit: int) -> list[dict[str, Any]]:
    """
    Extracts a single page of products from the API.

    Args:
        client (APIClient): Configured API client.
        skip (int): Number of records to skip.
        limit (int): Maximum records to retrieve.

    Returns:
        list[dict[str, Any]]: Raw product dictionaries returned by the API.
    """

    logger.info("[1/5] EXTRACT")

    data = client.get(
        "/prices",
        params={
            "limit": limit,
            "skip": skip,
        },
    )

    return data.get("prices", [])


def validate_products(raw_products: list[dict[str, Any]]) -> list[Product]:
    """
    Validates a list of raw dictionaries against the Pydantic Product schema.

    Records that fail schema validation are silently dropped from the pipeline.

    Args:
        raw_products (list[dict[str, Any]]): The unvalidated JSON data extracted from the API.

    Returns:
        list[Product]: A list of successfully validated Pydantic Product model instances.
    """
    logger.info("[2/5] VALIDATE: %d products", len(raw_products))
    valid = []

    for item in raw_products:
        try:
            valid.append(Product.model_validate(item))
        except ValidationError as e:
            logger.warning("Validation failed: %s", e)
            continue

    return valid


def transform(products: list[Product]) -> list[dict[str, Any]]:
    """
    Transforms validated Product models into a flattened dictionary structure.

    Selects specific fields required for the downstream load phase, stripping
    out unnecessary metadata.

    Args:
        products (list[Product]): Validated Pydantic objects.

    Returns:
        list[dict[str, Any]]: Transformed dictionaries ready for database insertion.
    """
    logger.info("[3/5] TRANSFORM: %d products", len(products))
    return [
        {
            "id": p.id,
            "title": p.title,
            "price": p.price,
            "thumbnail": str(p.thumbnail),
        }
        for p in products
    ]


def fetch_all_products(client: APIClient) -> list[dict[str, Any]]:
    """Orchestrates the full extraction, validation, and transformation pipeline.

    Loops through paginated API endpoints until all available records are exhausted,
    passing the data through the validation and transformation steps sequentially.

    Args:
        session (requests.Session): The active HTTP session to use for all requests.

    Returns:
        list[dict[str, Any]]: The complete, fully processed dataset.
    """
    limit = 20
    skip = 0
    final_dataset: list[dict[str, Any]] = []

    logger.info("Starting Ingestion Pipeline...")

    while True:
        # 1. Extract
        products = extract_page(client, skip, limit)
        if not products:
            logger.info("No more records found. Ingestion complete.")
            break

        # 2. Validate
        validated = validate_products(products)

        # 3. Transform
        transformed = transform(validated)
        final_dataset.extend(transformed)

        logger.info(
            "Processed page (skip=%d): %d rows | Running total: %d",
            skip,
            len(transformed),
            len(final_dataset),
        )

        skip += limit

    return final_dataset


def main() -> None:

    with APIClient() as client:
        data = fetch_all_products(client)

    print(f"Total records: {len(data)}")

    print("Sample:", data[0] if data else None)


if __name__ == "__main__":
    main()

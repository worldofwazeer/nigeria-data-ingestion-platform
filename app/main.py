"""Command-line entry point for fetching OpaIndex price data."""

from app.api_client import APIClient
from app.pipeline import ingest_opaindex_prices


def main() -> None:
    with APIClient() as client:
        response = ingest_opaindex_prices(client)
    print(f"Fetched {response.count} OpaIndex price records.")


if __name__ == "__main__":
    main()

"""OpaIndex ingestion orchestration."""

from app.api_client import APIClient
from app.connectors.opaindex import OpaIndexConnector
from app.models.opaindex import OpaIndexResponse


def ingest_opaindex_prices(client: APIClient) -> OpaIndexResponse:
    """Fetch OpaIndex prices and validate the source response contract."""
    raw_response = OpaIndexConnector(client).fetch_prices()
    return OpaIndexResponse.model_validate(raw_response)

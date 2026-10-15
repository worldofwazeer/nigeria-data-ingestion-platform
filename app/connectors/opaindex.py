from typing import Any

from app.api_client import APIClient


class OpaIndexConnector:
    """Connector for acquiring market price data from OpaIndex."""

    ENDPOINT = "/prices"

    def __init__(self, client: APIClient) -> None:
        self.client = client

    def fetch_prices(self) -> dict[str, Any]:
        """Fetch raw price data from OpaIndex."""
        payload = self.client.get(self.ENDPOINT)
        if not isinstance(payload, dict):
            raise ValueError("OpaIndex /prices response must be a JSON object")
        return payload

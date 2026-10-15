from app.api_client import APIClient, JsonValue


class OpaIndexConnector:
    """Connector for acquiring market price data from OpaIndex."""

    ENDPOINT = "/prices"

    def __init__(self, client: APIClient) -> None:
        self.client = client

    def fetch_prices(self) -> JsonValue:
        """Fetch raw price data from OpaIndex."""
        return self.client.get(self.ENDPOINT)

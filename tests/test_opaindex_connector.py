from unittest.mock import Mock

import pytest

from app.connectors.opaindex import OpaIndexConnector


def test_connector_delegates_to_prices_endpoint() -> None:
    client = Mock()
    client.get.return_value = {"prices": []}

    assert OpaIndexConnector(client).fetch_prices() == {"prices": []}
    client.get.assert_called_once_with("/prices")


def test_connector_returns_json_payload_without_schema_validation() -> None:
    client = Mock()
    client.get.return_value = []

    assert OpaIndexConnector(client).fetch_prices() == []

"""Unit tests for the APIClient module."""

from unittest.mock import MagicMock, patch

# pyrefly: ignore [missing-import]
import pytest
import requests
from requests.exceptions import ConnectionError as ReqConnectionError
from requests.exceptions import HTTPError, JSONDecodeError, Timeout

from report_generator.api_client import APIClient
from report_generator.exceptions import APIClientError


class TestAPIClient:
    """Test suite covering APIClient behaviors, error conditions, and normalization."""

    def test_mock_sales_data_protocol(self) -> None:
        """Verify built-in mock protocol returns valid populated records without network."""
        client = APIClient(base_url="mock://enterprise-sales-api")
        data = client.fetch_sales_data()
        assert isinstance(data, list)
        assert len(data) >= 30
        for item in data:
            assert "product" in item
            assert "category" in item
            assert "quantity" in item
            assert "unit_price" in item
            assert "revenue" in item
            assert item["revenue"] > 0

    @patch("requests.get")
    def test_api_fetch_success_list_payload(self, mock_get: MagicMock) -> None:
        """Verify successful API fetch when response is a JSON list."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"date": "2026-03-01", "product": "ThinkPad", "category": "Electronics", "quantity": 2, "unit_price": 50000.0, "revenue": 100000.0},
            {"date": "2026-03-02", "product": "Chair", "category": "Furniture", "quantity": 5, "unit_price": 4000.0, "revenue": 20000.0},
        ]
        mock_get.return_value = mock_response

        client = APIClient(base_url="https://api.example.com/sales", timeout=5)
        records = client.fetch_sales_data()

        assert len(records) == 2
        assert records[0]["product"] == "ThinkPad"
        assert records[0]["revenue"] == 100000.0
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_api_fetch_success_dict_wrapped_payload(self, mock_get: MagicMock) -> None:
        """Verify successful normalization when records are nested under 'data' key."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "data": [
                {"title": "Enterprise Server", "category": "Hardware", "stock": 4, "price": 80000.0, "total": 320000.0},
            ],
        }
        mock_get.return_value = mock_response

        client = APIClient(base_url="https://api.example.com/items")
        records = client.fetch_sales_data()

        assert len(records) == 1
        assert records[0]["product"] == "Enterprise Server"
        assert records[0]["category"] == "Hardware"
        assert records[0]["quantity"] == 4
        assert records[0]["revenue"] == 320000.0

    @patch("requests.get")
    def test_api_connection_error(self, mock_get: MagicMock) -> None:
        """Verify that connection failure raises APIClientError with appropriate message."""
        mock_get.side_effect = ReqConnectionError("Failed to establish a new connection")

        client = APIClient(base_url="https://unreachable.domain.org/sales")
        with pytest.raises(APIClientError) as exc_info:
            client.fetch_sales_data()

        assert "ERROR: Unable to connect to the data API." in str(exc_info.value)

    @patch("requests.get")
    def test_api_timeout_error(self, mock_get: MagicMock) -> None:
        """Verify that request timeout raises APIClientError."""
        mock_get.side_effect = Timeout("Request timed out")

        client = APIClient(base_url="https://slow.example.com", timeout=3)
        with pytest.raises(APIClientError) as exc_info:
            client.fetch_sales_data()

        assert "timed out after 3 seconds" in str(exc_info.value)

    @patch("requests.get")
    def test_api_http_error(self, mock_get: MagicMock) -> None:
        """Verify HTTP 500 status raises APIClientError."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = HTTPError("Internal Server Error")
        mock_get.return_value = mock_response

        client = APIClient(base_url="https://failing.example.com")
        with pytest.raises(APIClientError) as exc_info:
            client.fetch_sales_data()

        assert "ERROR: API returned HTTP status 500." in str(exc_info.value)

    @patch("requests.get")
    def test_api_invalid_json(self, mock_get: MagicMock) -> None:
        """Verify that non-JSON response raises APIClientError."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Expecting value", "<html>404 Not Found</html>", 0)
        mock_get.return_value = mock_response

        client = APIClient(base_url="https://api.example.com/bad-json")
        with pytest.raises(APIClientError) as exc_info:
            client.fetch_sales_data()

        assert "ERROR: Invalid JSON response received from API." in str(exc_info.value)

    @patch("requests.get")
    def test_api_empty_response(self, mock_get: MagicMock) -> None:
        """Verify empty records raise APIClientError."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        client = APIClient(base_url="https://api.example.com/empty")
        with pytest.raises(APIClientError) as exc_info:
            client.fetch_sales_data()

        assert "ERROR: API response contained no valid records." in str(exc_info.value)

    @patch("requests.get")
    def test_api_unexpected_payload_type(self, mock_get: MagicMock) -> None:
        """Verify primitive type payload raises APIClientError."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = 12345
        mock_get.return_value = mock_response

        client = APIClient(base_url="https://api.example.com/scalar")
        with pytest.raises(APIClientError) as exc_info:
            client.fetch_sales_data()

        assert "ERROR: Unexpected API response format" in str(exc_info.value)

    @patch("requests.get")
    def test_api_auth_token_header(self, mock_get: MagicMock) -> None:
        """Verify Authorization header is included when api_key is configured."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"product": "Widget", "category": "Test", "quantity": 1, "unit_price": 10.0, "revenue": 10.0}
        ]
        mock_get.return_value = mock_response

        client = APIClient(base_url="https://secure.example.com", api_key="secret-token-123")
        client.fetch_sales_data()

        call_kwargs = mock_get.call_args[1]
        assert "Authorization" in call_kwargs["headers"]
        assert call_kwargs["headers"]["Authorization"] == "Bearer secret-token-123"

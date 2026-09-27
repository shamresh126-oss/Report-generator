"""REST API Client for enterprise sales data fetching.

Handles HTTP requests, connection timeouts, retries, and errors with comprehensive
logging and data normalization.
"""

from typing import Any, Dict, List, Optional
import requests
from requests.exceptions import ConnectionError as ReqConnectionError
from requests.exceptions import HTTPError, JSONDecodeError, RequestException, Timeout

from report_generator.exceptions import APIClientError
from report_generator.logger import get_logger

logger = get_logger("api_client")


class APIClient:
    """Client for fetching sales and performance data from external REST APIs."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 10,
        api_key: Optional[str] = None,
    ) -> None:
        """Initialize the API client.

        Args:
            base_url: The root URL of the target API service.
            timeout: Maximum seconds to wait for a network response.
            api_key: Optional authentication token or API key.
        """
        self.base_url = (base_url or "https://dummyjson.com/c/mock-sales").strip()
        self.timeout = timeout
        self.api_key = api_key
        logger.debug(
            "APIClient initialized with base_url=%s, timeout=%ds",
            self.base_url,
            self.timeout,
        )

    def fetch_sales_data(self, endpoint: str = "") -> List[Dict[str, Any]]:
        """Fetch sales data from the configured REST API endpoint.

        Args:
            endpoint: Optional sub-path to append to the base URL.

        Returns:
            List[Dict[str, Any]]: Clean list of standardized record dictionaries.

        Raises:
            APIClientError: If connection fails, request times out, HTTP error occurs,
                            or response is not valid JSON.
        """
        # Built-in enterprise mock protocol support for offline or test environments
        if self.base_url.startswith("mock://") or self.base_url == "mock":
            logger.info("Using built-in enterprise mock sales service (%s)", self.base_url)
            return self.get_mock_sales_data()

        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}" if endpoint else self.base_url
        headers: Dict[str, str] = {
            "Accept": "application/json",
            "User-Agent": "EnterpriseReportGenerator/1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        logger.info("Executing API GET request to %s (timeout: %ds)", url, self.timeout)

        try:
            response = requests.get(url, headers=headers, timeout=self.timeout)
            logger.debug("Received HTTP status %d from %s", response.status_code, url)

            # Raise HTTPError for 4xx and 5xx responses
            response.raise_for_status()

            payload = response.json()
            return self._normalize_payload(payload)

        except ReqConnectionError as exc:
            msg = "ERROR: Unable to connect to the data API."
            logger.error("%s Details: %s", msg, exc)
            raise APIClientError(msg, original_exception=exc) from exc

        except Timeout as exc:
            msg = f"ERROR: API request timed out after {self.timeout} seconds."
            logger.error("%s Details: %s", msg, exc)
            raise APIClientError(msg, original_exception=exc) from exc

        except HTTPError as exc:
            status = response.status_code if "response" in locals() else "Unknown"
            msg = f"ERROR: API returned HTTP status {status}."
            logger.error("%s Details: %s", msg, exc)
            raise APIClientError(msg, original_exception=exc) from exc

        except JSONDecodeError as exc:
            msg = "ERROR: Invalid JSON response received from API."
            logger.error("%s Details: %s", msg, exc)
            raise APIClientError(msg, original_exception=exc) from exc

        except RequestException as exc:
            msg = f"ERROR: Network request failed: {exc}"
            logger.error(msg)
            raise APIClientError(msg, original_exception=exc) from exc

    def _normalize_payload(self, payload: Any) -> List[Dict[str, Any]]:
        """Extract and validate the record list from various JSON structures.

        Args:
            payload: Parsed JSON structure (dict or list).

        Returns:
            List of standardized dictionary records.

        Raises:
            APIClientError: If payload cannot be normalized into sales records.
        """
        raw_records: List[Any] = []

        if isinstance(payload, list):
            raw_records = payload
        elif isinstance(payload, dict):
            # Check common enterprise wrapper keys
            for key in ("data", "sales", "records", "items", "products", "results"):
                if key in payload and isinstance(payload[key], list):
                    raw_records = payload[key]
                    break
            else:
                # If single record wrapped in dictionary
                raw_records = [payload]
        else:
            raise APIClientError("ERROR: Unexpected API response format (expected list or dict).")

        normalized: List[Dict[str, Any]] = []
        for index, item in enumerate(raw_records):
            if not isinstance(item, dict):
                logger.warning("Skipping non-dictionary record at index %d: %s", index, item)
                continue

            # Standardize field names
            record = {
                "date": str(item.get("date", item.get("order_date", "2026-01-01"))),
                "product": str(item.get("product", item.get("title", item.get("name", "Unknown Product")))),
                "category": str(item.get("category", "General")),
                "quantity": int(item.get("quantity", item.get("stock", 1))),
                "unit_price": float(item.get("unit_price", item.get("price", 0.0))),
                "revenue": float(
                    item.get(
                        "revenue",
                        item.get("total", float(item.get("quantity", 1)) * float(item.get("unit_price", item.get("price", 0.0)))),
                    )
                ),
            }
            normalized.append(record)

        if not normalized:
            raise APIClientError("ERROR: API response contained no valid records.")

        logger.info("Successfully fetched and normalized %d records from API", len(normalized))
        return normalized

    @staticmethod
    def get_mock_sales_data() -> List[Dict[str, Any]]:
        """Generate a realistic mock sales dataset for testing and offline execution.

        Returns:
            List of sales record dictionaries.
        """
        return [
            {"date": "2026-01-10", "product": "ThinkPad X1 Carbon", "category": "Electronics", "quantity": 10, "unit_price": 125000.0, "revenue": 1250000.0},
            {"date": "2026-01-15", "product": "Ergonomic Mesh Chair", "category": "Furniture", "quantity": 20, "unit_price": 18500.0, "revenue": 370000.0},
            {"date": "2026-01-20", "product": "Enterprise Cloud Suite Annual", "category": "Cloud Services", "quantity": 5, "unit_price": 120000.0, "revenue": 600000.0},
            {"date": "2026-02-05", "product": "Dell UltraSharp 27 Monitor", "category": "Electronics", "quantity": 25, "unit_price": 34990.0, "revenue": 874750.0},
            {"date": "2026-02-12", "product": "CRM Automation License Pack", "category": "Enterprise Software", "quantity": 15, "unit_price": 65000.0, "revenue": 975000.0},
            {"date": "2026-02-18", "product": "Motorized Standing Desk", "category": "Furniture", "quantity": 12, "unit_price": 32000.0, "revenue": 384000.0},
            {"date": "2026-03-01", "product": "MacBook Pro 16 M3", "category": "Electronics", "quantity": 8, "unit_price": 249900.0, "revenue": 1999200.0},
            {"date": "2026-03-10", "product": "LaserJet Pro MFP Printer", "category": "Office Equipment", "quantity": 10, "unit_price": 28500.0, "revenue": 285000.0},
            {"date": "2026-03-15", "product": "Managed Kubernetes Cluster", "category": "Cloud Services", "quantity": 6, "unit_price": 95000.0, "revenue": 570000.0},
            {"date": "2026-03-25", "product": "BI Analytics Platform Seats", "category": "Enterprise Software", "quantity": 20, "unit_price": 22000.0, "revenue": 440000.0},
            {"date": "2026-04-05", "product": "Smart Whiteboard 65-inch", "category": "Office Equipment", "quantity": 4, "unit_price": 115000.0, "revenue": 460000.0},
            {"date": "2026-04-15", "product": "Logitech MX Master 3S", "category": "Electronics", "quantity": 40, "unit_price": 8995.0, "revenue": 359800.0},
            {"date": "2026-04-20", "product": "Cloud Storage Enterprise 10TB", "category": "Cloud Services", "quantity": 12, "unit_price": 45000.0, "revenue": 540000.0},
            {"date": "2026-05-02", "product": "Workflow Automation Suite", "category": "Enterprise Software", "quantity": 15, "unit_price": 34000.0, "revenue": 510000.0},
            {"date": "2026-05-15", "product": "Executive Boardroom Table", "category": "Furniture", "quantity": 2, "unit_price": 85000.0, "revenue": 170000.0},
            {"date": "2026-05-28", "product": "Network Attached Storage 48TB", "category": "Electronics", "quantity": 5, "unit_price": 135000.0, "revenue": 675000.0},
            {"date": "2026-06-08", "product": "High-Capacity Toner Cartridge", "category": "Office Equipment", "quantity": 30, "unit_price": 4800.0, "revenue": 144000.0},
            {"date": "2026-06-18", "product": "DevOps Pipeline CI/CD Engine", "category": "Cloud Services", "quantity": 8, "unit_price": 78000.0, "revenue": 624000.0},
            {"date": "2026-06-25", "product": "Dual Monitor Arm Mount", "category": "Furniture", "quantity": 20, "unit_price": 6800.0, "revenue": 136000.0},
            {"date": "2026-07-04", "product": "Cisco Gigabit Enterprise Switch", "category": "Electronics", "quantity": 7, "unit_price": 42000.0, "revenue": 294000.0},
            {"date": "2026-07-15", "product": "Noise-Cancelling Headset Pro", "category": "Electronics", "quantity": 35, "unit_price": 14500.0, "revenue": 507500.0},
            {"date": "2026-07-28", "product": "Air Purifier Commercial", "category": "Office Equipment", "quantity": 8, "unit_price": 24000.0, "revenue": 192000.0},
            {"date": "2026-08-05", "product": "Data Security Endpoint Pro", "category": "Enterprise Software", "quantity": 25, "unit_price": 15000.0, "revenue": 375000.0},
            {"date": "2026-08-16", "product": "Conference Room Audio Bar", "category": "Electronics", "quantity": 5, "unit_price": 54000.0, "revenue": 270000.0},
            {"date": "2026-08-25", "product": "Multi-Cloud Backup Service", "category": "Cloud Services", "quantity": 10, "unit_price": 52000.0, "revenue": 520000.0},
            {"date": "2026-09-02", "product": "Acoustic Privacy Panel Set", "category": "Furniture", "quantity": 14, "unit_price": 12500.0, "revenue": 175000.0},
            {"date": "2026-09-10", "product": "iPad Pro Enterprise Kit", "category": "Electronics", "quantity": 12, "unit_price": 89000.0, "revenue": 1068000.0},
            {"date": "2026-09-18", "product": "Thermal Label Printer", "category": "Office Equipment", "quantity": 12, "unit_price": 19800.0, "revenue": 237600.0},
            {"date": "2026-09-22", "product": "API Gateway Enterprise", "category": "Enterprise Software", "quantity": 6, "unit_price": 98000.0, "revenue": 588000.0},
            {"date": "2026-09-26", "product": "Virtual Desktop Infrastructure", "category": "Cloud Services", "quantity": 10, "unit_price": 64000.0, "revenue": 640000.0},
        ]

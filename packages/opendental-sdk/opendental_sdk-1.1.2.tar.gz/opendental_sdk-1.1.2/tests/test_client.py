"""
Tests for the OpenDentalClient class.
"""

import pytest
import responses
from unittest.mock import patch, Mock
from opendental import OpenDentalClient, OpenDentalAPIError


class TestOpenDentalClient:
    """Test cases for the OpenDentalClient class."""

    def test_client_initialization_with_keys(self):
        """Test client initialization with explicit API keys."""
        client = OpenDentalClient(
            developer_key="test_dev_key", customer_key="test_cust_key"
        )

        assert client.developer_key == "test_dev_key"
        assert client.customer_key == "test_cust_key"
        assert client.base_url == "https://api.opendental.com/api/v1"
        assert client.timeout == 30

    @patch.dict(
        "os.environ",
        {
            "OPENDENTAL_DEVELOPER_KEY": "env_dev_key",
            "OPENDENTAL_CUSTOMER_KEY": "env_cust_key",
        },
    )
    def test_client_initialization_with_env_vars(self):
        """Test client initialization with environment variables."""
        client = OpenDentalClient()

        assert client.developer_key == "env_dev_key"
        assert client.customer_key == "env_cust_key"

    def test_client_initialization_missing_keys(self):
        """Test client initialization fails without API keys."""
        with pytest.raises(
            ValueError, match="Both developer_key and customer_key are required"
        ):
            OpenDentalClient()

    def test_client_initialization_with_custom_config(self):
        """Test client initialization with custom configuration."""
        client = OpenDentalClient(
            developer_key="test_dev_key",
            customer_key="test_cust_key",
            base_url="https://custom.api.com",
            timeout=60,
            max_retries=5,
            debug=True,
        )

        assert client.base_url == "https://custom.api.com"
        assert client.timeout == 60
        assert client.debug is True

    def test_client_has_resource_managers(self):
        """Test that client has all resource managers initialized."""
        client = OpenDentalClient(
            developer_key="test_dev_key", customer_key="test_cust_key"
        )

        assert hasattr(client, "patients")
        assert hasattr(client, "appointments")
        assert hasattr(client, "claims")
        assert hasattr(client, "chart_modules")

    @responses.activate
    def test_get_request_success(self):
        """Test successful GET request."""
        responses.add(
            responses.GET,
            "https://api.opendental.com/api/v1/test",
            json={"result": "success"},
            status=200,
        )

        client = OpenDentalClient(
            developer_key="test_dev_key", customer_key="test_cust_key"
        )

        result = client.get("test")

        assert result == {"result": "success"}
        assert len(responses.calls) == 1
        assert (
            "ODFHIR test_dev_key/test_cust_key"
            in responses.calls[0].request.headers["Authorization"]
        )

    @responses.activate
    def test_post_request_success(self):
        """Test successful POST request."""
        responses.add(
            responses.POST,
            "https://api.opendental.com/api/v1/test",
            json={"id": 123, "created": True},
            status=201,
        )

        client = OpenDentalClient(
            developer_key="test_dev_key", customer_key="test_cust_key"
        )

        result = client.post("test", {"name": "Test"})

        assert result == {"id": 123, "created": True}

    @responses.activate
    def test_put_request_success(self):
        """Test successful PUT request."""
        responses.add(
            responses.PUT,
            "https://api.opendental.com/api/v1/test/123",
            json={"id": 123, "updated": True},
            status=200,
        )

        client = OpenDentalClient(
            developer_key="test_dev_key", customer_key="test_cust_key"
        )

        result = client.put("test/123", {"name": "Updated"})

        assert result == {"id": 123, "updated": True}

    @responses.activate
    def test_delete_request_success(self):
        """Test successful DELETE request."""
        responses.add(
            responses.DELETE, "https://api.opendental.com/api/v1/test/123", status=204
        )

        client = OpenDentalClient(
            developer_key="test_dev_key", customer_key="test_cust_key"
        )

        result = client.delete("test/123")

        assert result is None  # 204 No Content should return None

    @responses.activate
    def test_http_error_handling(self):
        """Test HTTP error handling."""
        responses.add(
            responses.GET,
            "https://api.opendental.com/api/v1/test",
            json={"message": "Not found"},
            status=404,
        )

        client = OpenDentalClient(
            developer_key="test_dev_key", customer_key="test_cust_key"
        )

        with pytest.raises(OpenDentalAPIError) as exc_info:
            client.get("test")

        assert exc_info.value.status_code == 404
        assert "Not found" in str(exc_info.value)

    @responses.activate
    def test_request_timeout_handling(self):
        """Test request timeout handling."""
        import requests.exceptions

        def timeout_callback(request):
            raise requests.exceptions.Timeout("Request timed out")

        responses.add_callback(
            responses.GET,
            "https://api.opendental.com/api/v1/test",
            callback=timeout_callback,
        )

        client = OpenDentalClient(
            developer_key="test_dev_key", customer_key="test_cust_key"
        )

        with pytest.raises(OpenDentalAPIError, match="Request failed"):
            client.get("test")

    def test_authorization_header_format(self):
        """Test that authorization header uses ODFHIR format."""
        client = OpenDentalClient(
            developer_key="dev_key_123", customer_key="customer_key_456"
        )

        expected_auth = "ODFHIR dev_key_123/customer_key_456"
        assert client.session.headers["Authorization"] == expected_auth

    def test_user_agent_header(self):
        """Test that user agent header is set correctly."""
        client = OpenDentalClient(developer_key="dev_key", customer_key="customer_key")

        assert client.session.headers["User-Agent"] == "opendental-python-sdk/1.0.0"

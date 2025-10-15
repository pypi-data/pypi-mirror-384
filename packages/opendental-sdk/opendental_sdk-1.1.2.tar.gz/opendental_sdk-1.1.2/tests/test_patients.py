"""
Tests for the PatientsResource class.
"""

import pytest
import responses
from opendental import OpenDentalClient, OpenDentalAPIError


class TestPatientsResource:
    """Test cases for the PatientsResource class."""

    @pytest.fixture
    def client(self):
        """Create a test client instance."""
        return OpenDentalClient(
            developer_key="test_dev_key", customer_key="test_cust_key"
        )

    @responses.activate
    def test_get_patient_success(self, client):
        """Test successful patient retrieval by ID."""
        patient_data = {
            "PatNum": 123,
            "LName": "Smith",
            "FName": "John",
            "Email": "john.smith@example.com",
        }

        responses.add(
            responses.GET,
            "https://api.opendental.com/api/v1/patients/123",
            json=patient_data,
            status=200,
        )

        result = client.patients.get(123)

        assert result == patient_data
        assert len(responses.calls) == 1

    @responses.activate
    def test_get_patient_not_found(self, client):
        """Test patient not found error."""
        responses.add(
            responses.GET,
            "https://api.opendental.com/api/v1/patients/999",
            json={"message": "Patient not found"},
            status=404,
        )

        with pytest.raises(OpenDentalAPIError) as exc_info:
            client.patients.get(999)

        assert exc_info.value.status_code == 404

    @responses.activate
    def test_search_patients_with_filters(self, client):
        """Test patient search with various filters."""
        search_results = [
            {"PatNum": 123, "LName": "Smith", "FName": "John"},
            {"PatNum": 124, "LName": "Smith", "FName": "Jane"},
        ]

        responses.add(
            responses.GET,
            "https://api.opendental.com/api/v1/patients",
            json=search_results,
            status=200,
        )

        result = client.patients.search(last_name="Smith", first_name="J", limit=10)

        assert result == search_results
        assert len(responses.calls) == 1

        # Check that query parameters were properly formatted
        request = responses.calls[0].request
        assert "LName=Smith" in request.url
        assert "FName=J" in request.url
        assert "limit=10" in request.url

    @responses.activate
    def test_search_patients_with_clinic_nums(self, client):
        """Test patient search with clinic numbers list."""
        responses.add(
            responses.GET,
            "https://api.opendental.com/api/v1/patients",
            json=[],
            status=200,
        )

        client.patients.search(clinic_nums=[1, 2, 3])

        request = responses.calls[0].request
        assert "clinicNums=1%2C2%2C3" in request.url  # URL encoded comma-separated list

    @responses.activate
    def test_search_simple_with_timestamp(self, client):
        """Test simple patient search with timestamp filtering."""
        search_results = [
            {"PatNum": 123, "LName": "Smith", "DateTStamp": "2024-01-15T10:00:00Z"}
        ]

        responses.add(
            responses.GET,
            "https://api.opendental.com/api/v1/patients/Simple",
            json=search_results,
            status=200,
        )

        result = client.patients.search_simple(
            last_name="Smith", date_timestamp_after="2024-01-01T00:00:00Z"
        )

        assert result == search_results
        request = responses.calls[0].request
        assert "DateTStamp=2024-01-01T00%3A00%3A00Z" in request.url

    @responses.activate
    def test_create_patient_success(self, client):
        """Test successful patient creation."""
        patient_data = {
            "LName": "Doe",
            "FName": "Jane",
            "Email": "jane.doe@example.com",
        }

        created_patient = {"PatNum": 456, **patient_data}

        responses.add(
            responses.POST,
            "https://api.opendental.com/api/v1/patients",
            json=created_patient,
            status=201,
        )

        result = client.patients.create(patient_data)

        assert result == created_patient
        assert len(responses.calls) == 1

    def test_create_patient_missing_required_fields(self, client):
        """Test patient creation with missing required fields."""
        patient_data = {
            "Email": "jane.doe@example.com"
            # Missing LName and FName
        }

        with pytest.raises(ValueError, match="Missing required fields"):
            client.patients.create(patient_data)

    @responses.activate
    def test_update_patient_success(self, client):
        """Test successful patient update."""
        update_data = {"Email": "newemail@example.com", "Phone": "555-1234"}

        updated_patient = {
            "PatNum": 123,
            "LName": "Smith",
            "FName": "John",
            **update_data,
        }

        responses.add(
            responses.PUT,
            "https://api.opendental.com/api/v1/patients/123",
            json=updated_patient,
            status=200,
        )

        result = client.patients.update(123, update_data)

        assert result == updated_patient

    @responses.activate
    def test_get_by_chart_number_found(self, client):
        """Test getting patient by chart number when found."""
        patient_data = {"PatNum": 123, "ChartNumber": "ABC123", "LName": "Smith"}

        responses.add(
            responses.GET,
            "https://api.opendental.com/api/v1/patients",
            json=[patient_data],
            status=200,
        )

        result = client.patients.get_by_chart_number("ABC123")

        assert result == patient_data
        request = responses.calls[0].request
        assert "ChartNumber=ABC123" in request.url
        assert "limit=1" in request.url

    @responses.activate
    def test_get_by_chart_number_not_found(self, client):
        """Test getting patient by chart number when not found."""
        responses.add(
            responses.GET,
            "https://api.opendental.com/api/v1/patients",
            json=[],
            status=200,
        )

        result = client.patients.get_by_chart_number("NOTFOUND")

        assert result is None

    @responses.activate
    def test_get_by_phone(self, client):
        """Test getting patients by phone number."""
        patients = [
            {"PatNum": 123, "Phone": "555-1234"},
            {"PatNum": 124, "Phone": "555-1234"},
        ]

        responses.add(
            responses.GET,
            "https://api.opendental.com/api/v1/patients",
            json=patients,
            status=200,
        )

        result = client.patients.get_by_phone("555-1234")

        assert result == patients
        request = responses.calls[0].request
        assert "Phone=555-1234" in request.url

    @responses.activate
    def test_get_by_email(self, client):
        """Test getting patients by email address."""
        patients = [{"PatNum": 123, "Email": "test@example.com"}]

        responses.add(
            responses.GET,
            "https://api.opendental.com/api/v1/patients",
            json=patients,
            status=200,
        )

        result = client.patients.get_by_email("test@example.com")

        assert result == patients
        request = responses.calls[0].request
        assert "Email=test%40example.com" in request.url

    @responses.activate
    def test_get_guarantors_only(self, client):
        """Test getting guarantor patients only."""
        guarantors = [{"PatNum": 123, "LName": "Smith", "Guarantor": 123}]

        responses.add(
            responses.GET,
            "https://api.opendental.com/api/v1/patients",
            json=guarantors,
            status=200,
        )

        result = client.patients.get_guarantors_only(last_name="Smith")

        assert result == guarantors
        request = responses.calls[0].request
        assert "guarOnly=True" in request.url
        assert "LName=Smith" in request.url

    @responses.activate
    def test_get_recent_modifications(self, client):
        """Test getting recently modified patients."""
        recent_patients = [{"PatNum": 123, "DateTStamp": "2024-01-15T10:00:00Z"}]

        responses.add(
            responses.GET,
            "https://api.opendental.com/api/v1/patients/Simple",
            json=recent_patients,
            status=200,
        )

        result = client.patients.get_recent_modifications(
            "2024-01-01T00:00:00Z", limit=50
        )

        assert result == recent_patients
        request = responses.calls[0].request
        assert "DateTStamp=2024-01-01T00%3A00%3A00Z" in request.url
        assert "limit=50" in request.url

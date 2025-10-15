"""
Tests for the AppointmentsResource class.
"""

import pytest
import responses
from opendental import OpenDentalClient, OpenDentalAPIError


class TestAppointmentsResource:
    """Test cases for the AppointmentsResource class."""

    @pytest.fixture
    def client(self):
        """Create a test client instance."""
        return OpenDentalClient(
            developer_key="test_dev_key", customer_key="test_cust_key"
        )

    @responses.activate
    def test_get_appointment_success(self, client):
        """Test successful appointment retrieval by ID."""
        appointment_data = {
            "AptNum": 123,
            "PatNum": 456,
            "AptDateTime": "2024-01-15T10:00:00",
            "ProvNum": 1,
            "AptStatus": "Scheduled",
        }

        responses.add(
            responses.GET,
            "https://api.opendental.com/api/v1/appointments/123",
            json=appointment_data,
            status=200,
        )

        result = client.appointments.get(123)

        assert result == appointment_data
        assert len(responses.calls) == 1

    @responses.activate
    def test_search_appointments_with_filters(self, client):
        """Test appointment search with various filters."""
        search_results = [
            {"AptNum": 123, "PatNum": 456, "AptStatus": "Scheduled"},
            {"AptNum": 124, "PatNum": 456, "AptStatus": "Complete"},
        ]

        responses.add(
            responses.GET,
            "https://api.opendental.com/api/v1/appointments",
            json=search_results,
            status=200,
        )

        result = client.appointments.search(
            patient_id=456,
            status="Scheduled",
            date_start="2024-01-01",
            date_end="2024-01-31",
            limit=10,
        )

        assert result == search_results
        request = responses.calls[0].request
        assert "PatNum=456" in request.url
        assert "AptStatus=Scheduled" in request.url
        assert "DateStart=2024-01-01" in request.url
        assert "DateEnd=2024-01-31" in request.url
        assert "limit=10" in request.url

    @responses.activate
    def test_get_asap_appointments(self, client):
        """Test getting ASAP appointments."""
        asap_appointments = [{"AptNum": 123, "PatNum": 456, "Priority": "ASAP"}]

        responses.add(
            responses.GET,
            "https://api.opendental.com/api/v1/appointments/asap",
            json=asap_appointments,
            status=200,
        )

        result = client.appointments.get_asap(patient_id=456, provider_id=1)

        assert result == asap_appointments
        request = responses.calls[0].request
        assert "PatNum=456" in request.url
        assert "ProvNum=1" in request.url

    @responses.activate
    def test_get_available_slots(self, client):
        """Test getting available appointment slots."""
        available_slots = [
            {"DateTime": "2024-01-15T10:00:00", "Available": True},
            {"DateTime": "2024-01-15T11:00:00", "Available": True},
        ]

        responses.add(
            responses.GET,
            "https://api.opendental.com/api/v1/appointments/slots",
            json=available_slots,
            status=200,
        )

        result = client.appointments.get_available_slots(
            provider_id=1,
            date_start="2024-01-15",
            date_end="2024-01-15",
            appointment_length=60,
        )

        assert result == available_slots
        request = responses.calls[0].request
        assert "ProvNum=1" in request.url
        assert "DateStart=2024-01-15" in request.url
        assert "DateEnd=2024-01-15" in request.url
        assert "Length=60" in request.url

    @responses.activate
    def test_get_web_schedule_slots(self, client):
        """Test getting web scheduling slots."""
        web_slots = [{"DateTime": "2024-01-15T14:00:00", "WebSchedulable": True}]

        responses.add(
            responses.GET,
            "https://api.opendental.com/api/v1/appointments/webschedslots",
            json=web_slots,
            status=200,
        )

        result = client.appointments.get_web_schedule_slots(
            provider_id=1,
            date_start="2024-01-15",
            date_end="2024-01-15",
            appointment_type_id=5,
        )

        assert result == web_slots
        request = responses.calls[0].request
        assert "ProvNum=1" in request.url
        assert "AppointmentTypeNum=5" in request.url

    @responses.activate
    def test_create_appointment_success(self, client):
        """Test successful appointment creation."""
        appointment_data = {
            "PatNum": 456,
            "AppointmentTypeNum": 1,
            "AptDateTime": "2024-01-15T10:00:00",
            "ProvNum": 1,
        }

        created_appointment = {
            "AptNum": 123,
            **appointment_data,
            "AptStatus": "Scheduled",
        }

        responses.add(
            responses.POST,
            "https://api.opendental.com/api/v1/appointments",
            json=created_appointment,
            status=201,
        )

        result = client.appointments.create(appointment_data)

        assert result == created_appointment

    def test_create_appointment_missing_patient(self, client):
        """Test appointment creation with missing PatNum."""
        appointment_data = {
            "AppointmentTypeNum": 1,
            "AptDateTime": "2024-01-15T10:00:00",
        }

        with pytest.raises(ValueError, match="Missing required fields"):
            client.appointments.create(appointment_data)

    def test_create_appointment_missing_type_and_procs(self, client):
        """Test appointment creation without AppointmentTypeNum or procNums."""
        appointment_data = {"PatNum": 456, "AptDateTime": "2024-01-15T10:00:00"}

        with pytest.raises(
            ValueError, match="Either AppointmentTypeNum or procNums is required"
        ):
            client.appointments.create(appointment_data)

    @responses.activate
    def test_create_planned_appointment(self, client):
        """Test creating a planned appointment."""
        planned_data = {"PatNum": 456, "Note": "Future treatment"}

        created_planned = {"PlannedAptNum": 789, **planned_data}

        responses.add(
            responses.POST,
            "https://api.opendental.com/api/v1/appointments/planned",
            json=created_planned,
            status=201,
        )

        result = client.appointments.create_planned(planned_data)

        assert result == created_planned

    @responses.activate
    def test_schedule_planned_appointment(self, client):
        """Test converting planned appointment to scheduled."""
        schedule_data = {"AptDateTime": "2024-01-15T10:00:00", "ProvNum": 1}

        scheduled_appointment = {
            "AptNum": 123,
            "PatNum": 456,
            **schedule_data,
            "AptStatus": "Scheduled",
        }

        responses.add(
            responses.POST,
            "https://api.opendental.com/api/v1/appointments/scheduleplanned",
            json=scheduled_appointment,
            status=201,
        )

        result = client.appointments.schedule_planned(789, schedule_data)

        assert result == scheduled_appointment

    @responses.activate
    def test_create_web_scheduled_appointment(self, client):
        """Test creating a web-scheduled appointment."""
        web_appointment_data = {
            "PatNum": 456,
            "AptDateTime": "2024-01-15T10:00:00",
            "ProvNum": 1,
            "WebScheduled": True,
        }

        created_web_appointment = {
            "AptNum": 123,
            **web_appointment_data,
            "AptStatus": "Scheduled",
        }

        responses.add(
            responses.POST,
            "https://api.opendental.com/api/v1/appointments/websched",
            json=created_web_appointment,
            status=201,
        )

        result = client.appointments.create_web_scheduled(web_appointment_data)

        assert result == created_web_appointment

    @responses.activate
    def test_update_appointment(self, client):
        """Test updating an appointment."""
        update_data = {"AptDateTime": "2024-01-15T11:00:00", "Note": "Updated time"}

        updated_appointment = {"AptNum": 123, "PatNum": 456, **update_data}

        responses.add(
            responses.PUT,
            "https://api.opendental.com/api/v1/appointments/123",
            json=updated_appointment,
            status=200,
        )

        result = client.appointments.update(123, update_data)

        assert result == updated_appointment

    @responses.activate
    def test_mark_broken(self, client):
        """Test marking appointment as broken."""
        broken_data = {"BrokenReason": "Patient cancelled"}

        broken_appointment = {"AptNum": 123, "AptStatus": "Broken", **broken_data}

        responses.add(
            responses.PUT,
            "https://api.opendental.com/api/v1/appointments/123/break",
            json=broken_appointment,
            status=200,
        )

        result = client.appointments.mark_broken(123, broken_data)

        assert result == broken_appointment

    @responses.activate
    def test_add_note(self, client):
        """Test adding a note to an appointment."""
        updated_appointment = {
            "AptNum": 123,
            "Note": "Patient prefers morning appointments",
        }

        responses.add(
            responses.PUT,
            "https://api.opendental.com/api/v1/appointments/123/note",
            json=updated_appointment,
            status=200,
        )

        result = client.appointments.add_note(
            123, "Patient prefers morning appointments"
        )

        assert result == updated_appointment

    @responses.activate
    def test_update_confirmation_status(self, client):
        """Test updating appointment confirmation status."""
        confirmed_appointment = {"AptNum": 123, "Confirmed": "Confirmed"}

        responses.add(
            responses.PUT,
            "https://api.opendental.com/api/v1/appointments/123/confirm",
            json=confirmed_appointment,
            status=200,
        )

        result = client.appointments.update_confirmation_status(123, "Confirmed")

        assert result == confirmed_appointment

    @responses.activate
    def test_get_by_patient(self, client):
        """Test getting appointments by patient ID."""
        patient_appointments = [
            {"AptNum": 123, "PatNum": 456, "AptStatus": "Scheduled"},
            {"AptNum": 124, "PatNum": 456, "AptStatus": "Complete"},
        ]

        responses.add(
            responses.GET,
            "https://api.opendental.com/api/v1/appointments",
            json=patient_appointments,
            status=200,
        )

        result = client.appointments.get_by_patient(456, "Scheduled")

        assert result == patient_appointments
        request = responses.calls[0].request
        assert "PatNum=456" in request.url
        assert "AptStatus=Scheduled" in request.url

    @responses.activate
    def test_get_scheduled(self, client):
        """Test getting scheduled appointments."""
        scheduled_appointments = [{"AptNum": 123, "AptStatus": "Scheduled"}]

        responses.add(
            responses.GET,
            "https://api.opendental.com/api/v1/appointments",
            json=scheduled_appointments,
            status=200,
        )

        result = client.appointments.get_scheduled(
            date_start="2024-01-01", date_end="2024-01-31"
        )

        assert result == scheduled_appointments
        request = responses.calls[0].request
        assert "AptStatus=Scheduled" in request.url
        assert "DateStart=2024-01-01" in request.url

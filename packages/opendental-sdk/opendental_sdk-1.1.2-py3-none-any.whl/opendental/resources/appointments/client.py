"""Appointments client for Open Dental SDK."""

from datetime import datetime, date
from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    Appointment,
    CreateAppointmentRequest,
    UpdateAppointmentRequest,
    AppointmentListResponse,
    AppointmentSearchRequest,
    AppointmentBlock
)


class AppointmentsClient(BaseResource):
    """Client for managing appointments in Open Dental."""
    
    def __init__(self, client):
        """Initialize the appointments client."""
        super().__init__(client, "appointments")
    
    def get(self, appointment_id: Union[int, str]) -> Appointment:
        """
        Get an appointment by ID.
        
        Args:
            appointment_id: The appointment ID
            
        Returns:
            Appointment: The appointment object
        """
        appointment_id = self._validate_id(appointment_id)
        endpoint = self._build_endpoint(appointment_id)
        response = self._get(endpoint)
        return self._handle_response(response, Appointment)
    
    def list(self, page: int = 1, per_page: int = 50) -> AppointmentListResponse:
        """
        List all appointments.
        
        Args:
            page: Page number (default: 1)
            per_page: Items per page (default: 50)
            
        Returns:
            AppointmentListResponse: List of appointments with pagination info
        """
        params = {
            "page": page,
            "per_page": per_page
        }
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return AppointmentListResponse(**response)
        elif isinstance(response, list):
            return AppointmentListResponse(
                appointments=[Appointment(**item) for item in response],
                total=len(response),
                page=page,
                per_page=per_page
            )
        else:
            return AppointmentListResponse(appointments=[], total=0, page=page, per_page=per_page)
    
    def create(self, appointment_data: CreateAppointmentRequest) -> Appointment:
        """
        Create a new appointment.
        
        Args:
            appointment_data: The appointment data to create
            
        Returns:
            Appointment: The created appointment object
        """
        endpoint = self._build_endpoint()
        data = appointment_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, Appointment)
    
    def update(self, appointment_id: Union[int, str], appointment_data: UpdateAppointmentRequest) -> Appointment:
        """
        Update an existing appointment.
        
        Args:
            appointment_id: The appointment ID
            appointment_data: The appointment data to update
            
        Returns:
            Appointment: The updated appointment object
        """
        appointment_id = self._validate_id(appointment_id)
        endpoint = self._build_endpoint(appointment_id)
        data = appointment_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, Appointment)
    
    def delete(self, appointment_id: Union[int, str]) -> bool:
        """
        Delete an appointment.
        
        Args:
            appointment_id: The appointment ID
            
        Returns:
            bool: True if deletion was successful
        """
        appointment_id = self._validate_id(appointment_id)
        endpoint = self._build_endpoint(appointment_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: AppointmentSearchRequest) -> AppointmentListResponse:
        """
        Search for appointments.
        
        Args:
            search_params: Search parameters
            
        Returns:
            AppointmentListResponse: List of matching appointments
        """
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return AppointmentListResponse(**response)
        elif isinstance(response, list):
            return AppointmentListResponse(
                appointments=[Appointment(**item) for item in response],
                total=len(response),
                page=search_params.page,
                per_page=search_params.per_page
            )
        else:
            return AppointmentListResponse(
                appointments=[], 
                total=0, 
                page=search_params.page, 
                per_page=search_params.per_page
            )
    
    def get_by_patient(self, patient_id: Union[int, str]) -> List[Appointment]:
        """
        Get appointments for a specific patient.
        
        Args:
            patient_id: Patient ID
            
        Returns:
            List[Appointment]: List of appointments for the patient
        """
        patient_id = int(self._validate_id(patient_id))
        search_params = AppointmentSearchRequest(patient_id=patient_id)
        result = self.search(search_params)
        return result.appointments
    
    def get_by_provider(self, provider_id: Union[int, str]) -> List[Appointment]:
        """
        Get appointments for a specific provider.
        
        Args:
            provider_id: Provider ID
            
        Returns:
            List[Appointment]: List of appointments for the provider
        """
        provider_id = int(self._validate_id(provider_id))
        search_params = AppointmentSearchRequest(provider_id=provider_id)
        result = self.search(search_params)
        return result.appointments
    
    def get_by_date_range(self, date_start: date, date_end: date) -> List[Appointment]:
        """
        Get appointments within a date range.
        
        Args:
            date_start: Start date
            date_end: End date
            
        Returns:
            List[Appointment]: List of appointments in the date range
        """
        search_params = AppointmentSearchRequest(
            date_start=date_start,
            date_end=date_end
        )
        result = self.search(search_params)
        return result.appointments
    
    def get_today(self) -> List[Appointment]:
        """
        Get today's appointments.
        
        Returns:
            List[Appointment]: List of today's appointments
        """
        today = date.today()
        return self.get_by_date_range(today, today)
    
    def get_upcoming(self, days: int = 7) -> List[Appointment]:
        """
        Get upcoming appointments.
        
        Args:
            days: Number of days ahead to look (default: 7)
            
        Returns:
            List[Appointment]: List of upcoming appointments
        """
        today = date.today()
        from datetime import timedelta
        end_date = today + timedelta(days=days)
        return self.get_by_date_range(today, end_date)
    
    def confirm(self, appointment_id: Union[int, str]) -> Appointment:
        """
        Confirm an appointment.
        
        Args:
            appointment_id: The appointment ID
            
        Returns:
            Appointment: The confirmed appointment
        """
        update_data = UpdateAppointmentRequest(confirmed=True)
        return self.update(appointment_id, update_data)
    
    def complete(self, appointment_id: Union[int, str]) -> Appointment:
        """
        Mark an appointment as complete.
        
        Args:
            appointment_id: The appointment ID
            
        Returns:
            Appointment: The completed appointment
        """
        update_data = UpdateAppointmentRequest(is_complete=True)
        return self.update(appointment_id, update_data)
    
    def get_schedule_blocks(self, operatory_id: int, date_start: date, date_end: date) -> List[AppointmentBlock]:
        """
        Get schedule blocks for an operatory.
        
        Args:
            operatory_id: Operatory ID
            date_start: Start date
            date_end: End date
            
        Returns:
            List[AppointmentBlock]: List of schedule blocks
        """
        endpoint = self._build_endpoint("schedule-blocks")
        params = {
            "operatory_id": operatory_id,
            "date_start": date_start.isoformat(),
            "date_end": date_end.isoformat()
        }
        response = self._get(endpoint, params=params)
        return self._handle_list_response(response, AppointmentBlock)
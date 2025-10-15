"""Appointment types client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    AppointmentType,
    CreateAppointmentTypeRequest,
    UpdateAppointmentTypeRequest,
    AppointmentTypeListResponse,
    AppointmentTypeSearchRequest
)


class AppointmentTypesClient(BaseResource):
    """Client for managing appointment types in Open Dental."""
    
    def __init__(self, client):
        """Initialize the appointment types client."""
        super().__init__(client, "appointment_types")
    
    def get(self, type_id: Union[int, str]) -> AppointmentType:
        """
        Get an appointment type by ID.
        
        Args:
            type_id: The appointment type ID
            
        Returns:
            AppointmentType: The appointment type object
        """
        type_id = self._validate_id(type_id)
        endpoint = self._build_endpoint(type_id)
        response = self._get(endpoint)
        return self._handle_response(response, AppointmentType)
    
    def list(self, page: int = 1, per_page: int = 50) -> AppointmentTypeListResponse:
        """
        List all appointment types.
        
        Args:
            page: Page number (default: 1)
            per_page: Items per page (default: 50)
            
        Returns:
            AppointmentTypeListResponse: List of appointment types with pagination info
        """
        params = {
            "page": page,
            "per_page": per_page
        }
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return AppointmentTypeListResponse(**response)
        elif isinstance(response, list):
            return AppointmentTypeListResponse(
                appointment_types=[AppointmentType(**item) for item in response],
                total=len(response),
                page=page,
                per_page=per_page
            )
        else:
            return AppointmentTypeListResponse(appointment_types=[], total=0, page=page, per_page=per_page)
    
    def create(self, type_data: CreateAppointmentTypeRequest) -> AppointmentType:
        """
        Create a new appointment type.
        
        Args:
            type_data: The appointment type data to create
            
        Returns:
            AppointmentType: The created appointment type object
        """
        endpoint = self._build_endpoint()
        data = type_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, AppointmentType)
    
    def update(self, type_id: Union[int, str], type_data: UpdateAppointmentTypeRequest) -> AppointmentType:
        """
        Update an existing appointment type.
        
        Args:
            type_id: The appointment type ID
            type_data: The appointment type data to update
            
        Returns:
            AppointmentType: The updated appointment type object
        """
        type_id = self._validate_id(type_id)
        endpoint = self._build_endpoint(type_id)
        data = type_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, AppointmentType)
    
    def delete(self, type_id: Union[int, str]) -> bool:
        """
        Delete an appointment type.
        
        Args:
            type_id: The appointment type ID
            
        Returns:
            bool: True if deletion was successful
        """
        type_id = self._validate_id(type_id)
        endpoint = self._build_endpoint(type_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: AppointmentTypeSearchRequest) -> AppointmentTypeListResponse:
        """
        Search for appointment types.
        
        Args:
            search_params: Search parameters
            
        Returns:
            AppointmentTypeListResponse: List of matching appointment types
        """
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return AppointmentTypeListResponse(**response)
        elif isinstance(response, list):
            return AppointmentTypeListResponse(
                appointment_types=[AppointmentType(**item) for item in response],
                total=len(response),
                page=search_params.page,
                per_page=search_params.per_page
            )
        else:
            return AppointmentTypeListResponse(
                appointment_types=[], 
                total=0, 
                page=search_params.page, 
                per_page=search_params.per_page
            )
    
    def get_active_types(self) -> List[AppointmentType]:
        """
        Get all active appointment types.
        
        Returns:
            List[AppointmentType]: List of active appointment types
        """
        search_params = AppointmentTypeSearchRequest(is_active=True)
        result = self.search(search_params)
        return result.appointment_types
    
    def get_by_duration(self, min_duration: int, max_duration: int) -> List[AppointmentType]:
        """
        Get appointment types by duration range.
        
        Args:
            min_duration: Minimum duration in minutes
            max_duration: Maximum duration in minutes
            
        Returns:
            List[AppointmentType]: List of matching appointment types
        """
        search_params = AppointmentTypeSearchRequest(
            duration_min=min_duration,
            duration_max=max_duration
        )
        result = self.search(search_params)
        return result.appointment_types
    
    def get_by_name(self, name: str) -> List[AppointmentType]:
        """
        Get appointment types by name.
        
        Args:
            name: Name to search for
            
        Returns:
            List[AppointmentType]: List of matching appointment types
        """
        search_params = AppointmentTypeSearchRequest(name=name)
        result = self.search(search_params)
        return result.appointment_types
"""Clinics client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    Clinic,
    CreateClinicRequest,
    UpdateClinicRequest,
    ClinicListResponse,
    ClinicSearchRequest
)


class ClinicsClient(BaseResource):
    """Client for managing clinics in Open Dental."""
    
    def __init__(self, client):
        """Initialize the clinics client."""
        super().__init__(client, "clinics")
    
    def get(self, clinic_id: Union[int, str]) -> Clinic:
        """
        Get a clinic by ID.
        
        Args:
            clinic_id: The clinic ID
            
        Returns:
            Clinic: The clinic object
        """
        clinic_id = self._validate_id(clinic_id)
        endpoint = self._build_endpoint(clinic_id)
        response = self._get(endpoint)
        return self._handle_response(response, Clinic)
    
    def list(self, page: int = 1, per_page: int = 50) -> ClinicListResponse:
        """
        List all clinics.
        
        Args:
            page: Page number (default: 1)
            per_page: Items per page (default: 50)
            
        Returns:
            ClinicListResponse: List of clinics with pagination info
        """
        params = {
            "page": page,
            "per_page": per_page
        }
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return ClinicListResponse(**response)
        elif isinstance(response, list):
            return ClinicListResponse(
                clinics=[Clinic(**item) for item in response],
                total=len(response),
                page=page,
                per_page=per_page
            )
        else:
            return ClinicListResponse(clinics=[], total=0, page=page, per_page=per_page)
    
    def create(self, clinic_data: CreateClinicRequest) -> Clinic:
        """
        Create a new clinic.
        
        Args:
            clinic_data: The clinic data to create
            
        Returns:
            Clinic: The created clinic object
        """
        endpoint = self._build_endpoint()
        data = clinic_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, Clinic)
    
    def update(self, clinic_id: Union[int, str], clinic_data: UpdateClinicRequest) -> Clinic:
        """
        Update an existing clinic.
        
        Args:
            clinic_id: The clinic ID
            clinic_data: The clinic data to update
            
        Returns:
            Clinic: The updated clinic object
        """
        clinic_id = self._validate_id(clinic_id)
        endpoint = self._build_endpoint(clinic_id)
        data = clinic_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, Clinic)
    
    def delete(self, clinic_id: Union[int, str]) -> bool:
        """
        Delete a clinic.
        
        Args:
            clinic_id: The clinic ID
            
        Returns:
            bool: True if deletion was successful
        """
        clinic_id = self._validate_id(clinic_id)
        endpoint = self._build_endpoint(clinic_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: ClinicSearchRequest) -> ClinicListResponse:
        """
        Search for clinics.
        
        Args:
            search_params: Search parameters
            
        Returns:
            ClinicListResponse: List of matching clinics
        """
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return ClinicListResponse(**response)
        elif isinstance(response, list):
            return ClinicListResponse(
                clinics=[Clinic(**item) for item in response],
                total=len(response),
                page=search_params.page,
                per_page=search_params.per_page
            )
        else:
            return ClinicListResponse(
                clinics=[], 
                total=0, 
                page=search_params.page, 
                per_page=search_params.per_page
            )
    
    def get_by_description(self, description: str) -> List[Clinic]:
        """
        Get clinics by description.
        
        Args:
            description: Clinic description to search for
            
        Returns:
            List[Clinic]: List of clinics with matching description
        """
        search_params = ClinicSearchRequest(description=description)
        result = self.search(search_params)
        return result.clinics
    
    def get_by_abbreviation(self, abbreviation: str) -> List[Clinic]:
        """
        Get clinics by abbreviation.
        
        Args:
            abbreviation: Clinic abbreviation to search for
            
        Returns:
            List[Clinic]: List of clinics with matching abbreviation
        """
        search_params = ClinicSearchRequest(abbreviation=abbreviation)
        result = self.search(search_params)
        return result.clinics
    
    def get_by_state(self, state: str) -> List[Clinic]:
        """
        Get clinics by state.
        
        Args:
            state: State to search for
            
        Returns:
            List[Clinic]: List of clinics in the state
        """
        search_params = ClinicSearchRequest(state=state)
        result = self.search(search_params)
        return result.clinics
    
    def get_active(self) -> List[Clinic]:
        """
        Get all active (non-hidden) clinics.
        
        Returns:
            List[Clinic]: List of active clinics
        """
        search_params = ClinicSearchRequest(is_hidden=False)
        result = self.search(search_params)
        return result.clinics
    
    def get_medical_clinics(self) -> List[Clinic]:
        """
        Get all medical clinics.
        
        Returns:
            List[Clinic]: List of medical clinics
        """
        search_params = ClinicSearchRequest(is_medical=True)
        result = self.search(search_params)
        return result.clinics
    
    def get_dental_clinics(self) -> List[Clinic]:
        """
        Get all dental clinics.
        
        Returns:
            List[Clinic]: List of dental clinics
        """
        search_params = ClinicSearchRequest(is_medical=False)
        result = self.search(search_params)
        return result.clinics
    
    def hide_clinic(self, clinic_id: Union[int, str]) -> Clinic:
        """
        Hide a clinic.
        
        Args:
            clinic_id: The clinic ID
            
        Returns:
            Clinic: The updated clinic object
        """
        update_data = UpdateClinicRequest(is_hidden=True)
        return self.update(clinic_id, update_data)
    
    def unhide_clinic(self, clinic_id: Union[int, str]) -> Clinic:
        """
        Unhide a clinic.
        
        Args:
            clinic_id: The clinic ID
            
        Returns:
            Clinic: The updated clinic object
        """
        update_data = UpdateClinicRequest(is_hidden=False)
        return self.update(clinic_id, update_data)
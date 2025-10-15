"""Patients client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    Patient,
    CreatePatientRequest,
    UpdatePatientRequest,
    PatientListResponse,
    PatientSearchRequest
)


class PatientsClient(BaseResource):
    """Client for managing patients in Open Dental."""
    
    def __init__(self, client):
        """Initialize the patients client."""
        super().__init__(client, "patients")
    
    def get(self, patient_id: Union[int, str]) -> Patient:
        """
        Get a patient by ID.
        
        Args:
            patient_id: The patient ID
            
        Returns:
            Patient: The patient object
        """
        patient_id = self._validate_id(patient_id)
        endpoint = self._build_endpoint(patient_id)
        response = self._get(endpoint)
        return self._handle_response(response, Patient)
    
    def list(self, page: int = 1, per_page: int = 50) -> PatientListResponse:
        """
        List all patients.
        
        Args:
            page: Page number (default: 1)
            per_page: Items per page (default: 50)
            
        Returns:
            PatientListResponse: List of patients with pagination info
        """
        params = {
            "page": page,
            "per_page": per_page
        }
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return PatientListResponse(**response)
        elif isinstance(response, list):
            return PatientListResponse(
                patients=[Patient(**item) for item in response],
                total=len(response),
                page=page,
                per_page=per_page
            )
        else:
            return PatientListResponse(patients=[], total=0, page=page, per_page=per_page)
    
    def create(self, patient_data: CreatePatientRequest) -> Patient:
        """
        Create a new patient.
        
        Args:
            patient_data: The patient data to create
            
        Returns:
            Patient: The created patient object
        """
        endpoint = self._build_endpoint()
        data = patient_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, Patient)
    
    def update(self, patient_id: Union[int, str], patient_data: UpdatePatientRequest) -> Patient:
        """
        Update an existing patient.
        
        Args:
            patient_id: The patient ID
            patient_data: The patient data to update
            
        Returns:
            Patient: The updated patient object
        """
        patient_id = self._validate_id(patient_id)
        endpoint = self._build_endpoint(patient_id)
        data = patient_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, Patient)
    
    def delete(self, patient_id: Union[int, str]) -> bool:
        """
        Delete a patient.
        
        Args:
            patient_id: The patient ID
            
        Returns:
            bool: True if deletion was successful
        """
        patient_id = self._validate_id(patient_id)
        endpoint = self._build_endpoint(patient_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: PatientSearchRequest) -> PatientListResponse:
        """
        Search for patients.
        
        Args:
            search_params: Search parameters
            
        Returns:
            PatientListResponse: List of matching patients
        """
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return PatientListResponse(**response)
        elif isinstance(response, list):
            return PatientListResponse(
                patients=[Patient(**item) for item in response],
                total=len(response),
                page=search_params.page,
                per_page=search_params.per_page
            )
        else:
            return PatientListResponse(
                patients=[], 
                total=0, 
                page=search_params.page, 
                per_page=search_params.per_page
            )
    
    def get_by_email(self, email: str) -> List[Patient]:
        """
        Get patients by email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            List[Patient]: List of patients with matching email
        """
        search_params = PatientSearchRequest(email=email)
        result = self.search(search_params)
        return result.patients
    
    def get_by_phone(self, phone: str) -> List[Patient]:
        """
        Get patients by phone number.
        
        Args:
            phone: Phone number to search for
            
        Returns:
            List[Patient]: List of patients with matching phone
        """
        search_params = PatientSearchRequest(phone=phone)
        result = self.search(search_params)
        return result.patients
    
    def get_by_name(self, first_name: Optional[str] = None, last_name: Optional[str] = None) -> List[Patient]:
        """
        Get patients by name.
        
        Args:
            first_name: First name to search for
            last_name: Last name to search for
            
        Returns:
            List[Patient]: List of patients with matching name
        """
        search_params = PatientSearchRequest(
            first_name=first_name,
            last_name=last_name
        )
        result = self.search(search_params)
        return result.patients
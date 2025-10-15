"""Medications client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    Medication,
    CreateMedicationRequest,
    UpdateMedicationRequest,
    MedicationListResponse,
    MedicationSearchRequest
)


class MedicationsClient(BaseResource):
    """Client for managing medications in Open Dental."""
    
    def __init__(self, client):
        """Initialize the medications client."""
        super().__init__(client, "medications")
    
    def get(self, medication_id: Union[int, str]) -> Medication:
        """
        Get a medication by ID.
        
        Args:
            medication_id: The medication ID
            
        Returns:
            Medication: The medication object
        """
        medication_id = self._validate_id(medication_id)
        endpoint = self._build_endpoint(medication_id)
        response = self._get(endpoint)
        return self._handle_response(response, Medication)
    
    def list(self, page: int = 1, per_page: int = 50) -> MedicationListResponse:
        """
        List all medications.
        
        Args:
            page: Page number (default: 1)
            per_page: Items per page (default: 50)
            
        Returns:
            MedicationListResponse: List of medications with pagination info
        """
        params = {
            "page": page,
            "per_page": per_page
        }
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return MedicationListResponse(**response)
        elif isinstance(response, list):
            return MedicationListResponse(
                medications=[Medication(**item) for item in response],
                total=len(response),
                page=page,
                per_page=per_page
            )
        else:
            return MedicationListResponse(medications=[], total=0, page=page, per_page=per_page)
    
    def create(self, medication_data: CreateMedicationRequest) -> Medication:
        """
        Create a new medication.
        
        Args:
            medication_data: The medication data to create
            
        Returns:
            Medication: The created medication object
        """
        endpoint = self._build_endpoint()
        data = medication_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, Medication)
    
    def update(self, medication_id: Union[int, str], medication_data: UpdateMedicationRequest) -> Medication:
        """
        Update an existing medication.
        
        Args:
            medication_id: The medication ID
            medication_data: The medication data to update
            
        Returns:
            Medication: The updated medication object
        """
        medication_id = self._validate_id(medication_id)
        endpoint = self._build_endpoint(medication_id)
        data = medication_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, Medication)
    
    def delete(self, medication_id: Union[int, str]) -> bool:
        """
        Delete a medication.
        
        Args:
            medication_id: The medication ID
            
        Returns:
            bool: True if deletion was successful
        """
        medication_id = self._validate_id(medication_id)
        endpoint = self._build_endpoint(medication_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: MedicationSearchRequest) -> MedicationListResponse:
        """
        Search for medications.
        
        Args:
            search_params: Search parameters
            
        Returns:
            MedicationListResponse: List of matching medications
        """
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return MedicationListResponse(**response)
        elif isinstance(response, list):
            return MedicationListResponse(
                medications=[Medication(**item) for item in response],
                total=len(response),
                page=search_params.page,
                per_page=search_params.per_page
            )
        else:
            return MedicationListResponse(
                medications=[], 
                total=0, 
                page=search_params.page, 
                per_page=search_params.per_page
            )
    
    def get_by_patient(self, pat_num: int) -> List[Medication]:
        """
        Get medications for a specific patient.
        
        Args:
            pat_num: Patient number
            
        Returns:
            List[Medication]: List of medications for the patient
        """
        search_params = MedicationSearchRequest(pat_num=pat_num)
        result = self.search(search_params)
        return result.medications
    
    def get_active_by_patient(self, pat_num: int) -> List[Medication]:
        """
        Get active medications for a specific patient.
        
        Args:
            pat_num: Patient number
            
        Returns:
            List[Medication]: List of active medications for the patient
        """
        search_params = MedicationSearchRequest(pat_num=pat_num, is_active=True)
        result = self.search(search_params)
        return result.medications
    
    def get_by_name(self, med_name: str) -> List[Medication]:
        """
        Get medications by name.
        
        Args:
            med_name: Medication name to search for
            
        Returns:
            List[Medication]: List of medications with matching name
        """
        search_params = MedicationSearchRequest(med_name=med_name)
        result = self.search(search_params)
        return result.medications
    
    def get_by_generic_name(self, generic_name: str) -> List[Medication]:
        """
        Get medications by generic name.
        
        Args:
            generic_name: Generic name to search for
            
        Returns:
            List[Medication]: List of medications with matching generic name
        """
        search_params = MedicationSearchRequest(generic_name=generic_name)
        result = self.search(search_params)
        return result.medications
    
    def get_by_rx_cui(self, rx_cui: str) -> List[Medication]:
        """
        Get medications by RxNorm CUI.
        
        Args:
            rx_cui: RxNorm CUI to search for
            
        Returns:
            List[Medication]: List of medications with matching RxNorm CUI
        """
        search_params = MedicationSearchRequest(rx_cui=rx_cui)
        result = self.search(search_params)
        return result.medications
    
    def discontinue_medication(self, medication_id: Union[int, str]) -> Medication:
        """
        Discontinue a medication.
        
        Args:
            medication_id: The medication ID
            
        Returns:
            Medication: The updated medication object
        """
        from datetime import date
        update_data = UpdateMedicationRequest(
            is_active=False,
            date_stop=date.today()
        )
        return self.update(medication_id, update_data)
    
    def reactivate_medication(self, medication_id: Union[int, str]) -> Medication:
        """
        Reactivate a medication.
        
        Args:
            medication_id: The medication ID
            
        Returns:
            Medication: The updated medication object
        """
        update_data = UpdateMedicationRequest(
            is_active=True,
            date_stop=None
        )
        return self.update(medication_id, update_data)
"""Allergies client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    Allergy,
    CreateAllergyRequest,
    UpdateAllergyRequest,
    AllergyListResponse,
    AllergySearchRequest
)


class AllergiesClient(BaseResource):
    """Client for managing allergies in Open Dental."""
    
    def __init__(self, client):
        """Initialize the allergies client."""
        super().__init__(client, "allergies")
    
    def get(self, allergy_id: Union[int, str]) -> Allergy:
        """
        Get an allergy by ID.
        
        Args:
            allergy_id: The allergy ID
            
        Returns:
            Allergy: The allergy object
        """
        allergy_id = self._validate_id(allergy_id)
        endpoint = self._build_endpoint(allergy_id)
        response = self._get(endpoint)
        return self._handle_response(response, Allergy)
    
    def list(self, page: int = 1, per_page: int = 50) -> AllergyListResponse:
        """
        List all allergies.
        
        Args:
            page: Page number (default: 1)
            per_page: Items per page (default: 50)
            
        Returns:
            AllergyListResponse: List of allergies with pagination info
        """
        params = {
            "page": page,
            "per_page": per_page
        }
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return AllergyListResponse(**response)
        elif isinstance(response, list):
            return AllergyListResponse(
                allergies=[Allergy(**item) for item in response],
                total=len(response),
                page=page,
                per_page=per_page
            )
        else:
            return AllergyListResponse(allergies=[], total=0, page=page, per_page=per_page)
    
    def create(self, allergy_data: CreateAllergyRequest) -> Allergy:
        """
        Create a new allergy.
        
        Args:
            allergy_data: The allergy data to create
            
        Returns:
            Allergy: The created allergy object
        """
        endpoint = self._build_endpoint()
        data = allergy_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, Allergy)
    
    def update(self, allergy_id: Union[int, str], allergy_data: UpdateAllergyRequest) -> Allergy:
        """
        Update an existing allergy.
        
        Args:
            allergy_id: The allergy ID
            allergy_data: The allergy data to update
            
        Returns:
            Allergy: The updated allergy object
        """
        allergy_id = self._validate_id(allergy_id)
        endpoint = self._build_endpoint(allergy_id)
        data = allergy_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, Allergy)
    
    def delete(self, allergy_id: Union[int, str]) -> bool:
        """
        Delete an allergy.
        
        Args:
            allergy_id: The allergy ID
            
        Returns:
            bool: True if deletion was successful
        """
        allergy_id = self._validate_id(allergy_id)
        endpoint = self._build_endpoint(allergy_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: AllergySearchRequest) -> AllergyListResponse:
        """
        Search for allergies.
        
        Args:
            search_params: Search parameters
            
        Returns:
            AllergyListResponse: List of matching allergies
        """
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return AllergyListResponse(**response)
        elif isinstance(response, list):
            return AllergyListResponse(
                allergies=[Allergy(**item) for item in response],
                total=len(response),
                page=search_params.page,
                per_page=search_params.per_page
            )
        else:
            return AllergyListResponse(
                allergies=[], 
                total=0, 
                page=search_params.page, 
                per_page=search_params.per_page
            )
    
    def get_by_patient(self, pat_num: int) -> List[Allergy]:
        """
        Get allergies for a specific patient.
        
        Args:
            pat_num: Patient number
            
        Returns:
            List[Allergy]: List of allergies for the patient
        """
        search_params = AllergySearchRequest(pat_num=pat_num)
        result = self.search(search_params)
        return result.allergies
    
    def get_active_by_patient(self, pat_num: int) -> List[Allergy]:
        """
        Get active allergies for a specific patient.
        
        Args:
            pat_num: Patient number
            
        Returns:
            List[Allergy]: List of active allergies for the patient
        """
        search_params = AllergySearchRequest(pat_num=pat_num, is_active=True)
        result = self.search(search_params)
        return result.allergies
    
    def get_by_allergen(self, allergen: str) -> List[Allergy]:
        """
        Get allergies by allergen name.
        
        Args:
            allergen: Allergen name
            
        Returns:
            List[Allergy]: List of allergies with matching allergen
        """
        search_params = AllergySearchRequest(allergen=allergen)
        result = self.search(search_params)
        return result.allergies
    
    def deactivate_allergy(self, allergy_id: Union[int, str]) -> Allergy:
        """
        Deactivate an allergy.
        
        Args:
            allergy_id: The allergy ID
            
        Returns:
            Allergy: The updated allergy object
        """
        update_data = UpdateAllergyRequest(is_active=False)
        return self.update(allergy_id, update_data)
    
    def activate_allergy(self, allergy_id: Union[int, str]) -> Allergy:
        """
        Activate an allergy.
        
        Args:
            allergy_id: The allergy ID
            
        Returns:
            Allergy: The updated allergy object
        """
        update_data = UpdateAllergyRequest(is_active=True)
        return self.update(allergy_id, update_data)
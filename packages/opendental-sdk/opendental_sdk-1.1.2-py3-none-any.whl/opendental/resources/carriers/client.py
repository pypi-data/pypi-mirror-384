"""Carriers client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    Carrier,
    CreateCarrierRequest,
    UpdateCarrierRequest,
    CarrierListResponse,
    CarrierSearchRequest
)


class CarriersClient(BaseResource):
    """Client for managing insurance carriers in Open Dental."""
    
    def __init__(self, client):
        """Initialize the carriers client."""
        super().__init__(client, "carriers")
    
    def get(self, carrier_id: Union[int, str]) -> Carrier:
        """
        Get a carrier by ID.
        
        Args:
            carrier_id: The carrier ID
            
        Returns:
            Carrier: The carrier object
        """
        carrier_id = self._validate_id(carrier_id)
        endpoint = self._build_endpoint(carrier_id)
        response = self._get(endpoint)
        return self._handle_response(response, Carrier)
    
    def list(self, page: int = 1, per_page: int = 50) -> CarrierListResponse:
        """
        List all carriers.
        
        Args:
            page: Page number (default: 1)
            per_page: Items per page (default: 50)
            
        Returns:
            CarrierListResponse: List of carriers with pagination info
        """
        params = {
            "page": page,
            "per_page": per_page
        }
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return CarrierListResponse(**response)
        elif isinstance(response, list):
            return CarrierListResponse(
                carriers=[Carrier(**item) for item in response],
                total=len(response),
                page=page,
                per_page=per_page
            )
        else:
            return CarrierListResponse(carriers=[], total=0, page=page, per_page=per_page)
    
    def create(self, carrier_data: CreateCarrierRequest) -> Carrier:
        """
        Create a new carrier.
        
        Args:
            carrier_data: The carrier data to create
            
        Returns:
            Carrier: The created carrier object
        """
        endpoint = self._build_endpoint()
        data = carrier_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, Carrier)
    
    def update(self, carrier_id: Union[int, str], carrier_data: UpdateCarrierRequest) -> Carrier:
        """
        Update an existing carrier.
        
        Args:
            carrier_id: The carrier ID
            carrier_data: The carrier data to update
            
        Returns:
            Carrier: The updated carrier object
        """
        carrier_id = self._validate_id(carrier_id)
        endpoint = self._build_endpoint(carrier_id)
        data = carrier_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, Carrier)
    
    def delete(self, carrier_id: Union[int, str]) -> bool:
        """
        Delete a carrier.
        
        Args:
            carrier_id: The carrier ID
            
        Returns:
            bool: True if deletion was successful
        """
        carrier_id = self._validate_id(carrier_id)
        endpoint = self._build_endpoint(carrier_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: CarrierSearchRequest) -> CarrierListResponse:
        """
        Search for carriers.
        
        Args:
            search_params: Search parameters
            
        Returns:
            CarrierListResponse: List of matching carriers
        """
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return CarrierListResponse(**response)
        elif isinstance(response, list):
            return CarrierListResponse(
                carriers=[Carrier(**item) for item in response],
                total=len(response),
                page=search_params.page,
                per_page=search_params.per_page
            )
        else:
            return CarrierListResponse(
                carriers=[], 
                total=0, 
                page=search_params.page, 
                per_page=search_params.per_page
            )
    
    def get_by_name(self, carrier_name: str) -> List[Carrier]:
        """
        Get carriers by name.
        
        Args:
            carrier_name: Carrier name to search for
            
        Returns:
            List[Carrier]: List of carriers with matching name
        """
        search_params = CarrierSearchRequest(carrier_name=carrier_name)
        result = self.search(search_params)
        return result.carriers
    
    def get_by_state(self, state: str) -> List[Carrier]:
        """
        Get carriers by state.
        
        Args:
            state: State to search for
            
        Returns:
            List[Carrier]: List of carriers in the state
        """
        search_params = CarrierSearchRequest(state=state)
        result = self.search(search_params)
        return result.carriers
    
    def get_active(self) -> List[Carrier]:
        """
        Get all active (non-hidden) carriers.
        
        Returns:
            List[Carrier]: List of active carriers
        """
        search_params = CarrierSearchRequest(is_hidden=False)
        result = self.search(search_params)
        return result.carriers
    
    def get_by_electronic_id(self, electronic_id: str) -> List[Carrier]:
        """
        Get carriers by electronic ID.
        
        Args:
            electronic_id: Electronic ID to search for
            
        Returns:
            List[Carrier]: List of carriers with matching electronic ID
        """
        search_params = CarrierSearchRequest(electronic_id=electronic_id)
        result = self.search(search_params)
        return result.carriers
    
    def hide_carrier(self, carrier_id: Union[int, str]) -> Carrier:
        """
        Hide a carrier.
        
        Args:
            carrier_id: The carrier ID
            
        Returns:
            Carrier: The updated carrier object
        """
        update_data = UpdateCarrierRequest(is_hidden=True)
        return self.update(carrier_id, update_data)
    
    def unhide_carrier(self, carrier_id: Union[int, str]) -> Carrier:
        """
        Unhide a carrier.
        
        Args:
            carrier_id: The carrier ID
            
        Returns:
            Carrier: The updated carrier object
        """
        update_data = UpdateCarrierRequest(is_hidden=False)
        return self.update(carrier_id, update_data)
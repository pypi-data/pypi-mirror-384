"""computers client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    Computer,
    CreateComputerRequest,
    UpdateComputerRequest,
    ComputerListResponse,
    ComputerSearchRequest
)


class ComputersClient(BaseResource):
    """Client for managing computer/workstations in Open Dental."""
    
    def __init__(self, client):
        """Initialize the computer/workstations client."""
        super().__init__(client, "computers")
    
    def get(self, item_id: Union[int, str]) -> Computer:
        """Get a computer/workstation by ID."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._get(endpoint)
        return self._handle_response(response, Computer)
    
    def list(self, page: int = 1, per_page: int = 50) -> ComputerListResponse:
        """List all computer/workstations."""
        params = {"page": page, "per_page": per_page}
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return ComputerListResponse(**response)
        elif isinstance(response, list):
            return ComputerListResponse(
                computers=[Computer(**item) for item in response],
                total=len(response), page=page, per_page=per_page
            )
        return ComputerListResponse(computers=[], total=0, page=page, per_page=per_page)
    
    def create(self, item_data: CreateComputerRequest) -> Computer:
        """Create a new computer/workstation."""
        endpoint = self._build_endpoint()
        data = item_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, Computer)
    
    def update(self, item_id: Union[int, str], item_data: UpdateComputerRequest) -> Computer:
        """Update an existing computer/workstation."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        data = item_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, Computer)
    
    def delete(self, item_id: Union[int, str]) -> bool:
        """Delete a computer/workstation."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: ComputerSearchRequest) -> ComputerListResponse:
        """Search for computer/workstations."""
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return ComputerListResponse(**response)
        elif isinstance(response, list):
            return ComputerListResponse(
                computers=[Computer(**item) for item in response],
                total=len(response), page=search_params.page, per_page=search_params.per_page
            )
        return ComputerListResponse(
            computers=[], total=0, page=search_params.page, per_page=search_params.per_page
        )

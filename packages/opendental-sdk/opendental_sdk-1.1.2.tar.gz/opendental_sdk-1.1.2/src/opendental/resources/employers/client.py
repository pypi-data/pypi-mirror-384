"""employers client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    Employer,
    CreateEmployerRequest,
    UpdateEmployerRequest,
    EmployerListResponse,
    EmployerSearchRequest
)


class EmployersClient(BaseResource):
    """Client for managing employers in Open Dental."""
    
    def __init__(self, client):
        """Initialize the employers client."""
        super().__init__(client, "employers")
    
    def get(self, item_id: Union[int, str]) -> Employer:
        """Get a employer by ID."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._get(endpoint)
        return self._handle_response(response, Employer)
    
    def list(self, page: int = 1, per_page: int = 50) -> EmployerListResponse:
        """List all employers."""
        params = {"page": page, "per_page": per_page}
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return EmployerListResponse(**response)
        elif isinstance(response, list):
            return EmployerListResponse(
                employers=[Employer(**item) for item in response],
                total=len(response), page=page, per_page=per_page
            )
        return EmployerListResponse(employers=[], total=0, page=page, per_page=per_page)
    
    def create(self, item_data: CreateEmployerRequest) -> Employer:
        """Create a new employer."""
        endpoint = self._build_endpoint()
        data = item_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, Employer)
    
    def update(self, item_id: Union[int, str], item_data: UpdateEmployerRequest) -> Employer:
        """Update an existing employer."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        data = item_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, Employer)
    
    def delete(self, item_id: Union[int, str]) -> bool:
        """Delete a employer."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: EmployerSearchRequest) -> EmployerListResponse:
        """Search for employers."""
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return EmployerListResponse(**response)
        elif isinstance(response, list):
            return EmployerListResponse(
                employers=[Employer(**item) for item in response],
                total=len(response), page=search_params.page, per_page=search_params.per_page
            )
        return EmployerListResponse(
            employers=[], total=0, page=search_params.page, per_page=search_params.per_page
        )

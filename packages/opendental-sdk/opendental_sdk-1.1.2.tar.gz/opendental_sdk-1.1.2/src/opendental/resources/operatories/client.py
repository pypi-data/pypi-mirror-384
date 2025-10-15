"""operatorys client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    Operatory,
    CreateOperatoryRequest,
    UpdateOperatoryRequest,
    OperatoryListResponse,
    OperatorySearchRequest
)


class OperatorysClient(BaseResource):
    """Client for managing operatory/rooms in Open Dental."""
    
    def __init__(self, client):
        """Initialize the operatory/rooms client."""
        super().__init__(client, "operatories")
    
    def get(self, item_id: Union[int, str]) -> Operatory:
        """Get a operatory/room by ID."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._get(endpoint)
        return self._handle_response(response, Operatory)
    
    def list(self, page: int = 1, per_page: int = 50) -> OperatoryListResponse:
        """List all operatory/rooms."""
        params = {"page": page, "per_page": per_page}
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return OperatoryListResponse(**response)
        elif isinstance(response, list):
            return OperatoryListResponse(
                operatories=[Operatory(**item) for item in response],
                total=len(response), page=page, per_page=per_page
            )
        return OperatoryListResponse(operatories=[], total=0, page=page, per_page=per_page)
    
    def create(self, item_data: CreateOperatoryRequest) -> Operatory:
        """Create a new operatory/room."""
        endpoint = self._build_endpoint()
        data = item_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, Operatory)
    
    def update(self, item_id: Union[int, str], item_data: UpdateOperatoryRequest) -> Operatory:
        """Update an existing operatory/room."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        data = item_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, Operatory)
    
    def delete(self, item_id: Union[int, str]) -> bool:
        """Delete a operatory/room."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: OperatorySearchRequest) -> OperatoryListResponse:
        """Search for operatory/rooms."""
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return OperatoryListResponse(**response)
        elif isinstance(response, list):
            return OperatoryListResponse(
                operatories=[Operatory(**item) for item in response],
                total=len(response), page=search_params.page, per_page=search_params.per_page
            )
        return OperatoryListResponse(
            operatories=[], total=0, page=search_params.page, per_page=search_params.per_page
        )

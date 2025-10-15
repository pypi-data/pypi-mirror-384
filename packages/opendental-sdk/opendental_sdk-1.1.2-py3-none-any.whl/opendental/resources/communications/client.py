"""communications client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    Communication,
    CreateCommunicationRequest,
    UpdateCommunicationRequest,
    CommunicationListResponse,
    CommunicationSearchRequest
)


class CommunicationsClient(BaseResource):
    """Client for managing communication logs in Open Dental."""
    
    def __init__(self, client):
        """Initialize the communication logs client."""
        super().__init__(client, "communications")
    
    def get(self, item_id: Union[int, str]) -> Communication:
        """Get a communication log by ID."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._get(endpoint)
        return self._handle_response(response, Communication)
    
    def list(self, page: int = 1, per_page: int = 50) -> CommunicationListResponse:
        """List all communication logs."""
        params = {"page": page, "per_page": per_page}
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return CommunicationListResponse(**response)
        elif isinstance(response, list):
            return CommunicationListResponse(
                communications=[Communication(**item) for item in response],
                total=len(response), page=page, per_page=per_page
            )
        return CommunicationListResponse(communications=[], total=0, page=page, per_page=per_page)
    
    def create(self, item_data: CreateCommunicationRequest) -> Communication:
        """Create a new communication log."""
        endpoint = self._build_endpoint()
        data = item_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, Communication)
    
    def update(self, item_id: Union[int, str], item_data: UpdateCommunicationRequest) -> Communication:
        """Update an existing communication log."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        data = item_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, Communication)
    
    def delete(self, item_id: Union[int, str]) -> bool:
        """Delete a communication log."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: CommunicationSearchRequest) -> CommunicationListResponse:
        """Search for communication logs."""
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return CommunicationListResponse(**response)
        elif isinstance(response, list):
            return CommunicationListResponse(
                communications=[Communication(**item) for item in response],
                total=len(response), page=search_params.page, per_page=search_params.per_page
            )
        return CommunicationListResponse(
            communications=[], total=0, page=search_params.page, per_page=search_params.per_page
        )

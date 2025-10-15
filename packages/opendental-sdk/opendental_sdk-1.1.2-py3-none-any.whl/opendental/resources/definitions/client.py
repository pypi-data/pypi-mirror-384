"""definitions client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    Definition,
    CreateDefinitionRequest,
    UpdateDefinitionRequest,
    DefinitionListResponse,
    DefinitionSearchRequest
)


class DefinitionsClient(BaseResource):
    """Client for managing system definitions in Open Dental."""
    
    def __init__(self, client):
        """Initialize the system definitions client."""
        super().__init__(client, "definitions")
    
    def get(self, item_id: Union[int, str]) -> Definition:
        """Get a system definition by ID."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._get(endpoint)
        return self._handle_response(response, Definition)
    
    def list(self, page: int = 1, per_page: int = 50) -> DefinitionListResponse:
        """List all system definitions."""
        params = {"page": page, "per_page": per_page}
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return DefinitionListResponse(**response)
        elif isinstance(response, list):
            return DefinitionListResponse(
                definitions=[Definition(**item) for item in response],
                total=len(response), page=page, per_page=per_page
            )
        return DefinitionListResponse(definitions=[], total=0, page=page, per_page=per_page)
    
    def create(self, item_data: CreateDefinitionRequest) -> Definition:
        """Create a new system definition."""
        endpoint = self._build_endpoint()
        data = item_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, Definition)
    
    def update(self, item_id: Union[int, str], item_data: UpdateDefinitionRequest) -> Definition:
        """Update an existing system definition."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        data = item_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, Definition)
    
    def delete(self, item_id: Union[int, str]) -> bool:
        """Delete a system definition."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: DefinitionSearchRequest) -> DefinitionListResponse:
        """Search for system definitions."""
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return DefinitionListResponse(**response)
        elif isinstance(response, list):
            return DefinitionListResponse(
                definitions=[Definition(**item) for item in response],
                total=len(response), page=search_params.page, per_page=search_params.per_page
            )
        return DefinitionListResponse(
            definitions=[], total=0, page=search_params.page, per_page=search_params.per_page
        )

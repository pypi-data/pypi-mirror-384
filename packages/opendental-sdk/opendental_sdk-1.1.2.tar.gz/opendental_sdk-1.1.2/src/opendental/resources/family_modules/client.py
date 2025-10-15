"""familymodules client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    FamilyModule,
    CreateFamilyModuleRequest,
    UpdateFamilyModuleRequest,
    FamilyModuleListResponse,
    FamilyModuleSearchRequest
)


class FamilyModulesClient(BaseResource):
    """Client for managing family modules in Open Dental."""
    
    def __init__(self, client):
        """Initialize the family modules client."""
        super().__init__(client, "family_modules")
    
    def get(self, item_id: Union[int, str]) -> FamilyModule:
        """Get a family module by ID."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._get(endpoint)
        return self._handle_response(response, FamilyModule)
    
    def list(self, page: int = 1, per_page: int = 50) -> FamilyModuleListResponse:
        """List all family modules."""
        params = {"page": page, "per_page": per_page}
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return FamilyModuleListResponse(**response)
        elif isinstance(response, list):
            return FamilyModuleListResponse(
                family_modules=[FamilyModule(**item) for item in response],
                total=len(response), page=page, per_page=per_page
            )
        return FamilyModuleListResponse(family_modules=[], total=0, page=page, per_page=per_page)
    
    def create(self, item_data: CreateFamilyModuleRequest) -> FamilyModule:
        """Create a new family module."""
        endpoint = self._build_endpoint()
        data = item_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, FamilyModule)
    
    def update(self, item_id: Union[int, str], item_data: UpdateFamilyModuleRequest) -> FamilyModule:
        """Update an existing family module."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        data = item_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, FamilyModule)
    
    def delete(self, item_id: Union[int, str]) -> bool:
        """Delete a family module."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: FamilyModuleSearchRequest) -> FamilyModuleListResponse:
        """Search for family modules."""
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return FamilyModuleListResponse(**response)
        elif isinstance(response, list):
            return FamilyModuleListResponse(
                family_modules=[FamilyModule(**item) for item in response],
                total=len(response), page=search_params.page, per_page=search_params.per_page
            )
        return FamilyModuleListResponse(
            family_modules=[], total=0, page=search_params.page, per_page=search_params.per_page
        )

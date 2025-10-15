"""diseases client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    Disease,
    CreateDiseaseRequest,
    UpdateDiseaseRequest,
    DiseaseListResponse,
    DiseaseSearchRequest
)


class DiseasesClient(BaseResource):
    """Client for managing disease/conditions in Open Dental."""
    
    def __init__(self, client):
        """Initialize the disease/conditions client."""
        super().__init__(client, "diseases")
    
    def get(self, item_id: Union[int, str]) -> Disease:
        """Get a disease/condition by ID."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._get(endpoint)
        return self._handle_response(response, Disease)
    
    def list(self, page: int = 1, per_page: int = 50) -> DiseaseListResponse:
        """List all disease/conditions."""
        params = {"page": page, "per_page": per_page}
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return DiseaseListResponse(**response)
        elif isinstance(response, list):
            return DiseaseListResponse(
                diseases=[Disease(**item) for item in response],
                total=len(response), page=page, per_page=per_page
            )
        return DiseaseListResponse(diseases=[], total=0, page=page, per_page=per_page)
    
    def create(self, item_data: CreateDiseaseRequest) -> Disease:
        """Create a new disease/condition."""
        endpoint = self._build_endpoint()
        data = item_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, Disease)
    
    def update(self, item_id: Union[int, str], item_data: UpdateDiseaseRequest) -> Disease:
        """Update an existing disease/condition."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        data = item_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, Disease)
    
    def delete(self, item_id: Union[int, str]) -> bool:
        """Delete a disease/condition."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: DiseaseSearchRequest) -> DiseaseListResponse:
        """Search for disease/conditions."""
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return DiseaseListResponse(**response)
        elif isinstance(response, list):
            return DiseaseListResponse(
                diseases=[Disease(**item) for item in response],
                total=len(response), page=search_params.page, per_page=search_params.per_page
            )
        return DiseaseListResponse(
            diseases=[], total=0, page=search_params.page, per_page=search_params.per_page
        )

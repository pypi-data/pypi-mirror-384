"""labcases client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    LabCase,
    CreateLabCaseRequest,
    UpdateLabCaseRequest,
    LabCaseListResponse,
    LabCaseSearchRequest
)


class LabCasesClient(BaseResource):
    """Client for managing laboratory cases in Open Dental."""
    
    def __init__(self, client):
        """Initialize the laboratory cases client."""
        super().__init__(client, "lab_cases")
    
    def get(self, item_id: Union[int, str]) -> LabCase:
        """Get a laboratory case by ID."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._get(endpoint)
        return self._handle_response(response, LabCase)
    
    def list(self, page: int = 1, per_page: int = 50) -> LabCaseListResponse:
        """List all laboratory cases."""
        params = {"page": page, "per_page": per_page}
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return LabCaseListResponse(**response)
        elif isinstance(response, list):
            return LabCaseListResponse(
                lab_cases=[LabCase(**item) for item in response],
                total=len(response), page=page, per_page=per_page
            )
        return LabCaseListResponse(lab_cases=[], total=0, page=page, per_page=per_page)
    
    def create(self, item_data: CreateLabCaseRequest) -> LabCase:
        """Create a new laboratory case."""
        endpoint = self._build_endpoint()
        data = item_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, LabCase)
    
    def update(self, item_id: Union[int, str], item_data: UpdateLabCaseRequest) -> LabCase:
        """Update an existing laboratory case."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        data = item_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, LabCase)
    
    def delete(self, item_id: Union[int, str]) -> bool:
        """Delete a laboratory case."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: LabCaseSearchRequest) -> LabCaseListResponse:
        """Search for laboratory cases."""
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return LabCaseListResponse(**response)
        elif isinstance(response, list):
            return LabCaseListResponse(
                lab_cases=[LabCase(**item) for item in response],
                total=len(response), page=search_params.page, per_page=search_params.per_page
            )
        return LabCaseListResponse(
            lab_cases=[], total=0, page=search_params.page, per_page=search_params.per_page
        )

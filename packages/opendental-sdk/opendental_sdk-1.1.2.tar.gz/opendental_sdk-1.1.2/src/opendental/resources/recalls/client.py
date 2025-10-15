"""recalls client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    Recall,
    CreateRecallRequest,
    UpdateRecallRequest,
    RecallListResponse,
    RecallSearchRequest
)


class RecallsClient(BaseResource):
    """Client for managing recalls in Open Dental."""
    
    def __init__(self, client):
        """Initialize the recalls client."""
        super().__init__(client, "recalls")
    
    def get(self, item_id: Union[int, str]) -> Recall:
        """Get a recall by ID."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._get(endpoint)
        return self._handle_response(response, Recall)
    
    def list(self, page: int = 1, per_page: int = 50) -> RecallListResponse:
        """List all recalls."""
        params = {"page": page, "per_page": per_page}
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return RecallListResponse(**response)
        elif isinstance(response, list):
            return RecallListResponse(
                recalls=[Recall(**item) for item in response],
                total=len(response), page=page, per_page=per_page
            )
        return RecallListResponse(recalls=[], total=0, page=page, per_page=per_page)
    
    def create(self, item_data: CreateRecallRequest) -> Recall:
        """Create a new recall."""
        endpoint = self._build_endpoint()
        data = item_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, Recall)
    
    def update(self, item_id: Union[int, str], item_data: UpdateRecallRequest) -> Recall:
        """Update an existing recall."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        data = item_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, Recall)
    
    def delete(self, item_id: Union[int, str]) -> bool:
        """Delete a recall."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: RecallSearchRequest) -> RecallListResponse:
        """Search for recalls."""
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return RecallListResponse(**response)
        elif isinstance(response, list):
            return RecallListResponse(
                recalls=[Recall(**item) for item in response],
                total=len(response), page=search_params.page, per_page=search_params.per_page
            )
        return RecallListResponse(
            recalls=[], total=0, page=search_params.page, per_page=search_params.per_page
        )

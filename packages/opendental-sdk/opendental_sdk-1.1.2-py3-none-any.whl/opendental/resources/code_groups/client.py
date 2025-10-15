"""Code groups client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    CodeGroup,
    CreateCodeGroupRequest,
    UpdateCodeGroupRequest,
    CodeGroupListResponse
)


class CodeGroupsClient(BaseResource):
    """Client for managing code groups in Open Dental."""
    
    def __init__(self, client):
        """Initialize the code groups client."""
        super().__init__(client, "codegroups")
    
    def get(self, item_id: Union[int, str]) -> CodeGroup:
        """Get a code group by ID."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._get(endpoint)
        return self._handle_response(response, CodeGroup)
    
    def list(self, page: int = 1, per_page: int = 50) -> CodeGroupListResponse:
        """List all code groups."""
        params = {"page": page, "per_page": per_page}
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return CodeGroupListResponse(**response)
        elif isinstance(response, list):
            return CodeGroupListResponse(
                code_groups=[CodeGroup(**item) for item in response],
                total=len(response), page=page, per_page=per_page
            )
        return CodeGroupListResponse(code_groups=[], total=0, page=page, per_page=per_page)
    
    def create(self, item_data: CreateCodeGroupRequest) -> CodeGroup:
        """Create a new code group."""
        endpoint = self._build_endpoint()
        data = item_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, CodeGroup)
    
    def update(self, item_id: Union[int, str], item_data: UpdateCodeGroupRequest) -> CodeGroup:
        """Update an existing code group."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        data = item_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, CodeGroup)
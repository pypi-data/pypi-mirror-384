"""statements client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    Statement,
    CreateStatementRequest,
    UpdateStatementRequest,
    StatementListResponse,
    StatementSearchRequest
)


class StatementsClient(BaseResource):
    """Client for managing statements in Open Dental."""
    
    def __init__(self, client):
        """Initialize the statements client."""
        super().__init__(client, "statements")
    
    def get(self, item_id: Union[int, str]) -> Statement:
        """Get a statement by ID."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._get(endpoint)
        return self._handle_response(response, Statement)
    
    def list(self, page: int = 1, per_page: int = 50) -> StatementListResponse:
        """List all statements."""
        params = {"page": page, "per_page": per_page}
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return StatementListResponse(**response)
        elif isinstance(response, list):
            return StatementListResponse(
                statements=[Statement(**item) for item in response],
                total=len(response), page=page, per_page=per_page
            )
        return StatementListResponse(statements=[], total=0, page=page, per_page=per_page)
    
    def create(self, item_data: CreateStatementRequest) -> Statement:
        """Create a new statement."""
        endpoint = self._build_endpoint()
        data = item_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, Statement)
    
    def update(self, item_id: Union[int, str], item_data: UpdateStatementRequest) -> Statement:
        """Update an existing statement."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        data = item_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, Statement)
    
    def delete(self, item_id: Union[int, str]) -> bool:
        """Delete a statement."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: StatementSearchRequest) -> StatementListResponse:
        """Search for statements."""
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return StatementListResponse(**response)
        elif isinstance(response, list):
            return StatementListResponse(
                statements=[Statement(**item) for item in response],
                total=len(response), page=search_params.page, per_page=search_params.per_page
            )
        return StatementListResponse(
            statements=[], total=0, page=search_params.page, per_page=search_params.per_page
        )

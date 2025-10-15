"""sheets client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    Sheet,
    CreateSheetRequest,
    UpdateSheetRequest,
    SheetListResponse,
    SheetSearchRequest
)


class SheetsClient(BaseResource):
    """Client for managing sheet/forms in Open Dental."""
    
    def __init__(self, client):
        """Initialize the sheet/forms client."""
        super().__init__(client, "sheets")
    
    def get(self, item_id: Union[int, str]) -> Sheet:
        """Get a sheet/form by ID."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._get(endpoint)
        return self._handle_response(response, Sheet)
    
    def list(self, page: int = 1, per_page: int = 50) -> SheetListResponse:
        """List all sheet/forms."""
        params = {"page": page, "per_page": per_page}
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return SheetListResponse(**response)
        elif isinstance(response, list):
            return SheetListResponse(
                sheets=[Sheet(**item) for item in response],
                total=len(response), page=page, per_page=per_page
            )
        return SheetListResponse(sheets=[], total=0, page=page, per_page=per_page)
    
    def create(self, item_data: CreateSheetRequest) -> Sheet:
        """Create a new sheet/form."""
        endpoint = self._build_endpoint()
        data = item_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, Sheet)
    
    def update(self, item_id: Union[int, str], item_data: UpdateSheetRequest) -> Sheet:
        """Update an existing sheet/form."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        data = item_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, Sheet)
    
    def delete(self, item_id: Union[int, str]) -> bool:
        """Delete a sheet/form."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: SheetSearchRequest) -> SheetListResponse:
        """Search for sheet/forms."""
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return SheetListResponse(**response)
        elif isinstance(response, list):
            return SheetListResponse(
                sheets=[Sheet(**item) for item in response],
                total=len(response), page=search_params.page, per_page=search_params.per_page
            )
        return SheetListResponse(
            sheets=[], total=0, page=search_params.page, per_page=search_params.per_page
        )

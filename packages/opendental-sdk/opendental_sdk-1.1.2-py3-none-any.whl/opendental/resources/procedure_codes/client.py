"""procedurecodes client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    ProcedureCode,
    CreateProcedureCodeRequest,
    UpdateProcedureCodeRequest,
    ProcedureCodeListResponse,
    ProcedureCodeSearchRequest
)


class ProcedureCodesClient(BaseResource):
    """Client for managing procedure codes in Open Dental."""
    
    def __init__(self, client):
        """Initialize the procedure codes client."""
        super().__init__(client, "procedurecodes")
    
    def get(self, item_id: Union[int, str]) -> ProcedureCode:
        """Get a procedure code by ID."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._get(endpoint)
        return self._handle_response(response, ProcedureCode)
    
    def list(self, page: int = 1, per_page: int = 50) -> ProcedureCodeListResponse:
        """List all procedure codes."""
        params = {"page": page, "per_page": per_page}
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return ProcedureCodeListResponse(**response)
        elif isinstance(response, list):
            return ProcedureCodeListResponse(
                procedure_codes=[ProcedureCode(**item) for item in response],
                total=len(response), page=page, per_page=per_page
            )
        return ProcedureCodeListResponse(procedure_codes=[], total=0, page=page, per_page=per_page)
    
    def create(self, item_data: CreateProcedureCodeRequest) -> ProcedureCode:
        """Create a new procedure code."""
        endpoint = self._build_endpoint()
        data = item_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, ProcedureCode)
    
    def update(self, item_id: Union[int, str], item_data: UpdateProcedureCodeRequest) -> ProcedureCode:
        """Update an existing procedure code."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        data = item_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, ProcedureCode)
    
    def delete(self, item_id: Union[int, str]) -> bool:
        """Delete a procedure code."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: ProcedureCodeSearchRequest) -> ProcedureCodeListResponse:
        """Search for procedure codes."""
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return ProcedureCodeListResponse(**response)
        elif isinstance(response, list):
            return ProcedureCodeListResponse(
                procedure_codes=[ProcedureCode(**item) for item in response],
                total=len(response), page=search_params.page, per_page=search_params.per_page
            )
        return ProcedureCodeListResponse(
            procedure_codes=[], total=0, page=search_params.page, per_page=search_params.per_page
        )

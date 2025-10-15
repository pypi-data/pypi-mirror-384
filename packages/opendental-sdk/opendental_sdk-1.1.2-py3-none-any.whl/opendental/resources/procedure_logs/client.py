"""procedurelogs client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    ProcedureLog,
    CreateProcedureLogRequest,
    UpdateProcedureLogRequest,
    ProcedureLogListResponse,
    ProcedureLogSearchRequest
)


class ProcedureLogsClient(BaseResource):
    """Client for managing procedure logs in Open Dental."""
    
    def __init__(self, client):
        """Initialize the procedure logs client."""
        super().__init__(client, "procedure_logs")
    
    def get(self, item_id: Union[int, str]) -> ProcedureLog:
        """Get a procedure log by ID."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._get(endpoint)
        return self._handle_response(response, ProcedureLog)
    
    def list(self, page: int = 1, per_page: int = 50) -> ProcedureLogListResponse:
        """List all procedure logs."""
        params = {"page": page, "per_page": per_page}
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return ProcedureLogListResponse(**response)
        elif isinstance(response, list):
            return ProcedureLogListResponse(
                procedure_logs=[ProcedureLog(**item) for item in response],
                total=len(response), page=page, per_page=per_page
            )
        return ProcedureLogListResponse(procedure_logs=[], total=0, page=page, per_page=per_page)
    
    def create(self, item_data: CreateProcedureLogRequest) -> ProcedureLog:
        """Create a new procedure log."""
        endpoint = self._build_endpoint()
        data = item_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, ProcedureLog)
    
    def update(self, item_id: Union[int, str], item_data: UpdateProcedureLogRequest) -> ProcedureLog:
        """Update an existing procedure log."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        data = item_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, ProcedureLog)
    
    def delete(self, item_id: Union[int, str]) -> bool:
        """Delete a procedure log."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: ProcedureLogSearchRequest) -> ProcedureLogListResponse:
        """Search for procedure logs."""
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return ProcedureLogListResponse(**response)
        elif isinstance(response, list):
            return ProcedureLogListResponse(
                procedure_logs=[ProcedureLog(**item) for item in response],
                total=len(response), page=search_params.page, per_page=search_params.per_page
            )
        return ProcedureLogListResponse(
            procedure_logs=[], total=0, page=search_params.page, per_page=search_params.per_page
        )

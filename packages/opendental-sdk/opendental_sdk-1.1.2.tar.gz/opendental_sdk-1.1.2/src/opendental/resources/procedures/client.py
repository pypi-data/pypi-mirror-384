"""Procedures client for Open Dental SDK."""

from typing import List, Optional, Union
from datetime import date
from ...base.resource import BaseResource
from .models import (
    Procedure,
    CreateProcedureRequest,
    UpdateProcedureRequest,
    ProcedureListResponse,
    ProcedureSearchRequest
)


class ProceduresClient(BaseResource):
    """Client for managing procedures in Open Dental."""
    
    def __init__(self, client):
        """Initialize the procedures client."""
        super().__init__(client, "procedures")
    
    def get(self, procedure_id: Union[int, str]) -> Procedure:
        """
        Get a procedure by ID.
        
        Args:
            procedure_id: The procedure ID
            
        Returns:
            Procedure: The procedure object
        """
        procedure_id = self._validate_id(procedure_id)
        endpoint = self._build_endpoint(procedure_id)
        response = self._get(endpoint)
        return self._handle_response(response, Procedure)
    
    def list(self, page: int = 1, per_page: int = 50) -> ProcedureListResponse:
        """
        List all procedures.
        
        Args:
            page: Page number (default: 1)
            per_page: Items per page (default: 50)
            
        Returns:
            ProcedureListResponse: List of procedures with pagination info
        """
        params = {
            "page": page,
            "per_page": per_page
        }
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return ProcedureListResponse(**response)
        elif isinstance(response, list):
            return ProcedureListResponse(
                procedures=[Procedure(**item) for item in response],
                total=len(response),
                page=page,
                per_page=per_page
            )
        else:
            return ProcedureListResponse(procedures=[], total=0, page=page, per_page=per_page)
    
    def create(self, procedure_data: CreateProcedureRequest) -> Procedure:
        """
        Create a new procedure.
        
        Args:
            procedure_data: The procedure data to create
            
        Returns:
            Procedure: The created procedure object
        """
        endpoint = self._build_endpoint()
        data = procedure_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, Procedure)
    
    def update(self, procedure_id: Union[int, str], procedure_data: UpdateProcedureRequest) -> Procedure:
        """
        Update an existing procedure.
        
        Args:
            procedure_id: The procedure ID
            procedure_data: The procedure data to update
            
        Returns:
            Procedure: The updated procedure object
        """
        procedure_id = self._validate_id(procedure_id)
        endpoint = self._build_endpoint(procedure_id)
        data = procedure_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, Procedure)
    
    def delete(self, procedure_id: Union[int, str]) -> bool:
        """
        Delete a procedure.
        
        Args:
            procedure_id: The procedure ID
            
        Returns:
            bool: True if deletion was successful
        """
        procedure_id = self._validate_id(procedure_id)
        endpoint = self._build_endpoint(procedure_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: ProcedureSearchRequest) -> ProcedureListResponse:
        """
        Search for procedures.
        
        Args:
            search_params: Search parameters
            
        Returns:
            ProcedureListResponse: List of matching procedures
        """
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return ProcedureListResponse(**response)
        elif isinstance(response, list):
            return ProcedureListResponse(
                procedures=[Procedure(**item) for item in response],
                total=len(response),
                page=search_params.page,
                per_page=search_params.per_page
            )
        else:
            return ProcedureListResponse(
                procedures=[], 
                total=0, 
                page=search_params.page, 
                per_page=search_params.per_page
            )
    
    def get_by_patient(self, pat_num: int) -> List[Procedure]:
        """
        Get procedures for a specific patient.
        
        Args:
            pat_num: Patient number
            
        Returns:
            List[Procedure]: List of procedures for the patient
        """
        search_params = ProcedureSearchRequest(pat_num=pat_num)
        result = self.search(search_params)
        return result.procedures
    
    def get_by_provider(self, prov_num: int) -> List[Procedure]:
        """
        Get procedures for a specific provider.
        
        Args:
            prov_num: Provider number
            
        Returns:
            List[Procedure]: List of procedures for the provider
        """
        search_params = ProcedureSearchRequest(prov_num=prov_num)
        result = self.search(search_params)
        return result.procedures
    
    def get_by_status(self, proc_status: str) -> List[Procedure]:
        """
        Get procedures by status.
        
        Args:
            proc_status: Procedure status (e.g., "TP", "C", "D")
            
        Returns:
            List[Procedure]: List of procedures with matching status
        """
        search_params = ProcedureSearchRequest(proc_status=proc_status)
        result = self.search(search_params)
        return result.procedures
    
    def get_by_date_range(self, start_date: date, end_date: date) -> List[Procedure]:
        """
        Get procedures within a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List[Procedure]: List of procedures within the date range
        """
        search_params = ProcedureSearchRequest(
            proc_date_start=start_date,
            proc_date_end=end_date
        )
        result = self.search(search_params)
        return result.procedures
    
    def get_treatment_planned(self) -> List[Procedure]:
        """
        Get all treatment planned procedures.
        
        Returns:
            List[Procedure]: List of treatment planned procedures
        """
        return self.get_by_status("TP")
    
    def get_completed(self) -> List[Procedure]:
        """
        Get all completed procedures.
        
        Returns:
            List[Procedure]: List of completed procedures
        """
        return self.get_by_status("C")
    
    def complete_procedure(self, procedure_id: Union[int, str]) -> Procedure:
        """
        Mark a procedure as complete.
        
        Args:
            procedure_id: The procedure ID
            
        Returns:
            Procedure: The updated procedure object
        """
        from datetime import date
        update_data = UpdateProcedureRequest(
            proc_status="C",
            proc_date=date.today()
        )
        return self.update(procedure_id, update_data)
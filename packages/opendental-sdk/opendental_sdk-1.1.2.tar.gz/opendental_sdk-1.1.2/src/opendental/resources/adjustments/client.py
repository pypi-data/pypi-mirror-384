"""Adjustments client for Open Dental SDK."""

from typing import List, Optional, Union
from datetime import date
from decimal import Decimal
from ...base.resource import BaseResource
from .models import (
    Adjustment,
    CreateAdjustmentRequest,
    UpdateAdjustmentRequest,
    AdjustmentListResponse,
    AdjustmentSearchRequest
)


class AdjustmentsClient(BaseResource):
    """Client for managing adjustments in Open Dental."""
    
    def __init__(self, client):
        """Initialize the adjustments client."""
        super().__init__(client, "adjustments")
    
    def get(self, adjustment_id: Union[int, str]) -> Adjustment:
        """
        Get an adjustment by ID.
        
        Args:
            adjustment_id: The adjustment ID
            
        Returns:
            Adjustment: The adjustment object
        """
        adjustment_id = self._validate_id(adjustment_id)
        endpoint = self._build_endpoint(adjustment_id)
        response = self._get(endpoint)
        return self._handle_response(response, Adjustment)
    
    def list(self, page: int = 1, per_page: int = 50) -> AdjustmentListResponse:
        """
        List all adjustments.
        
        Args:
            page: Page number (default: 1)
            per_page: Items per page (default: 50)
            
        Returns:
            AdjustmentListResponse: List of adjustments with pagination info
        """
        params = {
            "page": page,
            "per_page": per_page
        }
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return AdjustmentListResponse(**response)
        elif isinstance(response, list):
            return AdjustmentListResponse(
                adjustments=[Adjustment(**item) for item in response],
                total=len(response),
                page=page,
                per_page=per_page
            )
        else:
            return AdjustmentListResponse(adjustments=[], total=0, page=page, per_page=per_page)
    
    def create(self, adjustment_data: CreateAdjustmentRequest) -> Adjustment:
        """
        Create a new adjustment.
        
        Args:
            adjustment_data: The adjustment data to create
            
        Returns:
            Adjustment: The created adjustment object
        """
        endpoint = self._build_endpoint()
        data = adjustment_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, Adjustment)
    
    def update(self, adjustment_id: Union[int, str], adjustment_data: UpdateAdjustmentRequest) -> Adjustment:
        """
        Update an existing adjustment.
        
        Args:
            adjustment_id: The adjustment ID
            adjustment_data: The adjustment data to update
            
        Returns:
            Adjustment: The updated adjustment object
        """
        adjustment_id = self._validate_id(adjustment_id)
        endpoint = self._build_endpoint(adjustment_id)
        data = adjustment_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, Adjustment)
    
    def delete(self, adjustment_id: Union[int, str]) -> bool:
        """
        Delete an adjustment.
        
        Args:
            adjustment_id: The adjustment ID
            
        Returns:
            bool: True if deletion was successful
        """
        adjustment_id = self._validate_id(adjustment_id)
        endpoint = self._build_endpoint(adjustment_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: AdjustmentSearchRequest) -> AdjustmentListResponse:
        """
        Search for adjustments.
        
        Args:
            search_params: Search parameters
            
        Returns:
            AdjustmentListResponse: List of matching adjustments
        """
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return AdjustmentListResponse(**response)
        elif isinstance(response, list):
            return AdjustmentListResponse(
                adjustments=[Adjustment(**item) for item in response],
                total=len(response),
                page=search_params.page,
                per_page=search_params.per_page
            )
        else:
            return AdjustmentListResponse(
                adjustments=[], 
                total=0, 
                page=search_params.page, 
                per_page=search_params.per_page
            )
    
    def get_by_patient(self, pat_num: int) -> List[Adjustment]:
        """
        Get adjustments for a specific patient.
        
        Args:
            pat_num: Patient number
            
        Returns:
            List[Adjustment]: List of adjustments for the patient
        """
        search_params = AdjustmentSearchRequest(pat_num=pat_num)
        result = self.search(search_params)
        return result.adjustments
    
    def get_by_provider(self, prov_num: int) -> List[Adjustment]:
        """
        Get adjustments for a specific provider.
        
        Args:
            prov_num: Provider number
            
        Returns:
            List[Adjustment]: List of adjustments for the provider
        """
        search_params = AdjustmentSearchRequest(prov_num=prov_num)
        result = self.search(search_params)
        return result.adjustments
    
    def get_by_date_range(self, start_date: date, end_date: date) -> List[Adjustment]:
        """
        Get adjustments within a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List[Adjustment]: List of adjustments within the date range
        """
        search_params = AdjustmentSearchRequest(
            adj_date_start=start_date,
            adj_date_end=end_date
        )
        result = self.search(search_params)
        return result.adjustments
    
    def get_by_procedure(self, proc_num: int) -> List[Adjustment]:
        """
        Get adjustments for a specific procedure.
        
        Args:
            proc_num: Procedure number
            
        Returns:
            List[Adjustment]: List of adjustments for the procedure
        """
        search_params = AdjustmentSearchRequest(proc_num=proc_num)
        result = self.search(search_params)
        return result.adjustments
    
    def create_discount_adjustment(self, pat_num: int, amount: Decimal, prov_num: int, 
                                  note: Optional[str] = None) -> Adjustment:
        """
        Create a discount adjustment for a patient.
        
        Args:
            pat_num: Patient number
            amount: Discount amount (should be negative for discounts)
            prov_num: Provider number
            note: Optional note
            
        Returns:
            Adjustment: The created adjustment object
        """
        from datetime import date
        adjustment_data = CreateAdjustmentRequest(
            pat_num=pat_num,
            adj_date=date.today(),
            adj_type=1,  # Assuming type 1 is discount
            adj_amt=amount,
            prov_num=prov_num,
            adj_note=note
        )
        return self.create(adjustment_data)
"""Fees client for Open Dental SDK."""

from typing import List, Optional, Union
from decimal import Decimal
from ...base.resource import BaseResource
from .models import (
    Fee,
    CreateFeeRequest,
    UpdateFeeRequest,
    FeeListResponse,
    FeeSearchRequest,
    FeeSchedule,
    CreateFeeScheduleRequest,
    UpdateFeeScheduleRequest
)


class FeesClient(BaseResource):
    """Client for managing fees in Open Dental."""
    
    def __init__(self, client):
        """Initialize the fees client."""
        super().__init__(client, "fees")
    
    def get(self, fee_id: Union[int, str]) -> Fee:
        """
        Get a fee by ID.
        
        Args:
            fee_id: The fee ID
            
        Returns:
            Fee: The fee object
        """
        fee_id = self._validate_id(fee_id)
        endpoint = self._build_endpoint(fee_id)
        response = self._get(endpoint)
        return self._handle_response(response, Fee)
    
    def list(self, page: int = 1, per_page: int = 50) -> FeeListResponse:
        """
        List all fees.
        
        Args:
            page: Page number (default: 1)
            per_page: Items per page (default: 50)
            
        Returns:
            FeeListResponse: List of fees with pagination info
        """
        params = {
            "page": page,
            "per_page": per_page
        }
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return FeeListResponse(**response)
        elif isinstance(response, list):
            return FeeListResponse(
                fees=[Fee(**item) for item in response],
                total=len(response),
                page=page,
                per_page=per_page
            )
        else:
            return FeeListResponse(fees=[], total=0, page=page, per_page=per_page)
    
    def create(self, fee_data: CreateFeeRequest) -> Fee:
        """
        Create a new fee.
        
        Args:
            fee_data: The fee data to create
            
        Returns:
            Fee: The created fee object
        """
        endpoint = self._build_endpoint()
        data = fee_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, Fee)
    
    def update(self, fee_id: Union[int, str], fee_data: UpdateFeeRequest) -> Fee:
        """
        Update an existing fee.
        
        Args:
            fee_id: The fee ID
            fee_data: The fee data to update
            
        Returns:
            Fee: The updated fee object
        """
        fee_id = self._validate_id(fee_id)
        endpoint = self._build_endpoint(fee_id)
        data = fee_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, Fee)
    
    def delete(self, fee_id: Union[int, str]) -> bool:
        """
        Delete a fee.
        
        Args:
            fee_id: The fee ID
            
        Returns:
            bool: True if deletion was successful
        """
        fee_id = self._validate_id(fee_id)
        endpoint = self._build_endpoint(fee_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: FeeSearchRequest) -> FeeListResponse:
        """
        Search for fees.
        
        Args:
            search_params: Search parameters
            
        Returns:
            FeeListResponse: List of matching fees
        """
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return FeeListResponse(**response)
        elif isinstance(response, list):
            return FeeListResponse(
                fees=[Fee(**item) for item in response],
                total=len(response),
                page=search_params.page,
                per_page=search_params.per_page
            )
        else:
            return FeeListResponse(
                fees=[], 
                total=0, 
                page=search_params.page, 
                per_page=search_params.per_page
            )
    
    def get_by_code(self, code_num: int) -> List[Fee]:
        """
        Get fees for a specific procedure code.
        
        Args:
            code_num: Procedure code number
            
        Returns:
            List[Fee]: List of fees for the procedure code
        """
        search_params = FeeSearchRequest(code_num=code_num)
        result = self.search(search_params)
        return result.fees
    
    def get_by_fee_schedule(self, fee_sched: int) -> List[Fee]:
        """
        Get fees for a specific fee schedule.
        
        Args:
            fee_sched: Fee schedule number
            
        Returns:
            List[Fee]: List of fees for the fee schedule
        """
        search_params = FeeSearchRequest(fee_sched=fee_sched)
        result = self.search(search_params)
        return result.fees
    
    def get_by_provider(self, prov_num: int) -> List[Fee]:
        """
        Get fees for a specific provider.
        
        Args:
            prov_num: Provider number
            
        Returns:
            List[Fee]: List of fees for the provider
        """
        search_params = FeeSearchRequest(prov_num=prov_num)
        result = self.search(search_params)
        return result.fees
    
    def get_by_clinic(self, clinic_num: int) -> List[Fee]:
        """
        Get fees for a specific clinic.
        
        Args:
            clinic_num: Clinic number
            
        Returns:
            List[Fee]: List of fees for the clinic
        """
        search_params = FeeSearchRequest(clinic_num=clinic_num)
        result = self.search(search_params)
        return result.fees
    
    def get_fee_for_procedure(self, code_num: int, fee_sched: int, 
                             prov_num: Optional[int] = None, 
                             clinic_num: Optional[int] = None) -> Optional[Fee]:
        """
        Get the fee for a specific procedure in a fee schedule.
        
        Args:
            code_num: Procedure code number
            fee_sched: Fee schedule number
            prov_num: Optional provider number
            clinic_num: Optional clinic number
            
        Returns:
            Optional[Fee]: The fee object if found, None otherwise
        """
        search_params = FeeSearchRequest(
            code_num=code_num,
            fee_sched=fee_sched,
            prov_num=prov_num,
            clinic_num=clinic_num
        )
        result = self.search(search_params)
        return result.fees[0] if result.fees else None
    
    # Fee Schedule methods
    def get_fee_schedule(self, fee_sched_id: Union[int, str]) -> FeeSchedule:
        """
        Get a fee schedule by ID.
        
        Args:
            fee_sched_id: The fee schedule ID
            
        Returns:
            FeeSchedule: The fee schedule object
        """
        fee_sched_id = self._validate_id(fee_sched_id)
        endpoint = self._build_endpoint("schedules", fee_sched_id)
        response = self._get(endpoint)
        return self._handle_response(response, FeeSchedule)
    
    def create_fee_schedule(self, fee_schedule_data: CreateFeeScheduleRequest) -> FeeSchedule:
        """
        Create a new fee schedule.
        
        Args:
            fee_schedule_data: The fee schedule data to create
            
        Returns:
            FeeSchedule: The created fee schedule object
        """
        endpoint = self._build_endpoint("schedules")
        data = fee_schedule_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, FeeSchedule)
    
    def update_fee_schedule(self, fee_sched_id: Union[int, str], 
                           fee_schedule_data: UpdateFeeScheduleRequest) -> FeeSchedule:
        """
        Update an existing fee schedule.
        
        Args:
            fee_sched_id: The fee schedule ID
            fee_schedule_data: The fee schedule data to update
            
        Returns:
            FeeSchedule: The updated fee schedule object
        """
        fee_sched_id = self._validate_id(fee_sched_id)
        endpoint = self._build_endpoint("schedules", fee_sched_id)
        data = fee_schedule_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, FeeSchedule)
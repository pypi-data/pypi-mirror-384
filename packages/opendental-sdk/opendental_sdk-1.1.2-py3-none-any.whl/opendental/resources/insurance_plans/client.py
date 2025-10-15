"""Insurance Plans client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    InsurancePlan,
    CreateInsurancePlanRequest,
    UpdateInsurancePlanRequest,
    InsurancePlanListResponse,
    InsurancePlanSearchRequest
)


class InsurancePlansClient(BaseResource):
    """Client for managing insurance plans in Open Dental."""
    
    def __init__(self, client):
        """Initialize the insurance plans client."""
        super().__init__(client, "insurance_plans")
    
    def get(self, plan_id: Union[int, str]) -> InsurancePlan:
        """
        Get an insurance plan by ID.
        
        Args:
            plan_id: The insurance plan ID
            
        Returns:
            InsurancePlan: The insurance plan object
        """
        plan_id = self._validate_id(plan_id)
        endpoint = self._build_endpoint(plan_id)
        response = self._get(endpoint)
        return self._handle_response(response, InsurancePlan)
    
    def list(self, page: int = 1, per_page: int = 50) -> InsurancePlanListResponse:
        """
        List all insurance plans.
        
        Args:
            page: Page number (default: 1)
            per_page: Items per page (default: 50)
            
        Returns:
            InsurancePlanListResponse: List of insurance plans with pagination info
        """
        params = {
            "page": page,
            "per_page": per_page
        }
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return InsurancePlanListResponse(**response)
        elif isinstance(response, list):
            return InsurancePlanListResponse(
                insurance_plans=[InsurancePlan(**item) for item in response],
                total=len(response),
                page=page,
                per_page=per_page
            )
        else:
            return InsurancePlanListResponse(insurance_plans=[], total=0, page=page, per_page=per_page)
    
    def create(self, plan_data: CreateInsurancePlanRequest) -> InsurancePlan:
        """
        Create a new insurance plan.
        
        Args:
            plan_data: The insurance plan data to create
            
        Returns:
            InsurancePlan: The created insurance plan object
        """
        endpoint = self._build_endpoint()
        data = plan_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, InsurancePlan)
    
    def update(self, plan_id: Union[int, str], plan_data: UpdateInsurancePlanRequest) -> InsurancePlan:
        """
        Update an existing insurance plan.
        
        Args:
            plan_id: The insurance plan ID
            plan_data: The insurance plan data to update
            
        Returns:
            InsurancePlan: The updated insurance plan object
        """
        plan_id = self._validate_id(plan_id)
        endpoint = self._build_endpoint(plan_id)
        data = plan_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, InsurancePlan)
    
    def delete(self, plan_id: Union[int, str]) -> bool:
        """
        Delete an insurance plan.
        
        Args:
            plan_id: The insurance plan ID
            
        Returns:
            bool: True if deletion was successful
        """
        plan_id = self._validate_id(plan_id)
        endpoint = self._build_endpoint(plan_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: InsurancePlanSearchRequest) -> InsurancePlanListResponse:
        """
        Search for insurance plans.
        
        Args:
            search_params: Search parameters
            
        Returns:
            InsurancePlanListResponse: List of matching insurance plans
        """
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return InsurancePlanListResponse(**response)
        elif isinstance(response, list):
            return InsurancePlanListResponse(
                insurance_plans=[InsurancePlan(**item) for item in response],
                total=len(response),
                page=search_params.page,
                per_page=search_params.per_page
            )
        else:
            return InsurancePlanListResponse(
                insurance_plans=[], 
                total=0, 
                page=search_params.page, 
                per_page=search_params.per_page
            )
    
    def get_by_carrier(self, carrier_num: int) -> List[InsurancePlan]:
        """
        Get insurance plans for a specific carrier.
        
        Args:
            carrier_num: Carrier number
            
        Returns:
            List[InsurancePlan]: List of insurance plans for the carrier
        """
        search_params = InsurancePlanSearchRequest(carrier_num=carrier_num)
        result = self.search(search_params)
        return result.insurance_plans
    
    def get_by_group_name(self, group_name: str) -> List[InsurancePlan]:
        """
        Get insurance plans by group name.
        
        Args:
            group_name: Group name to search for
            
        Returns:
            List[InsurancePlan]: List of insurance plans with matching group name
        """
        search_params = InsurancePlanSearchRequest(group_name=group_name)
        result = self.search(search_params)
        return result.insurance_plans
    
    def get_by_employer(self, employer: str) -> List[InsurancePlan]:
        """
        Get insurance plans by employer.
        
        Args:
            employer: Employer name to search for
            
        Returns:
            List[InsurancePlan]: List of insurance plans for the employer
        """
        search_params = InsurancePlanSearchRequest(employer=employer)
        result = self.search(search_params)
        return result.insurance_plans
    
    def get_active(self) -> List[InsurancePlan]:
        """
        Get all active (non-hidden) insurance plans.
        
        Returns:
            List[InsurancePlan]: List of active insurance plans
        """
        search_params = InsurancePlanSearchRequest(is_hidden=False)
        result = self.search(search_params)
        return result.insurance_plans
    
    def get_by_plan_type(self, plan_type: str) -> List[InsurancePlan]:
        """
        Get insurance plans by plan type.
        
        Args:
            plan_type: Plan type to search for
            
        Returns:
            List[InsurancePlan]: List of insurance plans with matching type
        """
        search_params = InsurancePlanSearchRequest(plan_type=plan_type)
        result = self.search(search_params)
        return result.insurance_plans
    
    def hide_plan(self, plan_id: Union[int, str]) -> InsurancePlan:
        """
        Hide an insurance plan.
        
        Args:
            plan_id: The insurance plan ID
            
        Returns:
            InsurancePlan: The updated insurance plan object
        """
        update_data = UpdateInsurancePlanRequest(is_hidden=True)
        return self.update(plan_id, update_data)
    
    def unhide_plan(self, plan_id: Union[int, str]) -> InsurancePlan:
        """
        Unhide an insurance plan.
        
        Args:
            plan_id: The insurance plan ID
            
        Returns:
            InsurancePlan: The updated insurance plan object
        """
        update_data = UpdateInsurancePlanRequest(is_hidden=False)
        return self.update(plan_id, update_data)
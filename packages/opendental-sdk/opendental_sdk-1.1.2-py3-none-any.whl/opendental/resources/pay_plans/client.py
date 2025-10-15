"""payplans client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    PayPlan,
    CreatePayPlanRequest,
    UpdatePayPlanRequest,
    PayPlanListResponse,
    PayPlanSearchRequest
)


class PayPlansClient(BaseResource):
    """Client for managing payment plans in Open Dental."""
    
    def __init__(self, client):
        """Initialize the payment plans client."""
        super().__init__(client, "pay_plans")
    
    def get(self, item_id: Union[int, str]) -> PayPlan:
        """Get a payment plan by ID."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._get(endpoint)
        return self._handle_response(response, PayPlan)
    
    def list(self, page: int = 1, per_page: int = 50) -> PayPlanListResponse:
        """List all payment plans."""
        params = {"page": page, "per_page": per_page}
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return PayPlanListResponse(**response)
        elif isinstance(response, list):
            return PayPlanListResponse(
                pay_plans=[PayPlan(**item) for item in response],
                total=len(response), page=page, per_page=per_page
            )
        return PayPlanListResponse(pay_plans=[], total=0, page=page, per_page=per_page)
    
    def create(self, item_data: CreatePayPlanRequest) -> PayPlan:
        """Create a new payment plan."""
        endpoint = self._build_endpoint()
        data = item_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, PayPlan)
    
    def update(self, item_id: Union[int, str], item_data: UpdatePayPlanRequest) -> PayPlan:
        """Update an existing payment plan."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        data = item_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, PayPlan)
    
    def delete(self, item_id: Union[int, str]) -> bool:
        """Delete a payment plan."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: PayPlanSearchRequest) -> PayPlanListResponse:
        """Search for payment plans."""
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return PayPlanListResponse(**response)
        elif isinstance(response, list):
            return PayPlanListResponse(
                pay_plans=[PayPlan(**item) for item in response],
                total=len(response), page=search_params.page, per_page=search_params.per_page
            )
        return PayPlanListResponse(
            pay_plans=[], total=0, page=search_params.page, per_page=search_params.per_page
        )

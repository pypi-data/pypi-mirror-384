"""referrals client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    Referral,
    CreateReferralRequest,
    UpdateReferralRequest,
    ReferralListResponse,
    ReferralSearchRequest
)


class ReferralsClient(BaseResource):
    """Client for managing referrals in Open Dental."""
    
    def __init__(self, client):
        """Initialize the referrals client."""
        super().__init__(client, "referrals")
    
    def get(self, item_id: Union[int, str]) -> Referral:
        """Get a referral by ID."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._get(endpoint)
        return self._handle_response(response, Referral)
    
    def list(self, page: int = 1, per_page: int = 50) -> ReferralListResponse:
        """List all referrals."""
        params = {"page": page, "per_page": per_page}
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return ReferralListResponse(**response)
        elif isinstance(response, list):
            return ReferralListResponse(
                referrals=[Referral(**item) for item in response],
                total=len(response), page=page, per_page=per_page
            )
        return ReferralListResponse(referrals=[], total=0, page=page, per_page=per_page)
    
    def create(self, item_data: CreateReferralRequest) -> Referral:
        """Create a new referral."""
        endpoint = self._build_endpoint()
        data = item_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, Referral)
    
    def update(self, item_id: Union[int, str], item_data: UpdateReferralRequest) -> Referral:
        """Update an existing referral."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        data = item_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, Referral)
    
    def delete(self, item_id: Union[int, str]) -> bool:
        """Delete a referral."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: ReferralSearchRequest) -> ReferralListResponse:
        """Search for referrals."""
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return ReferralListResponse(**response)
        elif isinstance(response, list):
            return ReferralListResponse(
                referrals=[Referral(**item) for item in response],
                total=len(response), page=search_params.page, per_page=search_params.per_page
            )
        return ReferralListResponse(
            referrals=[], total=0, page=search_params.page, per_page=search_params.per_page
        )

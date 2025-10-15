"""Coverage Category client for the Open Dental API."""

from typing import Optional, List, Union
from ...base.resource import BaseResource
from .models import (
    CoverageCategory,
    CreateCoverageCategoryRequest,
    UpdateCoverageCategoryRequest,
    CoverageCategoryListResponse,
)


class CoverageCategoryClient(BaseResource):
    """
    Client for interacting with Coverage Category (CovCat) resources.
    
    Coverage Categories are used in insurance benefit processing and electronic
    eligibility and benefits. They are global and changes may affect all plans.
    """

    def __init__(self, client):
        """Initialize the coverage category client."""
        super().__init__(client, "covcats")

    def get(self, item_id: Union[int, str]) -> CoverageCategory:
        """Get a coverage category by ID."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._get(endpoint)
        return self._handle_response(response, CoverageCategory)

    def list(self, page: int = 1, per_page: int = 50) -> CoverageCategoryListResponse:
        """List all coverage categories."""
        params = {"page": page, "per_page": per_page}
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return CoverageCategoryListResponse(**response)
        elif isinstance(response, list):
            return CoverageCategoryListResponse(
                coverage_categories=[CoverageCategory(**item) for item in response],
                total=len(response), page=page, per_page=per_page
            )
        return CoverageCategoryListResponse(coverage_categories=[], total=0, page=page, per_page=per_page)

    def create(self, item_data: CreateCoverageCategoryRequest) -> CoverageCategory:
        """
        Create a new coverage category.
        
        Important: Do not alter Insurance Categories without a full understanding of what
        this does as insurance categories are global and changes may affect all plans.
        """
        endpoint = self._build_endpoint()
        data = item_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, CoverageCategory)

    def update(
        self, item_id: Union[int, str], item_data: UpdateCoverageCategoryRequest
    ) -> CoverageCategory:
        """
        Update an existing coverage category.
        
        This affects all benefits that are currently tied to this CovCat.
        """
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        data = item_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, CoverageCategory)

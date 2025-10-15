"""Chart modules client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    ChartModule,
    CreateChartModuleRequest,
    UpdateChartModuleRequest,
    ChartModuleListResponse,
    ChartModuleSearchRequest
)


class ChartModulesClient(BaseResource):
    """Client for managing chart modules in Open Dental."""
    
    def __init__(self, client):
        """Initialize the chart modules client."""
        super().__init__(client, "chart_modules")
    
    def get(self, module_id: Union[int, str]) -> ChartModule:
        """Get a chart module by ID."""
        module_id = self._validate_id(module_id)
        endpoint = self._build_endpoint(module_id)
        response = self._get(endpoint)
        return self._handle_response(response, ChartModule)
    
    def list(self, page: int = 1, per_page: int = 50) -> ChartModuleListResponse:
        """List all chart modules."""
        params = {"page": page, "per_page": per_page}
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return ChartModuleListResponse(**response)
        elif isinstance(response, list):
            return ChartModuleListResponse(
                chart_modules=[ChartModule(**item) for item in response],
                total=len(response), page=page, per_page=per_page
            )
        return ChartModuleListResponse(chart_modules=[], total=0, page=page, per_page=per_page)
    
    def create(self, module_data: CreateChartModuleRequest) -> ChartModule:
        """Create a new chart module."""
        endpoint = self._build_endpoint()
        data = module_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, ChartModule)
    
    def update(self, module_id: Union[int, str], module_data: UpdateChartModuleRequest) -> ChartModule:
        """Update an existing chart module."""
        module_id = self._validate_id(module_id)
        endpoint = self._build_endpoint(module_id)
        data = module_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, ChartModule)
    
    def delete(self, module_id: Union[int, str]) -> bool:
        """Delete a chart module."""
        module_id = self._validate_id(module_id)
        endpoint = self._build_endpoint(module_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: ChartModuleSearchRequest) -> ChartModuleListResponse:
        """Search for chart modules."""
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return ChartModuleListResponse(**response)
        elif isinstance(response, list):
            return ChartModuleListResponse(
                chart_modules=[ChartModule(**item) for item in response],
                total=len(response), page=search_params.page, per_page=search_params.per_page
            )
        return ChartModuleListResponse(
            chart_modules=[], total=0, page=search_params.page, per_page=search_params.per_page
        )
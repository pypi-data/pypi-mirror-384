"""schedules client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    Schedule,
    CreateScheduleRequest,
    UpdateScheduleRequest,
    ScheduleListResponse,
    ScheduleSearchRequest
)


class SchedulesClient(BaseResource):
    """Client for managing schedules in Open Dental."""
    
    def __init__(self, client):
        """Initialize the schedules client."""
        super().__init__(client, "schedules")
    
    def get(self, item_id: Union[int, str]) -> Schedule:
        """Get a schedule by ID."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._get(endpoint)
        return self._handle_response(response, Schedule)
    
    def list(self, page: int = 1, per_page: int = 50) -> ScheduleListResponse:
        """List all schedules."""
        params = {"page": page, "per_page": per_page}
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return ScheduleListResponse(**response)
        elif isinstance(response, list):
            return ScheduleListResponse(
                schedules=[Schedule(**item) for item in response],
                total=len(response), page=page, per_page=per_page
            )
        return ScheduleListResponse(schedules=[], total=0, page=page, per_page=per_page)
    
    def create(self, item_data: CreateScheduleRequest) -> Schedule:
        """Create a new schedule."""
        endpoint = self._build_endpoint()
        data = item_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, Schedule)
    
    def update(self, item_id: Union[int, str], item_data: UpdateScheduleRequest) -> Schedule:
        """Update an existing schedule."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        data = item_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, Schedule)
    
    def delete(self, item_id: Union[int, str]) -> bool:
        """Delete a schedule."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: ScheduleSearchRequest) -> ScheduleListResponse:
        """Search for schedules."""
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return ScheduleListResponse(**response)
        elif isinstance(response, list):
            return ScheduleListResponse(
                schedules=[Schedule(**item) for item in response],
                total=len(response), page=search_params.page, per_page=search_params.per_page
            )
        return ScheduleListResponse(
            schedules=[], total=0, page=search_params.page, per_page=search_params.per_page
        )

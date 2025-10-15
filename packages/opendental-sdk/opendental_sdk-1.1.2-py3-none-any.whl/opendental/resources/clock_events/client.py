"""clockevents client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    ClockEvent,
    CreateClockEventRequest,
    UpdateClockEventRequest,
    ClockEventListResponse,
    ClockEventSearchRequest
)


class ClockEventsClient(BaseResource):
    """Client for managing time clock events in Open Dental."""
    
    def __init__(self, client):
        """Initialize the time clock events client."""
        super().__init__(client, "clock_events")
    
    def get(self, item_id: Union[int, str]) -> ClockEvent:
        """Get a time clock event by ID."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._get(endpoint)
        return self._handle_response(response, ClockEvent)
    
    def list(self, page: int = 1, per_page: int = 50) -> ClockEventListResponse:
        """List all time clock events."""
        params = {"page": page, "per_page": per_page}
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return ClockEventListResponse(**response)
        elif isinstance(response, list):
            return ClockEventListResponse(
                clock_events=[ClockEvent(**item) for item in response],
                total=len(response), page=page, per_page=per_page
            )
        return ClockEventListResponse(clock_events=[], total=0, page=page, per_page=per_page)
    
    def create(self, item_data: CreateClockEventRequest) -> ClockEvent:
        """Create a new time clock event."""
        endpoint = self._build_endpoint()
        data = item_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, ClockEvent)
    
    def update(self, item_id: Union[int, str], item_data: UpdateClockEventRequest) -> ClockEvent:
        """Update an existing time clock event."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        data = item_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, ClockEvent)
    
    def delete(self, item_id: Union[int, str]) -> bool:
        """Delete a time clock event."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: ClockEventSearchRequest) -> ClockEventListResponse:
        """Search for time clock events."""
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return ClockEventListResponse(**response)
        elif isinstance(response, list):
            return ClockEventListResponse(
                clock_events=[ClockEvent(**item) for item in response],
                total=len(response), page=search_params.page, per_page=search_params.per_page
            )
        return ClockEventListResponse(
            clock_events=[], total=0, page=search_params.page, per_page=search_params.per_page
        )

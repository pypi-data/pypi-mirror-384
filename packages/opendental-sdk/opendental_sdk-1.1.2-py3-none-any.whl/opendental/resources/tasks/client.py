"""tasks client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    Task,
    CreateTaskRequest,
    UpdateTaskRequest,
    TaskListResponse,
    TaskSearchRequest
)


class TasksClient(BaseResource):
    """Client for managing tasks in Open Dental."""
    
    def __init__(self, client):
        """Initialize the tasks client."""
        super().__init__(client, "tasks")
    
    def get(self, item_id: Union[int, str]) -> Task:
        """Get a task by ID."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._get(endpoint)
        return self._handle_response(response, Task)
    
    def list(self, page: int = 1, per_page: int = 50) -> TaskListResponse:
        """List all tasks."""
        params = {"page": page, "per_page": per_page}
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return TaskListResponse(**response)
        elif isinstance(response, list):
            return TaskListResponse(
                tasks=[Task(**item) for item in response],
                total=len(response), page=page, per_page=per_page
            )
        return TaskListResponse(tasks=[], total=0, page=page, per_page=per_page)
    
    def create(self, item_data: CreateTaskRequest) -> Task:
        """Create a new task."""
        endpoint = self._build_endpoint()
        data = item_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, Task)
    
    def update(self, item_id: Union[int, str], item_data: UpdateTaskRequest) -> Task:
        """Update an existing task."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        data = item_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, Task)
    
    def delete(self, item_id: Union[int, str]) -> bool:
        """Delete a task."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: TaskSearchRequest) -> TaskListResponse:
        """Search for tasks."""
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return TaskListResponse(**response)
        elif isinstance(response, list):
            return TaskListResponse(
                tasks=[Task(**item) for item in response],
                total=len(response), page=search_params.page, per_page=search_params.per_page
            )
        return TaskListResponse(
            tasks=[], total=0, page=search_params.page, per_page=search_params.per_page
        )

"""tasks models for Open Dental SDK."""

from datetime import datetime
from typing import Optional, List

from ...base.models import BaseModel


class Task(BaseModel):
    """Task model."""
    
    # Primary identifiers
    id: int
    tasks_num: int
    
    # Basic information
    name: str
    description: Optional[str] = None
    
    # Status
    is_active: bool = True
    
    # Timestamps
    date_created: Optional[datetime] = None
    date_modified: Optional[datetime] = None


class CreateTaskRequest(BaseModel):
    """Request model for creating a new task."""
    
    # Required fields
    name: str
    
    # Optional fields
    description: Optional[str] = None
    is_active: bool = True


class UpdateTaskRequest(BaseModel):
    """Request model for updating an existing task."""
    
    # All fields are optional for updates
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class TaskListResponse(BaseModel):
    """Response model for task list operations."""
    
    tasks: List[Task]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class TaskSearchRequest(BaseModel):
    """Request model for searching tasks."""
    
    name: Optional[str] = None
    is_active: Optional[bool] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50

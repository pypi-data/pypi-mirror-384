"""clockevents models for Open Dental SDK."""

from datetime import datetime
from typing import Optional, List

from ...base.models import BaseModel


class ClockEvent(BaseModel):
    """ClockEvent model."""
    
    # Primary identifiers
    id: int
    clock_events_num: int
    
    # Basic information
    name: str
    description: Optional[str] = None
    
    # Status
    is_active: bool = True
    
    # Timestamps
    date_created: Optional[datetime] = None
    date_modified: Optional[datetime] = None


class CreateClockEventRequest(BaseModel):
    """Request model for creating a new time clock event."""
    
    # Required fields
    name: str
    
    # Optional fields
    description: Optional[str] = None
    is_active: bool = True


class UpdateClockEventRequest(BaseModel):
    """Request model for updating an existing time clock event."""
    
    # All fields are optional for updates
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ClockEventListResponse(BaseModel):
    """Response model for time clock event list operations."""
    
    clock_events: List[ClockEvent]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class ClockEventSearchRequest(BaseModel):
    """Request model for searching time clock events."""
    
    name: Optional[str] = None
    is_active: Optional[bool] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50

"""computers models for Open Dental SDK."""

from datetime import datetime
from typing import Optional, List

from ...base.models import BaseModel


class Computer(BaseModel):
    """Computer model."""
    
    # Primary identifiers
    id: int
    computers_num: int
    
    # Basic information
    name: str
    description: Optional[str] = None
    
    # Status
    is_active: bool = True
    
    # Timestamps
    date_created: Optional[datetime] = None
    date_modified: Optional[datetime] = None


class CreateComputerRequest(BaseModel):
    """Request model for creating a new computer/workstation."""
    
    # Required fields
    name: str
    
    # Optional fields
    description: Optional[str] = None
    is_active: bool = True


class UpdateComputerRequest(BaseModel):
    """Request model for updating an existing computer/workstation."""
    
    # All fields are optional for updates
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ComputerListResponse(BaseModel):
    """Response model for computer/workstation list operations."""
    
    computers: List[Computer]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class ComputerSearchRequest(BaseModel):
    """Request model for searching computer/workstations."""
    
    name: Optional[str] = None
    is_active: Optional[bool] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50

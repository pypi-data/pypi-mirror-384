"""communications models for Open Dental SDK."""

from datetime import datetime
from typing import Optional, List

from ...base.models import BaseModel


class Communication(BaseModel):
    """Communication model."""
    
    # Primary identifiers
    id: int
    communications_num: int
    
    # Basic information
    name: str
    description: Optional[str] = None
    
    # Status
    is_active: bool = True
    
    # Timestamps
    date_created: Optional[datetime] = None
    date_modified: Optional[datetime] = None


class CreateCommunicationRequest(BaseModel):
    """Request model for creating a new communication log."""
    
    # Required fields
    name: str
    
    # Optional fields
    description: Optional[str] = None
    is_active: bool = True


class UpdateCommunicationRequest(BaseModel):
    """Request model for updating an existing communication log."""
    
    # All fields are optional for updates
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CommunicationListResponse(BaseModel):
    """Response model for communication log list operations."""
    
    communications: List[Communication]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class CommunicationSearchRequest(BaseModel):
    """Request model for searching communication logs."""
    
    name: Optional[str] = None
    is_active: Optional[bool] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50

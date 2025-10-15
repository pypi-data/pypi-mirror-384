"""employers models for Open Dental SDK."""

from datetime import datetime
from typing import Optional, List

from ...base.models import BaseModel


class Employer(BaseModel):
    """Employer model."""
    
    # Primary identifiers
    id: int
    employers_num: int
    
    # Basic information
    name: str
    description: Optional[str] = None
    
    # Status
    is_active: bool = True
    
    # Timestamps
    date_created: Optional[datetime] = None
    date_modified: Optional[datetime] = None


class CreateEmployerRequest(BaseModel):
    """Request model for creating a new employer."""
    
    # Required fields
    name: str
    
    # Optional fields
    description: Optional[str] = None
    is_active: bool = True


class UpdateEmployerRequest(BaseModel):
    """Request model for updating an existing employer."""
    
    # All fields are optional for updates
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class EmployerListResponse(BaseModel):
    """Response model for employer list operations."""
    
    employers: List[Employer]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class EmployerSearchRequest(BaseModel):
    """Request model for searching employers."""
    
    name: Optional[str] = None
    is_active: Optional[bool] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50

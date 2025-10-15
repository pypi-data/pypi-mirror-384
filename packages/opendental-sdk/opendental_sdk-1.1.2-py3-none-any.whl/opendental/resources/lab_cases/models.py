"""labcases models for Open Dental SDK."""

from datetime import datetime
from typing import Optional, List

from ...base.models import BaseModel


class LabCase(BaseModel):
    """LabCase model."""
    
    # Primary identifiers
    id: int
    lab_cases_num: int
    
    # Basic information
    name: str
    description: Optional[str] = None
    
    # Status
    is_active: bool = True
    
    # Timestamps
    date_created: Optional[datetime] = None
    date_modified: Optional[datetime] = None


class CreateLabCaseRequest(BaseModel):
    """Request model for creating a new laboratory case."""
    
    # Required fields
    name: str
    
    # Optional fields
    description: Optional[str] = None
    is_active: bool = True


class UpdateLabCaseRequest(BaseModel):
    """Request model for updating an existing laboratory case."""
    
    # All fields are optional for updates
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class LabCaseListResponse(BaseModel):
    """Response model for laboratory case list operations."""
    
    lab_cases: List[LabCase]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class LabCaseSearchRequest(BaseModel):
    """Request model for searching laboratory cases."""
    
    name: Optional[str] = None
    is_active: Optional[bool] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50

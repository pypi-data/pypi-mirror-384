"""diseases models for Open Dental SDK."""

from datetime import datetime
from typing import Optional, List

from ...base.models import BaseModel


class Disease(BaseModel):
    """Disease model."""
    
    # Primary identifiers
    id: int
    diseases_num: int
    
    # Basic information
    name: str
    description: Optional[str] = None
    
    # Status
    is_active: bool = True
    
    # Timestamps
    date_created: Optional[datetime] = None
    date_modified: Optional[datetime] = None


class CreateDiseaseRequest(BaseModel):
    """Request model for creating a new disease/condition."""
    
    # Required fields
    name: str
    
    # Optional fields
    description: Optional[str] = None
    is_active: bool = True


class UpdateDiseaseRequest(BaseModel):
    """Request model for updating an existing disease/condition."""
    
    # All fields are optional for updates
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DiseaseListResponse(BaseModel):
    """Response model for disease/condition list operations."""
    
    diseases: List[Disease]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class DiseaseSearchRequest(BaseModel):
    """Request model for searching disease/conditions."""
    
    name: Optional[str] = None
    is_active: Optional[bool] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50

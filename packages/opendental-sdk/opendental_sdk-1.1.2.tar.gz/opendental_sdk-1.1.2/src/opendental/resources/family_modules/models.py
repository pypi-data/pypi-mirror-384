"""familymodules models for Open Dental SDK."""

from datetime import datetime
from typing import Optional, List

from ...base.models import BaseModel


class FamilyModule(BaseModel):
    """FamilyModule model."""
    
    # Primary identifiers
    id: int
    family_modules_num: int
    
    # Basic information
    name: str
    description: Optional[str] = None
    
    # Status
    is_active: bool = True
    
    # Timestamps
    date_created: Optional[datetime] = None
    date_modified: Optional[datetime] = None


class CreateFamilyModuleRequest(BaseModel):
    """Request model for creating a new family module."""
    
    # Required fields
    name: str
    
    # Optional fields
    description: Optional[str] = None
    is_active: bool = True


class UpdateFamilyModuleRequest(BaseModel):
    """Request model for updating an existing family module."""
    
    # All fields are optional for updates
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class FamilyModuleListResponse(BaseModel):
    """Response model for family module list operations."""
    
    family_modules: List[FamilyModule]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class FamilyModuleSearchRequest(BaseModel):
    """Request model for searching family modules."""
    
    name: Optional[str] = None
    is_active: Optional[bool] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50

"""pharmacys models for Open Dental SDK."""

from datetime import datetime
from typing import Optional, List

from ...base.models import BaseModel


class Pharmacy(BaseModel):
    """Pharmacy model."""
    
    # Primary identifiers
    id: int
    pharmacies_num: int
    
    # Basic information
    name: str
    description: Optional[str] = None
    
    # Status
    is_active: bool = True
    
    # Timestamps
    date_created: Optional[datetime] = None
    date_modified: Optional[datetime] = None


class CreatePharmacyRequest(BaseModel):
    """Request model for creating a new pharmacy."""
    
    # Required fields
    name: str
    
    # Optional fields
    description: Optional[str] = None
    is_active: bool = True


class UpdatePharmacyRequest(BaseModel):
    """Request model for updating an existing pharmacy."""
    
    # All fields are optional for updates
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PharmacyListResponse(BaseModel):
    """Response model for pharmacy list operations."""
    
    pharmacies: List[Pharmacy]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class PharmacySearchRequest(BaseModel):
    """Request model for searching pharmacys."""
    
    name: Optional[str] = None
    is_active: Optional[bool] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50

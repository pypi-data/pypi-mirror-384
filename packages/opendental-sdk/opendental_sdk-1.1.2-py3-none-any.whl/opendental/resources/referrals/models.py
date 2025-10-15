"""referrals models for Open Dental SDK."""

from datetime import datetime
from typing import Optional, List

from ...base.models import BaseModel


class Referral(BaseModel):
    """Referral model."""
    
    # Primary identifiers
    id: int
    referrals_num: int
    
    # Basic information
    name: str
    description: Optional[str] = None
    
    # Status
    is_active: bool = True
    
    # Timestamps
    date_created: Optional[datetime] = None
    date_modified: Optional[datetime] = None


class CreateReferralRequest(BaseModel):
    """Request model for creating a new referral."""
    
    # Required fields
    name: str
    
    # Optional fields
    description: Optional[str] = None
    is_active: bool = True


class UpdateReferralRequest(BaseModel):
    """Request model for updating an existing referral."""
    
    # All fields are optional for updates
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ReferralListResponse(BaseModel):
    """Response model for referral list operations."""
    
    referrals: List[Referral]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class ReferralSearchRequest(BaseModel):
    """Request model for searching referrals."""
    
    name: Optional[str] = None
    is_active: Optional[bool] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50

"""Carrier models for Open Dental SDK."""

from datetime import datetime, date
from typing import Optional, List

from ...base.models import BaseModel


class Carrier(BaseModel):
    """Insurance carrier model."""
    
    # Primary identifiers
    id: int
    carrier_num: int
    
    # Carrier information
    carrier_name: str
    carrier_group_name: Optional[str] = None
    
    # Contact information
    address: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    phone: Optional[str] = None
    
    # Electronic processing
    electronic_id: Optional[str] = None
    is_hidden: bool = False
    
    # Timestamps
    date_created: Optional[datetime] = None
    date_modified: Optional[datetime] = None


class CreateCarrierRequest(BaseModel):
    """Request model for creating a new carrier."""
    
    # Required fields
    carrier_name: str
    
    # Optional fields
    carrier_group_name: Optional[str] = None
    address: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    phone: Optional[str] = None
    electronic_id: Optional[str] = None
    is_hidden: bool = False


class UpdateCarrierRequest(BaseModel):
    """Request model for updating an existing carrier."""
    
    # All fields are optional for updates
    carrier_name: Optional[str] = None
    carrier_group_name: Optional[str] = None
    address: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    phone: Optional[str] = None
    electronic_id: Optional[str] = None
    is_hidden: Optional[bool] = None


class CarrierListResponse(BaseModel):
    """Response model for carrier list operations."""
    
    carriers: List[Carrier]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class CarrierSearchRequest(BaseModel):
    """Request model for searching carriers."""
    
    carrier_name: Optional[str] = None
    carrier_group_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    electronic_id: Optional[str] = None
    is_hidden: Optional[bool] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50
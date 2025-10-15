"""Adjustment models for Open Dental SDK."""

from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal

from ...base.models import BaseModel


class Adjustment(BaseModel):
    """Adjustment model."""
    
    # Primary identifiers
    id: int
    adj_num: int
    
    # Patient information
    pat_num: int
    
    # Adjustment details
    adj_date: date
    adj_type: int
    adj_amt: Decimal
    
    # Provider information
    prov_num: int
    
    # Description and notes
    adj_note: Optional[str] = None
    
    # Procedure reference
    proc_num: Optional[int] = None
    proc_date: Optional[date] = None
    
    # Timestamps
    date_entry: Optional[datetime] = None
    date_created: Optional[datetime] = None
    date_modified: Optional[datetime] = None
    
    # Clinic information
    clinic_num: Optional[int] = None


class CreateAdjustmentRequest(BaseModel):
    """Request model for creating a new adjustment."""
    
    # Required fields
    pat_num: int
    adj_date: date
    adj_type: int
    adj_amt: Decimal
    prov_num: int
    
    # Optional fields
    adj_note: Optional[str] = None
    proc_num: Optional[int] = None
    proc_date: Optional[date] = None
    clinic_num: Optional[int] = None


class UpdateAdjustmentRequest(BaseModel):
    """Request model for updating an existing adjustment."""
    
    # All fields are optional for updates
    adj_date: Optional[date] = None
    adj_type: Optional[int] = None
    adj_amt: Optional[Decimal] = None
    prov_num: Optional[int] = None
    adj_note: Optional[str] = None
    proc_num: Optional[int] = None
    proc_date: Optional[date] = None
    clinic_num: Optional[int] = None


class AdjustmentListResponse(BaseModel):
    """Response model for adjustment list operations."""
    
    adjustments: List[Adjustment]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class AdjustmentSearchRequest(BaseModel):
    """Request model for searching adjustments."""
    
    pat_num: Optional[int] = None
    prov_num: Optional[int] = None
    adj_type: Optional[int] = None
    adj_date_start: Optional[date] = None
    adj_date_end: Optional[date] = None
    proc_num: Optional[int] = None
    clinic_num: Optional[int] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50
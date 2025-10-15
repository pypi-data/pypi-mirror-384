"""payplans models for Open Dental SDK."""

from datetime import datetime
from typing import Optional, List

from ...base.models import BaseModel


class PayPlan(BaseModel):
    """PayPlan model."""
    
    # Primary identifiers
    id: int
    pay_plans_num: int
    
    # Basic information
    name: str
    description: Optional[str] = None
    
    # Status
    is_active: bool = True
    
    # Timestamps
    date_created: Optional[datetime] = None
    date_modified: Optional[datetime] = None


class CreatePayPlanRequest(BaseModel):
    """Request model for creating a new payment plan."""
    
    # Required fields
    name: str
    
    # Optional fields
    description: Optional[str] = None
    is_active: bool = True


class UpdatePayPlanRequest(BaseModel):
    """Request model for updating an existing payment plan."""
    
    # All fields are optional for updates
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PayPlanListResponse(BaseModel):
    """Response model for payment plan list operations."""
    
    pay_plans: List[PayPlan]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class PayPlanSearchRequest(BaseModel):
    """Request model for searching payment plans."""
    
    name: Optional[str] = None
    is_active: Optional[bool] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50

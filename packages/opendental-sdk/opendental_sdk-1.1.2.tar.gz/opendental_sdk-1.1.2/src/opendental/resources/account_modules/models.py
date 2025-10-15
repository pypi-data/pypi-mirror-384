"""Account modules models for Open Dental SDK."""

from datetime import datetime
from typing import Optional, List
from decimal import Decimal

from ...base.models import BaseModel


class AccountModule(BaseModel):
    """Account module model."""
    
    # Primary identifiers
    id: int
    account_module_num: int
    
    # Module information
    module_name: str
    description: Optional[str] = None
    version: Optional[str] = None
    
    # Configuration
    is_enabled: bool = True
    is_required: bool = False
    
    # Pricing information
    monthly_fee: Optional[Decimal] = None
    setup_fee: Optional[Decimal] = None
    per_user_fee: Optional[Decimal] = None
    
    # License information
    license_key: Optional[str] = None
    expiration_date: Optional[datetime] = None
    max_users: Optional[int] = None
    
    # Status tracking
    status: Optional[str] = None
    last_updated: Optional[datetime] = None
    
    # Timestamps
    date_created: Optional[datetime] = None
    date_modified: Optional[datetime] = None


class CreateAccountModuleRequest(BaseModel):
    """Request model for creating a new account module."""
    
    # Required fields
    module_name: str
    
    # Optional fields
    description: Optional[str] = None
    version: Optional[str] = None
    is_enabled: bool = True
    is_required: bool = False
    
    # Pricing information
    monthly_fee: Optional[Decimal] = None
    setup_fee: Optional[Decimal] = None
    per_user_fee: Optional[Decimal] = None
    
    # License information
    license_key: Optional[str] = None
    expiration_date: Optional[datetime] = None
    max_users: Optional[int] = None
    
    # Status tracking
    status: Optional[str] = None


class UpdateAccountModuleRequest(BaseModel):
    """Request model for updating an existing account module."""
    
    # All fields are optional for updates
    module_name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    is_enabled: Optional[bool] = None
    is_required: Optional[bool] = None
    
    # Pricing information
    monthly_fee: Optional[Decimal] = None
    setup_fee: Optional[Decimal] = None
    per_user_fee: Optional[Decimal] = None
    
    # License information
    license_key: Optional[str] = None
    expiration_date: Optional[datetime] = None
    max_users: Optional[int] = None
    
    # Status tracking
    status: Optional[str] = None


class AccountModuleListResponse(BaseModel):
    """Response model for account module list operations."""
    
    account_modules: List[AccountModule]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class AccountModuleSearchRequest(BaseModel):
    """Request model for searching account modules."""
    
    module_name: Optional[str] = None
    is_enabled: Optional[bool] = None
    is_required: Optional[bool] = None
    status: Optional[str] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50
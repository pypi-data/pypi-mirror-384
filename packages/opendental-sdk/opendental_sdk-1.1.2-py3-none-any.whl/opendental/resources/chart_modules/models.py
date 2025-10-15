"""Chart modules models for Open Dental SDK."""

from datetime import datetime
from typing import Optional, List

from ...base.models import BaseModel


class ChartModule(BaseModel):
    """Chart module model."""
    
    # Primary identifiers
    id: int
    chart_module_num: int
    
    # Module information
    module_name: str
    description: Optional[str] = None
    version: Optional[str] = None
    
    # Configuration
    is_enabled: bool = True
    is_default: bool = False
    
    # Display settings
    display_order: Optional[int] = None
    color: Optional[str] = None
    
    # Permissions
    required_permissions: Optional[List[str]] = None
    visible_to_roles: Optional[List[str]] = None
    
    # Timestamps
    date_created: Optional[datetime] = None
    date_modified: Optional[datetime] = None


class CreateChartModuleRequest(BaseModel):
    """Request model for creating a new chart module."""
    
    # Required fields
    module_name: str
    
    # Optional fields
    description: Optional[str] = None
    version: Optional[str] = None
    is_enabled: bool = True
    is_default: bool = False
    display_order: Optional[int] = None
    color: Optional[str] = None
    required_permissions: Optional[List[str]] = None
    visible_to_roles: Optional[List[str]] = None


class UpdateChartModuleRequest(BaseModel):
    """Request model for updating an existing chart module."""
    
    # All fields are optional for updates
    module_name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    is_enabled: Optional[bool] = None
    is_default: Optional[bool] = None
    display_order: Optional[int] = None
    color: Optional[str] = None
    required_permissions: Optional[List[str]] = None
    visible_to_roles: Optional[List[str]] = None


class ChartModuleListResponse(BaseModel):
    """Response model for chart module list operations."""
    
    chart_modules: List[ChartModule]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class ChartModuleSearchRequest(BaseModel):
    """Request model for searching chart modules."""
    
    module_name: Optional[str] = None
    is_enabled: Optional[bool] = None
    is_default: Optional[bool] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50
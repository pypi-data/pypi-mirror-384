"""sheets models for Open Dental SDK."""

from datetime import datetime
from typing import Optional, List

from ...base.models import BaseModel


class Sheet(BaseModel):
    """Sheet model."""
    
    # Primary identifiers
    id: int
    sheets_num: int
    
    # Basic information
    name: str
    description: Optional[str] = None
    
    # Status
    is_active: bool = True
    
    # Timestamps
    date_created: Optional[datetime] = None
    date_modified: Optional[datetime] = None


class CreateSheetRequest(BaseModel):
    """Request model for creating a new sheet/form."""
    
    # Required fields
    name: str
    
    # Optional fields
    description: Optional[str] = None
    is_active: bool = True


class UpdateSheetRequest(BaseModel):
    """Request model for updating an existing sheet/form."""
    
    # All fields are optional for updates
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class SheetListResponse(BaseModel):
    """Response model for sheet/form list operations."""
    
    sheets: List[Sheet]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class SheetSearchRequest(BaseModel):
    """Request model for searching sheet/forms."""
    
    name: Optional[str] = None
    is_active: Optional[bool] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50

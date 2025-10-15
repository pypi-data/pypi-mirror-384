"""definitions models for Open Dental SDK."""

from datetime import datetime
from typing import Optional, List

from ...base.models import BaseModel


class Definition(BaseModel):
    """Definition model."""
    
    # Primary identifiers
    id: int
    definitions_num: int
    
    # Basic information
    name: str
    description: Optional[str] = None
    
    # Status
    is_active: bool = True
    
    # Timestamps
    date_created: Optional[datetime] = None
    date_modified: Optional[datetime] = None


class CreateDefinitionRequest(BaseModel):
    """Request model for creating a new system definition."""
    
    # Required fields
    name: str
    
    # Optional fields
    description: Optional[str] = None
    is_active: bool = True


class UpdateDefinitionRequest(BaseModel):
    """Request model for updating an existing system definition."""
    
    # All fields are optional for updates
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DefinitionListResponse(BaseModel):
    """Response model for system definition list operations."""
    
    definitions: List[Definition]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class DefinitionSearchRequest(BaseModel):
    """Request model for searching system definitions."""
    
    name: Optional[str] = None
    is_active: Optional[bool] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50

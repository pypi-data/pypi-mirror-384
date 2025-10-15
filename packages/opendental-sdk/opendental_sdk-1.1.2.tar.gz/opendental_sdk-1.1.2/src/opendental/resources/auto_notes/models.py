"""Auto notes models for Open Dental SDK."""

from datetime import datetime
from typing import Optional, List

from ...base.models import BaseModel


class AutoNote(BaseModel):
    """Auto note model."""
    
    # Primary identifiers
    id: int
    auto_note_num: int
    
    # Basic information
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    
    # Content
    note_text: str
    prompt_text: Optional[str] = None
    
    # Configuration
    is_active: bool = True
    is_protected: bool = False
    requires_signature: bool = False
    
    # Usage tracking
    usage_count: Optional[int] = None
    last_used: Optional[datetime] = None
    
    # Template variables
    variables: Optional[List[str]] = None
    default_values: Optional[dict] = None
    
    # Timestamps
    date_created: Optional[datetime] = None
    date_modified: Optional[datetime] = None


class CreateAutoNoteRequest(BaseModel):
    """Request model for creating a new auto note."""
    
    # Required fields
    name: str
    note_text: str
    
    # Optional fields
    description: Optional[str] = None
    category: Optional[str] = None
    prompt_text: Optional[str] = None
    
    # Configuration
    is_active: bool = True
    is_protected: bool = False
    requires_signature: bool = False
    
    # Template variables
    variables: Optional[List[str]] = None
    default_values: Optional[dict] = None


class UpdateAutoNoteRequest(BaseModel):
    """Request model for updating an existing auto note."""
    
    # All fields are optional for updates
    name: Optional[str] = None
    note_text: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    prompt_text: Optional[str] = None
    
    # Configuration
    is_active: Optional[bool] = None
    is_protected: Optional[bool] = None
    requires_signature: Optional[bool] = None
    
    # Template variables
    variables: Optional[List[str]] = None
    default_values: Optional[dict] = None


class AutoNoteListResponse(BaseModel):
    """Response model for auto note list operations."""
    
    auto_notes: List[AutoNote]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class AutoNoteSearchRequest(BaseModel):
    """Request model for searching auto notes."""
    
    name: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None
    is_protected: Optional[bool] = None
    text_search: Optional[str] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50
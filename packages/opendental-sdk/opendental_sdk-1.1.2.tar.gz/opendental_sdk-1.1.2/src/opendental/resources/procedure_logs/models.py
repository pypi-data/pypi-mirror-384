"""procedurelogs models for Open Dental SDK."""

from datetime import datetime
from typing import Optional, List

from ...base.models import BaseModel


class ProcedureLog(BaseModel):
    """ProcedureLog model."""
    
    # Primary identifiers
    id: int
    procedure_logs_num: int
    
    # Basic information
    name: str
    description: Optional[str] = None
    
    # Status
    is_active: bool = True
    
    # Timestamps
    date_created: Optional[datetime] = None
    date_modified: Optional[datetime] = None


class CreateProcedureLogRequest(BaseModel):
    """Request model for creating a new procedure log."""
    
    # Required fields
    name: str
    
    # Optional fields
    description: Optional[str] = None
    is_active: bool = True


class UpdateProcedureLogRequest(BaseModel):
    """Request model for updating an existing procedure log."""
    
    # All fields are optional for updates
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ProcedureLogListResponse(BaseModel):
    """Response model for procedure log list operations."""
    
    procedure_logs: List[ProcedureLog]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class ProcedureLogSearchRequest(BaseModel):
    """Request model for searching procedure logs."""
    
    name: Optional[str] = None
    is_active: Optional[bool] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50
